#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maestro.tmps.parser import ParseError, parse_tmps


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate parseability and decision distribution on dataset")
    ap.add_argument("--dataset", type=Path, required=True)
    args = ap.parse_args()

    rows = _load_jsonl(args.dataset)
    parse_ok = 0
    decisions: dict[str, int] = {}

    for row in rows:
        text = row["messages"][-1]["content"]
        try:
            rec = parse_tmps(text)
            parse_ok += 1
            decisions[rec.c.decision] = decisions.get(rec.c.decision, 0) + 1
        except ParseError:
            pass

    total = len(rows)
    pct = (100.0 * parse_ok / total) if total else 0.0
    print(f"rows={total} parse_ok={parse_ok} parse_rate={pct:.2f}%")
    print("decision_counts=", decisions)


if __name__ == "__main__":
    main()
