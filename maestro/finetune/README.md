# Validator Finetune Starter (Qwen2.5-3B + QLoRA)

This folder gives you a minimal end-to-end pipeline to build a validator dataset and start QLoRA training.

## 1) Extract real examples from Maestro runs

```bash
python finetune/scripts/extract_real_pairs.py \
  --runs-root .maestro/runs \
  --out finetune/data/raw_runs/real_pairs.jsonl
```

## 2) Generate synthetic examples

```bash
python finetune/scripts/generate_synth_dataset.py \
  --n 1000 \
  --out finetune/data/synth/synth_pairs.jsonl
```

## 3) Filter + split

```bash
python finetune/scripts/filter_and_split.py \
  --real finetune/data/raw_runs/real_pairs.jsonl \
  --synth finetune/data/synth/synth_pairs.jsonl \
  --out-dir finetune/data/processed
```

This step keeps only parseable TMP-S examples and writes:
- `train.jsonl`
- `val.jsonl`
- `test.jsonl`

## 4) Quick dataset sanity check

```bash
python finetune/scripts/eval_tmps.py --dataset finetune/data/processed/train.jsonl
python finetune/scripts/eval_tmps.py --dataset finetune/data/processed/test.jsonl
```

## 5) Train with QLoRA

Use your preferred trainer (Axolotl / TRL / Unsloth). A starter config is provided at:

- `finetune/configs/qwen25_3b_qlora.yaml`

Example (Axolotl-style):

```bash
axolotl train finetune/configs/qwen25_3b_qlora.yaml
```

## 6) Evaluate finetuned model outputs

Run model inference on `test.jsonl`, then re-run `eval_tmps.py` on generated outputs to measure parse rate and decision distribution.

---

## Notes

- Focus metric #1: parseability (`parse_tmps` success rate).
- Focus metric #2: decision correctness (`A/R/X/E`) on your curated eval set.
- Start with quality over quantity: 1k clean examples > 10k noisy examples.
