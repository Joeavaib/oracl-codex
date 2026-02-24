# Maestro

Maestro is a deterministic local orchestrator that coordinates specialist coding models via Ollama using TMP-S v2.4 validator records.

## Run

```bash
maestro run --repo PATH --request FILE_OR_STRING --cfg CFG.json [--sandboxed|--unsafe-local]
```

Outputs are written to `.maestro/runs/{sid}/{runid}` and worktrees/copies under `.maestro/work/{sid}/{runid}/repo`.


## Config

Example `CFG.json`:

```json
{
  "ollama_host": "http://127.0.0.1:11434",
  "ollama_timeout_s": 300,
  "validator_model": "qwen2.5-coder:14b",
  "max_retries": 2,
  "abs_max_turns": 6,
  "execution_mode": "sandboxed",
  "apply_to_repo": false,
  "allow_renames": false,
  "parallel_decompose": false,
  "validator_input_cap": 24000,
  "checks": [],
  "agents": {
    "imp": {"model": "qwen2.5-coder:14b"},
    "tst": {"model": "qwen2.5-coder:14b"},
    "doc": {"model": "qwen2.5-coder:14b"}
  }
}
```

### Fields

- `ollama_host`: Base URL for the Ollama HTTP API.
- `ollama_timeout_s`: Request timeout in seconds for Ollama generate calls (must be `> 0`).
- `validator_model`: Model used for validation records.
- `max_retries`: Maximum retry attempts for failed rounds.
- `abs_max_turns`: Hard cap on orchestration turns.
- `execution_mode`: One of `sandboxed` or `unsafe-local`.
- `apply_to_repo`: Whether to apply accepted patch to target repo.
- `checks`: Optional command checks to run.
- `agents`: Specialist agent model mapping.
- `allow_renames`: Allow file rename operations in patch application.
- `parallel_decompose`: Enable parallel decomposition mode.
- `validator_input_cap`: Input size cap for validator prompts.



## Execution model

Maestro executes specialist/validator calls **sequentially (one after another)**.
No concurrent specialist fan-out is performed in this build.



