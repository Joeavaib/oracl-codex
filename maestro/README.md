# Maestro

Maestro is a deterministic local orchestrator that coordinates specialist coding models via Ollama using TMP-S v2.4 validator records.

## Run

```bash
maestro run --repo PATH --request FILE_OR_STRING --cfg CFG.json [--sandboxed|--unsafe-local]
```

Outputs are written to `.maestro/runs/{sid}/{runid}` and worktrees/copies under `.maestro/work/{sid}/{runid}/repo`.

## Config

Example `CFG.json`:

```json
{
  "ollama_host": "http://127.0.0.1:11434",
  "ollama_timeout_s": 300,
  "validator_backend": "hf",
  "validator_model": "Qwen/Qwen3-4B",
  "validator_adapter_path": "./out/qwen4b-tmps-lora-rocm",
  "validator_seed": 42,
  "strict_mode": true,
  "max_retries": 2,
  "abs_max_turns": 6,
  "execution_mode": "sandboxed",
  "apply_to_repo": false,
  "allow_renames": false,
  "parallel_decompose": false,
  "validator_input_cap": 24000,
  "checks": [],
  "agents": {
    "imp": {"model": "qwen2.5-coder:14b"},
    "tst": {"model": "qwen2.5-coder:14b"},
    "doc": {"model": "qwen2.5-coder:14b"}
  }
}
```

### Fields

- `ollama_host`: Base URL for the Ollama HTTP API.
- `ollama_timeout_s`: Request timeout in seconds for Ollama generate calls (must be `> 0`).
- `validator_backend`: Validator backend, either `ollama` or `hf`.
- `validator_model`: Model used for TMP-S validation records.
- `validator_adapter_path`: Optional PEFT adapter path used by `validator_backend=hf`.
- `validator_seed`: Optional deterministic seed for validator decoding.
- `strict_mode`: If true, any TMP-S normalization change causes retry/rejection instead of silent healing.
- `max_retries`: Maximum retry attempts for failed rounds.
- `abs_max_turns`: Hard cap on orchestration turns.
- `execution_mode`: One of `sandboxed` or `unsafe-local`.
- `apply_to_repo`: Whether to apply accepted patch to target repo.
- `checks`: Optional command checks to run.
- `agents`: Specialist agent model mapping.
- `allow_renames`: Allow file rename operations in patch application.
- `parallel_decompose`: Enable parallel decomposition mode.
- `validator_input_cap`: Input size cap for validator prompts.

## HF/Adapter validator usage

Set `validator_backend` to `hf`, set `validator_model` to the base model, and set `validator_adapter_path` to your LoRA/PEFT adapter directory.

The HF client loads `AutoTokenizer` + `AutoModelForCausalLM` once per process and reuses cached model instances; adapter loading is applied via `PeftModel.from_pretrained(...)`.

ROCm note: PyTorch often still reports device names as `cuda:0` on ROCm systems; this is expected.

## Validator finetuning

A ready-to-run starter pipeline for Qwen2.5-3B + QLoRA is available under `finetune/`.

See `finetune/README.md` for extraction, synthetic data generation, filtering/splitting, and training config steps.

## Execution model

Maestro executes specialist/validator calls **sequentially (one after another)**.
No concurrent specialist fan-out is performed in this build.
