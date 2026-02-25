from __future__ import annotations

import re

from .types import ALine, BLine, CLine, ELine, TMPSRecord, VLine


class ParseError(ValueError):
    pass


def split_with_escape(text: str) -> list[str]:
    out, current = [], []
    esc = False
    for ch in text:
        if esc:
            if ch == "|":
                current.append("|")
            else:
                current.extend(["\\", ch])
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == "|":
            out.append("".join(current))
            current = []
            continue
        current.append(ch)
    if esc:
        current.append("\\")
    out.append("".join(current))
    return out


def parse_tmps(raw: str) -> TMPSRecord:
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    i = 0
    if not lines:
        raise ParseError("empty")

    if not lines[0].startswith("V "):
        raise ParseError("missing V")

    vparts = split_with_escape(lines[0][2:])
    if len(vparts) != 4:
        raise ParseError("invalid V")
    v = VLine(vparts[0], vparts[1], vparts[2], int(vparts[3]))
    i = 1

    if i >= len(lines) or not lines[i].startswith("A "):
        raise ParseError("missing A")
    aparts = split_with_escape(lines[i][2:])
    if len(aparts) != 4:
        raise ParseError("invalid A")
    a = ALine(*aparts)
    if not re.fullmatch(r"[01]{4}", a.hard4):
        raise ParseError("hard4")
    if not re.fullmatch(r"\d{4}", a.soft4):
        raise ParseError("soft4")
    if a.verdict not in {"P", "W", "F", "H"}:
        raise ParseError("verdict")
    i += 1

    es: list[ELine] = []
    while i < len(lines) and lines[i].startswith("E "):
        eparts = split_with_escape(lines[i][2:])
        if len(eparts) not in {3, 4}:
            raise ParseError("invalid E")
        es.append(ELine(eparts[0], eparts[1], eparts[2], eparts[3] if len(eparts) == 4 else None))
        i += 1

    bs: list[BLine] = []
    while i < len(lines) and lines[i].startswith("B "):
        payload = lines[i][2:]
        if "|" not in payload:
            raise ParseError("invalid B")
        left, right = payload.split("|", 1)
        if ":" not in left:
            raise ParseError("invalid B")
        pri_s, agent = left.split(":", 1)

        try:
            pri = int(pri_s)
        except ValueError:
            raise ParseError("B pri") from None

        if pri < 1 or pri > 7:
            raise ParseError("B pri range")
        if not re.fullmatch(r"[a-z]{2,4}", agent):
            raise ParseError("B agent")

        action_parts = split_with_escape(right)
        if len(action_parts) != 1:
            raise ParseError("B action (unescaped pipe)")

        bs.append(BLine(pri, agent, action_parts[0]))
        i += 1

    if not 3 <= len(bs) <= 7:
        raise ParseError("B count")
    pris = [b.pri for b in bs]
    if pris != sorted(pris) or len(set(pris)) != len(pris):
        raise ParseError("B order")

    if i >= len(lines) or not lines[i].startswith("C "):
        raise ParseError("missing C")
    cparts = split_with_escape(lines[i][2:])
    if len(cparts) != 4:
        raise ParseError("invalid C")
    c = CLine(cparts[0], int(cparts[1]), int(cparts[2]), cparts[3])
    if c.decision not in {"A", "R", "X", "E"}:
        raise ParseError("decision")
    if c.strategy not in {0, 1, 2, 3, 4, 5}:
        raise ParseError("strategy")
    if i != len(lines) - 1:
        raise ParseError("trailing lines")
    return TMPSRecord(v=v, a=a, e=es, b=bs, c=c)
