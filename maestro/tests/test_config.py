import pytest

from maestro.config import RunnerConfig


def test_parallel_decompose_rejected():
    with pytest.raises(ValueError):
        RunnerConfig.from_dict(
            {
                "validator_model": "val",
                "parallel_decompose": True,
                "agents": {"imp": {"model": "m"}},
            }
        )
