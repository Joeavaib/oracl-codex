from pathlib import Path

from maestro.config import RunnerConfig
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


class MockLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, model, prompt, options=None, system=None):
        self.calls += 1
        if system:
            return VALID_TMPS
        return """diff --git a/file.txt b/file.txt
new file mode 100644
index 0000000..ce01362
--- /dev/null
+++ b/file.txt
@@ -0,0 +1 @@
+hello
"""


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
            "agents": {"imp": {"model": "impl"}},
        }
    )


def test_orchestrator_accept_writes_final_artifacts(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitkeep").write_text("")

    cfg = _build_cfg()
    result = Orchestrator(cfg, MockLLM()).run(repo, "implement x")
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
    assert opts["seed"] == 42


def test_tmps_repair_loop_uses_error_reason_for_parse_and_semantics(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg = _build_cfg()
    semantically_invalid = VALID_TMPS.replace("C A|1|0|*", "C A|1|1|*")
    validator = RecordingValidator(["bad", semantically_invalid, VALID_TMPS])

    Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    assert "[INVALID_TMP-S] reason=" in validator.calls[1]["prompt"]
    assert "[INVALID_TMP-S] reason=" in validator.calls[2]["prompt"]


def test_strict_mode_rejects_normalization_changes(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    cfg = _build_cfg(strict_mode=True)

    tmps_needs_normalization = "\n".join(
        [
            "V 2.4|s|r|0",
            "A 1011|9999|H|bad",
            "B 1:imp|do",
            "B 2:tst|do",
            "B 3:doc|do",
            "C X|1|0|*",
        ]
    )
    validator = RecordingValidator([tmps_needs_normalization, VALID_TMPS])

    Orchestrator(cfg, SpecialistMock(), validator_client=validator).run(repo, "implement x")

    assert "strict_mode: normalization changed TMP-S record" in validator.calls[1]["prompt"]
