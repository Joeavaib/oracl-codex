from __future__ import annotations

import json
import subprocess
from pathlib import Path

from maestro.config import RunnerConfig
from maestro.llm.prompts import VALIDATOR_SYSTEM_PROMPT, build_specialist_prompt
from maestro.log import RunLogger
from maestro.orch.artifact import parse_artifact
from maestro.orch.checks import run_checks
from maestro.orch.context import build_validator_input
from maestro.orch.delta import extract_delta
from maestro.orch.escalate import synthetic_meta_escalation
from maestro.orch.patch import apply_diff, apply_file_blocks
from maestro.orch.routing import route_initial_agent
from maestro.store import RunStore
from maestro.tmps.normalize import normalize_tmps
from maestro.tmps.parser import ParseError, parse_tmps

from maestro.tmps.validate import TMPSValidationError, validate_tmps_semantics

from maestro.tmps.validate import validate_tmps_semantics


MAX_TMPS_RETRIES = 2


class Orchestrator:
    def __init__(self, cfg: RunnerConfig, llm_client, validator_client=None):
        self.cfg = cfg
        self.llm = llm_client
        self.validator_llm = validator_client or llm_client

    def run(self, repo: Path, request_text: str) -> dict:
        store = RunStore(repo)
        run = store.init_run()
        sid, runid = run["sid"], run["runid"]
        run_root, work_repo = run["run_root"], run["work_repo"]
        store.clone_repo_to_work(work_repo)
        logger = RunLogger(run_root)
        store.write_text(run_root / "request.txt", request_text)
        store.write_json(run_root / "cfg.json", json.loads(json.dumps(self.cfg, default=lambda o: o.__dict__)))

        turn = 0
        budget = self.cfg.max_retries
        abs_remaining = self.cfg.abs_max_turns
        last_tmps_raw = "NONE"

        agent = route_initial_agent(request_text)
        specialist_prompt = request_text + "\nOutput unified diff or FILE blocks only."
        specialist_output = self._call_specialist(agent, specialist_prompt)

        while True:
            tdir = logger.turn_dir(turn)
            store.write_text(tdir / "specialist_agent.txt", agent)
            store.write_text(tdir / "specialist_prompt.txt", specialist_prompt)
            store.write_text(tdir / "specialist_output.txt", specialist_output)

            artifact = parse_artifact(specialist_output)
            store.write_json(tdir / "artifact_kind.json", {"kind": artifact.kind})

            patch_apply = {"ok": False, "error": "invalid artifact"}
            if artifact.kind == "diff":
                patch_apply = apply_diff(work_repo, artifact.payload, self.cfg.allow_renames)
            elif artifact.kind == "file_blocks":
                patch_apply = apply_file_blocks(work_repo, artifact.payload)
            store.write_json(tdir / "patch_apply.json", patch_apply)

            checks = run_checks(work_repo, self.cfg, patch_apply.get("ok", False))
            store.write_json(tdir / "checks.json", checks)

            val_input = build_validator_input(
                "NORMAL",
                request_text,
                "",
                artifact.kind,
                artifact.payload,
                patch_apply,
                checks,
                last_tmps_raw,
                self.cfg.validator_input_cap,
            )
            store.write_text(tdir / "validator_input.txt", val_input)

            budget_after_turn = max(0, budget - 1)
            raw, parsed = self._validate_tmps_with_retry(
                val_input,
                sid=sid,
                runid=runid,
                turn=turn,
                budget_after_turn=budget_after_turn,
            )
            store.write_text(tdir / "tmps_raw.txt", raw)

            parsed_snapshot = json.dumps(parsed, default=lambda o: o.__dict__, sort_keys=True)
            normalized = normalize_tmps(parsed, budget_after_turn)

            raw, parsed = self._validate_tmps_with_retry(val_input, sid=sid, runid=runid, turn=turn)
            store.write_text(tdir / "tmps_raw.txt", raw)

            parsed_snapshot = json.dumps(parsed, default=lambda o: o.__dict__, sort_keys=True)
            normalized = normalize_tmps(parsed, budget)

            normalized_snapshot = json.dumps(normalized, default=lambda o: o.__dict__, sort_keys=True)
            if self.cfg.strict_mode and normalized_snapshot != parsed_snapshot:
                strict_reason = "strict_mode: normalization changed TMP-S record"
                raw, parsed = self._validate_tmps_with_retry(
                    val_input,
                    sid=sid,
                    runid=runid,
                    turn=turn,
                    initial_reason=strict_reason,

                    budget_after_turn=budget_after_turn,
                )
                store.write_text(tdir / "tmps_raw_retry_strict.txt", raw)
                parsed_snapshot = json.dumps(parsed, default=lambda o: o.__dict__, sort_keys=True)
                normalized = normalize_tmps(parsed, budget_after_turn)

                )
                store.write_text(tdir / "tmps_raw_retry_strict.txt", raw)
                parsed_snapshot = json.dumps(parsed, default=lambda o: o.__dict__, sort_keys=True)
                normalized = normalize_tmps(parsed, budget)

                normalized_snapshot = json.dumps(normalized, default=lambda o: o.__dict__, sort_keys=True)
                if normalized_snapshot != parsed_snapshot:
                    raise ParseError(strict_reason)

            store.write_json(tdir / "tmps_parsed.json", json.loads(json.dumps(parsed, default=lambda o: o.__dict__)))
            store.write_json(tdir / "tmps_normalized.json", json.loads(json.dumps(normalized, default=lambda o: o.__dict__)))
            last_tmps_raw = raw

            final_dir = run_root / "final"
            final_dir.mkdir(parents=True, exist_ok=True)
            decision = normalized.c.decision
            store.write_text(final_dir / "decision.txt", decision)

            if decision == "A":
                diff = subprocess.run(["git", "diff", "--no-index", str(repo), str(work_repo)], capture_output=True, text=True).stdout
                store.write_text(final_dir / "final_patch.diff", diff)
                store.write_text(final_dir / "final_summary.md", f"Accepted on turn {turn}. checks={checks['summary']}\n")
                return {"decision": "A", "run_root": str(run_root)}
            if decision == "E" or abs_remaining <= 0:
                esc = final_dir / "escalation_bundle"
                esc.mkdir(parents=True, exist_ok=True)
                store.write_text(esc / "last_tmps_raw.txt", raw)
                store.write_json(esc / "last_tmps_normalized.json", json.loads(json.dumps(normalized, default=lambda o: o.__dict__)))
                store.write_text(esc / "last_specialist_output.txt", specialist_output)
                store.write_json(esc / "patch_apply.json", patch_apply)
                store.write_json(esc / "checks.json", checks)
                return {"decision": "E", "run_root": str(run_root)}

            if budget == 0:
                decision = "E"
                continue
            agent = normalized.b[0].agent
            task = normalized.b[0].action
            focus = normalized.c.focus
            delta = extract_delta(focus, artifact.payload, checks["summary"])
            specialist_prompt = build_specialist_prompt(normalized.c.strategy, agent, request_text, raw, delta, task)
            budget -= 1
            turn += 1
            abs_remaining -= 1
            specialist_output = self._call_specialist(agent, specialist_prompt)

    def _validator_options(self) -> dict[str, int | float]:

        options: dict[str, int | float | bool] = {
            "temperature": 0.0,
            "top_p": 1.0,
            "num_ctx": 4096,
            "num_predict": 512,

        options: dict[str, int | float] = {
            "temperature": 0.0,
            "top_p": 1.0,
            "num_predict": 512,
            "max_new_tokens": 512,

            "do_sample": False,
        }
        if self.cfg.validator_seed is not None:
            options["seed"] = int(self.cfg.validator_seed)
        return options

    def _validate_tmps_with_retry(
        self,
        val_input: str,
        sid: str,
        runid: str,
        turn: int,

        budget_after_turn: int,


        initial_reason: str | None = None,
    ) -> tuple[str, object]:
        prompt = val_input
        reason = initial_reason
        for attempt in range(MAX_TMPS_RETRIES + 1):
            if reason:
                prompt = f"{val_input}\n[INVALID_TMP-S] reason={reason} regenerate strictly valid TMP-S only"

            raw = self.validator_llm.generate(
                self.cfg.validator_model,
                prompt,
                options=self._validator_options(),
                system=VALIDATOR_SYSTEM_PROMPT,
            )
            try:
                parsed = parse_tmps(raw)

                validate_tmps_semantics(parsed, budget_after_turn)
                return raw, parsed
            except (ParseError, TMPSValidationError) as err:

                validate_tmps_semantics(parsed)
                return raw, parsed
            except ParseError as err:

                reason = str(err)
                if attempt == MAX_TMPS_RETRIES:
                    parsed = synthetic_meta_escalation(sid, runid, turn)
                    return "", parsed

        parsed = synthetic_meta_escalation(sid, runid, turn)
        return "", parsed

    def _call_specialist(self, agent: str, prompt: str) -> str:
        output = self._call_agent(agent, prompt)
        for _ in range(2):
            if parse_artifact(output).kind != "invalid":
                return output
            output = self._call_agent(
                agent,
                prompt
                + "\n\n[FORMAT_ERROR] Return ONLY one unified diff (starting with 'diff --git') "
                + "or FILE blocks (starting with 'FILE: '). No prose, no markdown fences.",
            )
        return output

    def _call_agent(self, agent: str, prompt: str) -> str:
        cfg = self.cfg.agents.get(agent)
        model = cfg.model if cfg else self.cfg.validator_model
        options = None
        if cfg:
            options = {
                "temperature": cfg.temperature,
                "top_p": cfg.top_p,
                "num_ctx": cfg.num_ctx,
            }
            if cfg.seed_optional is not None:
                options["seed"] = cfg.seed_optional
        return self.llm.generate(model, prompt, options=options)
