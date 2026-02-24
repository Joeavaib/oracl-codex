from __future__ import annotations

import json
import urllib.request


class OllamaClient:
    def __init__(self, host: str):
        self.host = host.rstrip("/")

    def generate(self, model: str, prompt: str, options: dict | None = None, system: str | None = None) -> str:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options
        if system:
            payload["system"] = system
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("response", "")
