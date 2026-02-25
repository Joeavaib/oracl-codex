from __future__ import annotations

from threading import Lock


class HFClient:
    _MODEL_CACHE: dict[tuple[str, str | None], tuple[object, object]] = {}
    _CACHE_LOCK = Lock()

    def __init__(self, adapter_path: str | None = None):
        self.adapter_path = adapter_path

    def _load_model(self, model: str) -> tuple[object, object]:
        cache_key = (model, self.adapter_path)
        with self._CACHE_LOCK:
            cached = self._MODEL_CACHE.get(cache_key)
            if cached is not None:
                return cached

            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
            base_model = AutoModelForCausalLM.from_pretrained(
                model,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                attn_implementation="eager",
            )
            if self.adapter_path:
                loaded_model = PeftModel.from_pretrained(base_model, self.adapter_path)
            else:
                loaded_model = base_model
            self._MODEL_CACHE[cache_key] = (tokenizer, loaded_model)
            return tokenizer, loaded_model

    @staticmethod
    def _build_prompt(prompt: str, system: str | None = None) -> str:
        if system:
            return f"{system.strip()}\n\n{prompt.strip()}"
        return prompt

    def generate(self, model: str, prompt: str, options: dict | None = None, system: str | None = None) -> str:
        tokenizer, loaded_model = self._load_model(model)
        opts = dict(options or {})
        seed = opts.pop("seed", None)
        max_new_tokens = int(opts.pop("max_new_tokens", opts.pop("num_predict", 512)))
        temperature = float(opts.pop("temperature", 0.0))
        top_p = float(opts.pop("top_p", 1.0))
        do_sample = bool(opts.pop("do_sample", False))

        full_prompt = self._build_prompt(prompt, system)
        try:
            inputs = tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": system or ""},
                    {"role": "user", "content": prompt},
                ],
                add_generation_prompt=True,
                return_tensors="pt",
            )
        except Exception:
            inputs = tokenizer(full_prompt, return_tensors="pt")["input_ids"]

        model_device = getattr(loaded_model, "device", None)
        if model_device is not None and hasattr(inputs, "to"):
            inputs = inputs.to(model_device)

        if seed is not None:
            import torch

            torch.manual_seed(int(seed))

        outputs = loaded_model.generate(
            inputs,
            do_sample=do_sample,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
        )
        generated = outputs[0][inputs.shape[-1] :]
        return tokenizer.decode(generated, skip_special_tokens=True).strip()
