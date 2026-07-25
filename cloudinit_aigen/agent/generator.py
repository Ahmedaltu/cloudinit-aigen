"""Generator: produces cloud-init YAML from a Plan, and fixes on validation errors."""
from __future__ import annotations
import re
from typing import List, TYPE_CHECKING

from cloudinit_aigen.tools.module_docs import lookup_module

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
- Only include runcmd entries that are directly relevant to the user's request and cannot be expressed with native cloud-init modules.
- If passwordless sudo is requested for a user, set that user's sudo field with NOPASSWD access.
- Put ssh_authorized_keys under the intended user entry.
- Never invent SSH public keys, credentials, or placeholder secrets.
- If the request mentions an SSH key but does not include literal public key material, omit ssh_authorized_keys and add a brief YAML comment telling the user to supply a real public key.
"""

FIX_SYSTEM_PROMPT = """\
You are a cloud-init expert. Fix the provided cloud-init YAML based on the validation errors.
Return only the corrected YAML. Start with exactly: #cloud-config
- Preserve the original request intent while fixing the YAML.
- Never invent SSH public keys, credentials, or placeholder secrets.
- If passwordless sudo is requested for a user, set that user's sudo field with NOPASSWD access.
- Prefer native cloud-init modules over runcmd whenever possible.
- ssh_authorized_keys must always be nested under the user, never at the top level."
- For passwordless sudo, add 'sudo: ALL=(ALL) NOPASSWD:ALL' under the user entry.
"""

SSH_PUBLIC_KEY_RE = re.compile(
    r"\b(?:ssh-(?:rsa|ed25519)|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\n\r]+)?"
)
SSH_KEY_REQUEST_RE = re.compile(r"\b(?:ssh|public)\s+key\b|\bauthorized key\b", flags=re.IGNORECASE)


class Generator:
    def __init__(self, backend: "BaseBackend"):
        self.backend = backend

    def generate(self, user_prompt: str, plan: "Plan") -> str:
        module_list = ", ".join(m.name for m in plan.modules)
        user_msg = (
            f"Request: {user_prompt}\n\n"
            f"Modules to include: {module_list}\n\n"
            f"{_build_request_hints(user_prompt)}\n\n"
            f"Module reference snippets:\n{_build_module_reference_snippets(plan)}"
        )
        response = self.backend.complete(system=GENERATE_SYSTEM_PROMPT, user=user_msg)
        return _normalize_yaml_response(response)

    def fix(self, yaml_str: str, user_prompt: str, errors: List[str]) -> str:
        error_text = "\n".join(f"- {e}" for e in errors)
        user_msg = (
            f"Original request: {user_prompt}\n\n"
            f"{_build_request_hints(user_prompt)}\n\n"
            f"Fix this cloud-init YAML:\n\n{yaml_str}\n\n"
            f"Validation errors:\n{error_text}"
        )
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


def _build_module_reference_snippets(plan: "Plan") -> str:
    snippets = [lookup_module(module.name) for module in plan.modules]
    return "\n\n".join(snippets)


def _build_request_hints(user_prompt: str) -> str:
    hints = [
        "Additional constraints:",
        "- Do not invent values that are not present in the request.",
    ]
    if SSH_KEY_REQUEST_RE.search(user_prompt) and not SSH_PUBLIC_KEY_RE.search(user_prompt):
        hints.append("- The request mentions an SSH key, but no actual public key was provided. Do not fabricate one.")
    return "\n".join(hints)
