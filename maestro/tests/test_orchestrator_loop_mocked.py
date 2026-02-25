from pathlib import Path

from maestro.config import RunnerConfig
import pytest

from maestro.orch.orchestrator import Orchestrator


VALID_TMPS = "\n".join(
    [
        "V 2.4|s|r|0",
        "A 1111|9999|P|good",
        "B 1:imp|done",
        "B 2:tst|done",
        "B 3:doc|done",
        "C A|1|0|*",
    ]
)


class RecordingValidator:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, model, prompt, options=None, system=None):
        self.calls.append({"model": model, "prompt": prompt, "options": options, "system": system})
        return self.responses.pop(0)


class SpecialistMock:
    def generate(self, model, prompt, options=None, system=None):
        return """diff --git a/file.txt b/file.txt
new file mode 100644
index 0000000..ce01362
--- /dev/null
+++ b/file.txt
@@ -0,0 +1 @@
+hello
"""


def _build_cfg(strict_mode=False):
    return RunnerConfig.from_dict(
        {
            "validator_model": "val",
            "max_retries": 1,
            "abs_max_turns": 3,
            "execution_mode": "unsafe-local",
            "checks": [],
            "strict_mode": strict_mode,
            "validator_seed": 42,
            "agents": {"imp": {"model": "impl"}},
        }
    )


def test_orchestrator_accept_writes_final_artifacts(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitkeep").write_text("")

    cfg = _build_cfg()
    validator = RecordingValidator([VALID_TMPS])
    result = Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    assert result["decision"] == "A"
    final = Path(result["run_root"]) / "final"
    assert (final / "final_patch.diff").exists()
    assert (final / "final_summary.md").exists()


def test_orchestrator_validator_passes_deterministic_options(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg = _build_cfg()
    validator = RecordingValidator([VALID_TMPS])

    Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    opts = validator.calls[0]["options"]
    assert opts["temperature"] == 0.0
    assert opts["top_p"] == 1.0
    assert opts["num_predict"] == 512
    assert opts["max_new_tokens"] == 512
    assert opts["do_sample"] is False
    assert opts["seed"] == 42


def test_orchestrator_repair_loop_uses_invalid_tmps_reason(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg = _build_cfg()
    validator = RecordingValidator(["bad", VALID_TMPS])

    Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    assert len(validator.calls) == 2
    assert "[INVALID_TMP-S] reason=" in validator.calls[1]["prompt"]


def test_strict_mode_rejects_normalization_change(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg = _build_cfg(strict_mode=True)

    def fake_normalize(record, budget_after_turn):
        record.c.focus = "changed.focus"
        return record

    monkeypatch.setattr("maestro.orch.orchestrator.normalize_tmps", fake_normalize)

    validator = RecordingValidator([VALID_TMPS, VALID_TMPS])

    with pytest.raises(Exception, match="strict_mode: normalization changed TMP-S record"):
        Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    assert "strict_mode: normalization changed TMP-S record" in validator.calls[1]["prompt"]
