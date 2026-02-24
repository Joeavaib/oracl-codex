from maestro.tmps.parser import ParseError, parse_tmps, split_with_escape


def test_split_with_escape_pipe():
    assert split_with_escape(r"a\|b|c") == ["a|b", "c"]


def test_parse_canonical():
    raw = "\n".join([
        "V 2.4|sid|run|1",
        "A 1111|9999|P|good",
        "B 1:imp|do one",
        "B 2:tst|do two",
        "B 3:doc|do three",
        "C A|1|2|*",
    ])
    rec = parse_tmps(raw)
    assert rec.v.ver == "2.4"
    assert rec.c.decision == "A"


def test_parse_legacy_without_v_defaults():
    raw = "\n".join([
        "A 1111|8888|W|ok",
        "B 1:imp|do one",
        "B 2:tst|do two",
        "B 3:doc|do three",
        "C R|1|1|*",
    ])
    rec = parse_tmps(raw)
    assert rec.v.sid == "anon"


def test_enforces_b_count():
    raw = "\n".join([
        "V 2.4|sid|run|1",
        "A 1111|9999|P|good",
        "B 1:imp|do one",
        "C A|1|2|*",
    ])
    try:
        parse_tmps(raw)
    except ParseError:
        assert True
    else:
        assert False
