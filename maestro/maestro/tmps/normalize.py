from __future__ import annotations

from .types import TMPSRecord


def normalize_tmps(record: TMPSRecord, budget_after_turn: int) -> TMPSRecord:
    budget_after_turn = max(0, min(9, budget_after_turn))
    record.c.max_retries = min(max(0, record.c.max_retries), budget_after_turn)

    verdict = record.a.verdict
    decision = record.c.decision

    if verdict in {"P", "W"}:
        decision = "A"
    elif verdict == "F":
        decision = "R" if budget_after_turn > 0 else "E"
    elif verdict == "H":
        if decision == "A":
            decision = "R" if budget_after_turn > 0 else "E"
    if decision == "A" and verdict in {"F", "H"}:
        decision = "R" if budget_after_turn > 0 else "E"
    if budget_after_turn == 0 and decision in {"R", "X"}:
        decision = "E"

    record.c.decision = decision
    record.c.max_retries = budget_after_turn
    return record
