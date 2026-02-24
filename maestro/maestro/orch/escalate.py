from __future__ import annotations

from maestro.tmps.types import ALine, BLine, CLine, ELine, TMPSRecord, VLine


def synthetic_meta_escalation(sid: str, runid: str, turn: int) -> TMPSRecord:
    return TMPSRecord(
        v=VLine("2.4", sid, runid, turn),
        a=ALine("0000", "0000", "H", "Validator-Fehler Meta-Escalation"),
        e=[ELine("validator.output", "C", "Validator konnte keinen gültigen Record erzeugen")],
        b=[
            BLine(1, "orch", "Escalate an Supervisor"),
            BLine(2, "sys", "Validator-Logs prüfen"),
            BLine(3, "sys", "Fallback-Validator aktivieren"),
        ],
        c=CLine("E", 0, 0, "*"),
    )
