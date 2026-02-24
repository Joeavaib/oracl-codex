# Maestro

Maestro is a deterministic local orchestrator that coordinates specialist coding models via Ollama using TMP-S v2.4 validator records.

## Run

```bash
maestro run --repo PATH --request FILE_OR_STRING --cfg CFG.json [--sandboxed|--unsafe-local]
```

Outputs are written to `.maestro/runs/{sid}/{runid}` and worktrees/copies under `.maestro/work/{sid}/{runid}/repo`.
