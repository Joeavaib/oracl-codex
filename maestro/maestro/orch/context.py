from __future__ import annotations

import json


def build_validator_input(
    mode: str,
    request: str,
    repo_summary: str,
    artifact_kind: str,
    artifact: str,
    patch_apply: dict,
    checks: dict,
    last_tmps: str,
    cap: int,
    *,
    sid: str,
    runid: str,
    turn: int,
    budget_after_turn: int,
) -> str:
    payload = (
        f"[SID] {sid}\n"
        f"[RUNID] {runid}\n"
        f"[TURN] {turn}\n"
        f"[BUDGET_AFTER_TURN] {budget_after_turn}\n"
        f"[MODE] {mode}\n"
        f"[REQUEST] {request}\n"
        f"[REPO_SUMMARY] {repo_summary}\n"
        f"[ARTIFACT_KIND] {artifact_kind}\n"
        f"[ARTIFACT] {artifact[:8000]}\n"
        f"[PATCH_APPLY] {json.dumps(patch_apply, sort_keys=True)}\n"
        f"[CHECKS] {json.dumps(checks, sort_keys=True)}\n"
        f"[LAST_TMPS] {last_tmps if last_tmps else 'NONE'}\n"
    )
    return payload[:cap]
