import os
import json
import urllib.request
from cloudinit_aigen.backends.base import BaseBackend

class AnthropicBackend(BaseBackend):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["content"][0]["text"]
