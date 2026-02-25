import pytest

from maestro.tmps.parser import parse_tmps
from maestro.tmps.validate import TMPSValidationError, validate_tmps_semantics


def test_validate_tmps_semantics_accepts_valid_record():
    raw = "\n".join([
        "V 2.4|sid|run|1",
        "A 1111|6655|W|good enough",
        "B 1:imp|do one",
        "B 2:tst|do two",
        "B 3:doc|do three",
        "C A|1|0|*",
    ])
    rec = parse_tmps(raw)
    validate_tmps_semantics(rec, budget_after_turn=0)


def test_validate_tmps_semantics_rejects_wrong_verdict_and_decision():
    raw = "\n".join([
        "V 2.4|sid|run|1",
        "A 1111|9999|F|bad verdict",
        "B 1:imp|do one",
        "B 2:tst|do two",
        "B 3:doc|do three",
        "C R|1|0|*",
    ])
    rec = parse_tmps(raw)
    with pytest.raises(TMPSValidationError, match="verdict mismatch"):
        validate_tmps_semantics(rec, budget_after_turn=0)


def test_validate_tmps_semantics_rejects_max_retries_mismatch():
    raw = "\n".join([
        "V 2.4|sid|run|1",
        "A 1111|9999|P|good",
        "B 1:imp|do one",
        "B 2:tst|do two",
        "B 3:doc|do three",
        "C A|1|2|*",
    ])
    rec = parse_tmps(raw)
    with pytest.raises(TMPSValidationError, match="max_retries mismatch"):
        validate_tmps_semantics(rec, budget_after_turn=0)
