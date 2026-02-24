from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandCheck:
    name: str
    cmd: str
    cwd: str = "."
    timeout_s: int = 60
    required: bool = True


@dataclass
class AgentConfig:
    model: str
    temperature: float = 0.0
    top_p: float = 1.0
    num_ctx: int = 4096
    seed_optional: int | None = None


@dataclass
class RunnerConfig:
    ollama_host: str = "http://127.0.0.1:11434"
    validator_model: str = ""
    max_retries: int = 2
    abs_max_turns: int = 6
    apply_to_repo: bool = False
    execution_mode: str = "sandboxed"
    checks: list[CommandCheck] = field(default_factory=list)
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    allow_renames: bool = False
    parallel_decompose: bool = False  # reserved; current runtime is strictly sequential
    validator_input_cap: int = 24000

    @classmethod
    def from_json_file(cls, path: str | Path) -> "RunnerConfig":
        raw = json.loads(Path(path).read_text())
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RunnerConfig":
        checks = [CommandCheck(**item) for item in raw.get("checks", [])]
        agents: dict[str, AgentConfig] = {}
        for code, cfg in raw.get("agents", {}).items():
            if not (2 <= len(code) <= 4 and code.islower()):
                raise ValueError(f"Invalid agent code: {code}")
            agents[code] = AgentConfig(**cfg)
        cfg = cls(
            ollama_host=raw.get("ollama_host", "http://127.0.0.1:11434"),
            validator_model=raw["validator_model"],
            max_retries=max(0, min(9, int(raw.get("max_retries", 2)))),
            abs_max_turns=int(raw.get("abs_max_turns", 6)),
            apply_to_repo=bool(raw.get("apply_to_repo", False)),
            execution_mode=raw.get("execution_mode", "sandboxed"),
            checks=checks,
            agents=agents,
            allow_renames=bool(raw.get("allow_renames", False)),
            parallel_decompose=False,
            validator_input_cap=int(raw.get("validator_input_cap", 24000)),
        )
        if bool(raw.get("parallel_decompose", False)):
            raise ValueError("parallel_decompose is not supported in this build; execution is sequential only")
        if cfg.execution_mode not in {"sandboxed", "unsafe-local"}:
            raise ValueError("execution_mode must be sandboxed or unsafe-local")
        return cfg
