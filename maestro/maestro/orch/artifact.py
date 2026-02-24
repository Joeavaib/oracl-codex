from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Artifact:
    kind: str
    payload: str


def _extract_fenced_block(output: str) -> str | None:
    for pattern in (
        r"```(?:diff)?\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
    ):
        m = re.search(pattern, output, flags=re.DOTALL)
        if m:
            return m.group(1).strip("\n")
    return None


def parse_artifact(output: str) -> Artifact:
    t = output.lstrip()
    if t.startswith("diff --git"):
        return Artifact("diff", t)
    if t.startswith("FILE: "):
        return Artifact("file_blocks", t)

    diff_idx = t.find("diff --git")
    if diff_idx >= 0:
        candidate = t[diff_idx:]
        return Artifact("diff", candidate)

    file_idx = t.find("FILE: ")
    if file_idx >= 0:
        candidate = t[file_idx:]
        return Artifact("file_blocks", candidate)

    fenced = _extract_fenced_block(t)
    if fenced:
        if fenced.startswith("diff --git"):
            return Artifact("diff", fenced)
        if fenced.startswith("FILE: "):
            return Artifact("file_blocks", fenced)

    return Artifact("invalid", output)
