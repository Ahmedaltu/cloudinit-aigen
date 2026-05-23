"""Planner: asks the LLM to identify which cloud-init modules are needed."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from cloudinit_aigen.backends.base import BaseBackend

PLAN_SYSTEM_PROMPT = """\
You are a cloud-init expert. Given a VM description, identify which cloud-init modules are needed.

Respond ONLY with a JSON object:
{
  "modules": [
    {"name": "users", "reason": "non-root deploy user required"},
    {"name": "packages", "reason": "Docker installation needed"}
  ]
}

Available modules: users, packages, runcmd, write_files, ssh_authorized_keys,
timezone, hostname, apt, snap, bootcmd, mounts, swap, ntp.

No explanation outside the JSON.
"""


@dataclass
class ModulePlan:
    name: str
    reason: str


@dataclass
class Plan:
    modules: List[ModulePlan]


class Planner:
    def __init__(self, backend: "BaseBackend"):
        self.backend = backend

    def plan(self, user_prompt: str) -> Plan:
        response = self.backend.complete(system=PLAN_SYSTEM_PROMPT, user=user_prompt)
        data = _extract_json_payload(response)
        modules_data = data.get("modules")
        if not isinstance(modules_data, list):
            raise ValueError("Planner response missing 'modules' list")
        modules = [ModulePlan(name=m["name"], reason=m["reason"]) for m in modules_data]
        return Plan(modules=modules)


def _extract_json_payload(response: str) -> dict[str, object]:
    text = response.strip()
    candidates: list[str] = []

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        candidates.append(fence_match.group(1).strip())

    candidates.append(text)

    json_start = text.find("{")
    json_end = text.rfind("}")
    if json_start != -1 and json_end != -1 and json_end >= json_start:
        candidates.append(text[json_start : json_end + 1].strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    raise ValueError("Planner response did not contain a valid JSON object")
