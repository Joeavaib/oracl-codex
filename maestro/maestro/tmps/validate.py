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

from maestro.tmps.parser import ParseError
from maestro.tmps.types import TMPSRecord


_VERDICT_BY_HARD4 = {
    "1111": "P",
    "1110": "W",
    "1100": "F",
    "1000": "F",
    "0000": "H",
}


def validate_tmps_semantics(record: TMPSRecord) -> None:
    expected_verdict = _VERDICT_BY_HARD4.get(record.a.hard4)
    if expected_verdict is None:
        raise ParseError(f"unsupported hard4: {record.a.hard4}")
    if record.a.verdict != expected_verdict:
        raise ParseError(
            f"verdict mismatch for hard4={record.a.hard4}: expected {expected_verdict}, got {record.a.verdict}"
        )

    pris = [b.pri for b in record.b]
    if pris != sorted(pris) or len(set(pris)) != len(pris):
        raise ParseError("B priorities must be strictly increasing")
    if not all(1 <= pri <= 9 for pri in pris):
        raise ParseError("B priorities must be in range 1..9")

    if record.c.max_retries < 0:
        raise ParseError("C.max_retries must be >= 0")

