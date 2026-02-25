from __future__ import annotations

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
