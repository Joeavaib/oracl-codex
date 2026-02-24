from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Artifact:
    kind: str
    payload: str


def parse_artifact(output: str) -> Artifact:
    t = output.lstrip()
    if t.startswith("diff --git"):
        return Artifact("diff", output)
    if t.startswith("FILE: "):
        return Artifact("file_blocks", output)
    return Artifact("invalid", output)
