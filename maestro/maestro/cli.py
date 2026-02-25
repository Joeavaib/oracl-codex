from __future__ import annotations

import argparse
from pathlib import Path

from maestro.config import RunnerConfig
from maestro.llm.ollama_client import OllamaClient
from maestro.orch.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(prog="maestro")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--repo", required=True)
    run.add_argument("--request", required=True)
    run.add_argument("--cfg", required=True)
    run.add_argument("--sandboxed", action="store_true")
    run.add_argument("--unsafe-local", action="store_true")

    args = parser.parse_args()
    if args.cmd == "run":
        cfg = RunnerConfig.from_json_file(args.cfg)
        if args.sandboxed:
            cfg.execution_mode = "sandboxed"
        if args.unsafe_local:
            cfg.execution_mode = "unsafe-local"

        req_arg = args.request
        req_path = Path(req_arg)
        request_text = req_path.read_text() if req_path.exists() else req_arg

        orch = Orchestrator(cfg, OllamaClient(cfg.ollama_host, timeout_s=cfg.ollama_timeout_s))
        result = orch.run(Path(args.repo), request_text)
        print(result)


if __name__ == "__main__":
    main()
