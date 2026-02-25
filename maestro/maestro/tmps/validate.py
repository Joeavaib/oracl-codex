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


def validate_tmps_semantics(rec: TMPSRecord, *, expected_budget_after_turn: int | None = None) -> None:
    derived = _derive_verdict(rec.a.hard4, rec.a.soft4)
    if rec.a.verdict != derived:
        raise TMPSValidationError(f"verdict mismatch: got={rec.a.verdict} expected={derived}")

    if expected_budget_after_turn is not None and rec.c.max_retries != expected_budget_after_turn:
        raise TMPSValidationError(
            f"max_retries mismatch: got={rec.c.max_retries} expected={expected_budget_after_turn}"
        )

    if derived in {"P", "W"}:
        if rec.c.decision != "A":
            raise TMPSValidationError(f"decision invalid for verdict {derived}: got={rec.c.decision} expected=A")
    elif derived == "F":
        expected = "R" if rec.c.max_retries > 0 else "E"
        if rec.c.decision != expected:
            raise TMPSValidationError(f"decision invalid for verdict F: got={rec.c.decision} expected={expected}")
    elif derived == "H":
        if rec.c.decision == "A":
            raise TMPSValidationError("decision invalid for verdict H: A is forbidden")
        if rec.c.decision not in {"R", "X", "E"}:
            raise TMPSValidationError(
                f"decision invalid for verdict H: got={rec.c.decision} expected one of R/X/E"
            )

    if rec.c.max_retries == 0 and rec.c.decision in {"R", "X"}:
        raise TMPSValidationError("decision invalid when max_retries=0: R/X forbidden")

    priorities = [line.pri for line in rec.b]
    if priorities != sorted(priorities) or len(set(priorities)) != len(priorities):
        raise TMPSValidationError("B priorities must be strictly increasing and unique")
