import json
from pathlib import Path

from maestro.config import RunnerConfig
from maestro.orch.orchestrator import Orchestrator


class MockLLM:
    def __init__(self):
        self.calls = 0

    def generate(self, model, prompt, options=None, system=None):
        self.calls += 1
        if system:
            return "\n".join([
                "V 2.4|s|r|0",
                "A 1111|9999|P|good",
                "B 1:imp|done",
                "B 2:tst|done",
                "B 3:doc|done",
                "C A|1|0|*",
            ])
        return """diff --git a/file.txt b/file.txt
new file mode 100644
index 0000000..ce01362
--- /dev/null
+++ b/file.txt
@@ -0,0 +1 @@
+hello
"""


def test_orchestrator_accept_writes_final_artifacts(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitkeep").write_text("")

    cfg = RunnerConfig.from_dict(
        {
            "validator_model": "val",
            "max_retries": 1,
            "abs_max_turns": 3,
            "execution_mode": "unsafe-local",
            "checks": [],
            "agents": {"imp": {"model": "impl"}},
        }
    )
    result = Orchestrator(cfg, MockLLM()).run(repo, "implement x")
    assert result["decision"] == "A"
    final = Path(result["run_root"]) / "final"
    assert (final / "final_patch.diff").exists()
    assert (final / "final_summary.md").exists()
