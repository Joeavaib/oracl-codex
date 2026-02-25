from __future__ import annotations

from maestro.tmps.types import TMPSRecord


class TMPSValidationError(ValueError):
    pass


def _derive_verdict(hard4: str, soft4: str) -> str:
    if "0" in hard4:
        return "H"
    score = sum(int(ch) for ch in soft4)
    if score >= 28:
        return "P"
    if score >= 20:
        return "W"
    return "F"


def validate_tmps_semantics(record: TMPSRecord, budget_after_turn: int) -> None:
    derived = _derive_verdict(record.a.hard4, record.a.soft4)
    if record.a.verdict != derived:
        raise TMPSValidationError(f"verdict mismatch: got={record.a.verdict} expected={derived}")

    expected_budget = max(0, min(9, budget_after_turn))
    if record.c.max_retries != expected_budget:
        raise TMPSValidationError(
            f"max_retries mismatch: got={record.c.max_retries} expected={expected_budget}"
        )

    if derived in {"P", "W"} and record.c.decision != "A":
        raise TMPSValidationError(f"decision invalid for verdict {derived}: got={record.c.decision} expected=A")

    if derived == "F":
        expected_decision = "R" if expected_budget > 0 else "E"
        if record.c.decision != expected_decision:
            raise TMPSValidationError(
                f"decision invalid for verdict F: got={record.c.decision} expected={expected_decision}"
            )

    if derived == "H" and record.c.decision not in {"R", "X", "E"}:
        raise TMPSValidationError(
            f"decision invalid for verdict H: got={record.c.decision} expected one of R/X/E"
        )
