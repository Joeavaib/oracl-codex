#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maestro.llm.prompts import VALIDATOR_SYSTEM_PROMPT
from maestro.tmps.parser import ParseError, parse_tmps


def _iter_turn_dirs(runs_root: Path):
    for turn in runs_root.glob("*/**/turns/*"):
        if turn.is_dir():
            yield turn


def _read_first_parseable_tmps(turn_dir: Path) -> str | None:
    for name in ("tmps_raw.txt", "tmps_raw_retry.txt"):
        p = turn_dir / name
        if not p.exists():
            continue
        raw = p.read_text().strip()
        if not raw:
            continue
        try:
            parse_tmps(raw)
            return raw
        except ParseError:
            continue
    return None


def extract_pairs(runs_root: Path) -> list[dict]:
    out: list[dict] = []
    for turn in _iter_turn_dirs(runs_root):
        validator_input = turn / "validator_input.txt"
        if not validator_input.exists():
            continue
        tmps_raw = _read_first_parseable_tmps(turn)
        if not tmps_raw:
            continue
        out.append(
            {
                "source": str(turn),
                "messages": [
                    {"role": "system", "content": VALIDATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": validator_input.read_text()},
                    {"role": "assistant", "content": tmps_raw},
                ],
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract parseable validator pairs from .maestro runs")
    ap.add_argument("--runs-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    pairs = extract_pairs(args.runs_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in pairs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(pairs)} examples to {args.out}")


if __name__ == "__main__":
    main()
