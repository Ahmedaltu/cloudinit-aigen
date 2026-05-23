"""Generator: produces cloud-init YAML from a Plan, and fixes on validation errors."""
from __future__ import annotations
import re
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from cloudinit_aigen.backends.base import BaseBackend
    from cloudinit_aigen.agent.planner import Plan

GENERATE_SYSTEM_PROMPT = """\
You are a cloud-init expert. Generate a valid cloud-init user-data YAML file.
- Start with exactly: #cloud-config
- Use only standard cloud-init modules
- YAML must be syntactically valid
- No explanation, no markdown fences, only the raw YAML
- Do NOT install in runcmd packages that are already listed under the packages module
- Do NOT define the same key twice on the same mapping (e.g. groups: appearing twice)
- Infer the target distro from the user's request. Default to Ubuntu/Debian if not specified
- Do not use sudo in runcmd, cloud-init already runs as root.
- Use 'packages' not 'package_install' to list packages to install.
- Only include runcmd entries that are directly relevant to the user's request.
"""

FIX_SYSTEM_PROMPT = """\
You are a cloud-init expert. Fix the provided cloud-init YAML based on the validation errors.
Return only the corrected YAML. Start with exactly: #cloud-config
"""


class Generator:
    def __init__(self, backend: "BaseBackend"):
        self.backend = backend

    def generate(self, user_prompt: str, plan: "Plan") -> str:
        module_list = ", ".join(m.name for m in plan.modules)
        user_msg = f"Request: {user_prompt}\n\nModules to include: {module_list}"
        response = self.backend.complete(system=GENERATE_SYSTEM_PROMPT, user=user_msg)
        return _normalize_yaml_response(response)

    def fix(self, yaml_str: str, errors: List[str]) -> str:
        error_text = "\n".join(f"- {e}" for e in errors)
        user_msg = f"Fix this cloud-init YAML:\n\n{yaml_str}\n\nValidation errors:\n{error_text}"
        response = self.backend.complete(system=FIX_SYSTEM_PROMPT, user=user_msg)
        return _normalize_yaml_response(response)


def _normalize_yaml_response(response: str) -> str:
    text = response.strip()

    fence_match = re.search(r"```(?:yaml|yml)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    header_index = text.find("#cloud-config")
    if header_index != -1:
        text = text[header_index:]

    return text.rstrip() + "\n"
