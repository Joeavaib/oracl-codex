import pytest

from maestro.config import RunnerConfig


def test_runner_config_ollama_timeout_default_and_override():
    cfg_default = RunnerConfig.from_dict({"validator_model": "val"})
    assert cfg_default.ollama_timeout_s == 300

    cfg_custom = RunnerConfig.from_dict({"validator_model": "val", "ollama_timeout_s": 45})
    assert cfg_custom.ollama_timeout_s == 45


@pytest.mark.parametrize("value", [0, -1])
def test_runner_config_ollama_timeout_must_be_positive(value):
    with pytest.raises(ValueError, match="ollama_timeout_s must be > 0"):
        RunnerConfig.from_dict({"validator_model": "val", "ollama_timeout_s": value})
