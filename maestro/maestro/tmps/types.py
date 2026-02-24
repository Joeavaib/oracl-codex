from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VLine:
    ver: str
    sid: str
    runid: str
    turn: int


@dataclass
class ALine:
    hard4: str
    soft4: str
    verdict: str
    rationale: str


@dataclass
class ELine:
    dotpath: str
    severity: str
    fix_hint: str
    turn_ref: str | None = None


@dataclass
class BLine:
    pri: int
    agent: str
    action: str


@dataclass
class CLine:
    decision: str
    strategy: int
    max_retries: int
    focus: str


@dataclass
class TMPSRecord:
    v: VLine
    a: ALine
    e: list[ELine]
    b: list[BLine]
    c: CLine
