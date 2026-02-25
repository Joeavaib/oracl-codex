#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maestro.tmps.normalize import normalize_tmps
from maestro.tmps.parser import ParseError, parse_tmps


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _is_valid_example(row: dict) -> bool:
    try:
        assistant = row["messages"][-1]["content"]
        parsed = parse_tmps(assistant)
        normalize_tmps(parsed, budget_after_turn=3)
        return True
    except (KeyError, IndexError, ParseError, TypeError, ValueError):
        return False


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Filter and split validator SFT data")
    ap.add_argument("--real", type=Path, required=True)
    ap.add_argument("--synth", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    all_rows = _load_jsonl(args.real) + _load_jsonl(args.synth)
    valid_rows = [r for r in all_rows if _is_valid_example(r)]
    random.Random(args.seed).shuffle(valid_rows)

    n = len(valid_rows)
    n_train = int(n * 0.85)
    n_val = int(n * 0.10)
    train = valid_rows[:n_train]
    val = valid_rows[n_train : n_train + n_val]
    test = valid_rows[n_train + n_val :]

    _write_jsonl(args.out_dir / "train.jsonl", train)
    _write_jsonl(args.out_dir / "val.jsonl", val)
    _write_jsonl(args.out_dir / "test.jsonl", test)

    print(f"total={len(all_rows)} valid={n} train={len(train)} val={len(val)} test={len(test)}")


if __name__ == "__main__":
    main()
