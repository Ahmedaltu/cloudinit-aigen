"""
Validator tool: runs yamllint and cloud-init schema checks on generated YAML.
Errors are fed back to the LLM for self-correction (ReAct loop).
"""
from __future__ import annotations
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, List
import yaml


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class _CommandValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


SSH_PUBLIC_KEY_RE = re.compile(
    r"\b(?:ssh-(?:rsa|ed25519)|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\n\r]+)?"
)
SSH_KEY_REQUEST_RE = re.compile(r"\b(?:ssh|public)\s+key\b|\bauthorized key\b", flags=re.IGNORECASE)
PASSWORDLESS_SUDO_RE = re.compile(r"\bpasswordless sudo\b|\bnopasswd\b", flags=re.IGNORECASE)
SSH_KEY_PLACEHOLDER_RE = re.compile(
    r"(your public ssh key|gohere|placeholder|example|replace me|insert key|\.\.\.)",
    flags=re.IGNORECASE,
)


def validate_yaml(yaml_str: str, user_prompt: str | None = None) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Check 1: #cloud-config header
    if not yaml_str.strip().startswith("#cloud-config"):
        errors.append("Missing '#cloud-config' header on first line")

    # Check 2: valid YAML syntax
    try:
        parsed = yaml.safe_load(yaml_str)
        if not isinstance(parsed, dict):
            errors.append("YAML top-level must be a mapping (dict)")
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return ValidationResult(ok=False, errors=errors)

    semantic_result = _run_semantic_checks(parsed, user_prompt)
    errors.extend(semantic_result.errors)
    warnings.extend(semantic_result.warnings)

    # Check 3: yamllint (if available)
    yamllint_result = _run_yamllint(yaml_str)
    errors.extend(yamllint_result.errors)
    warnings.extend(yamllint_result.warnings)

    # Check 4: cloud-init schema (if available)
    schema_result = _run_cloudinit_schema(yaml_str)
    errors.extend(schema_result.errors)
    warnings.extend(schema_result.warnings)

    return ValidationResult(ok=len(errors) == 0, errors=errors, warnings=warnings)


def _run_yamllint(yaml_str: str) -> _CommandValidationResult:
    try:
        result = subprocess.run(
            ["yamllint", "-d", "{extends: relaxed, rules: {line-length: {max: 120}}}", "-"],
            input=yaml_str, capture_output=True, text=True,
        )
    except FileNotFoundError:
        return _CommandValidationResult(
            warnings=["yamllint is not installed; skipping YAML lint validation"],
        )

    if result.returncode != 0:
        return _CommandValidationResult(
            errors=[f"yamllint: {line}" for line in _command_output_lines(result.stdout, result.stderr)],
        )
    return _CommandValidationResult()


def _run_cloudinit_schema(yaml_str: str) -> _CommandValidationResult:
    tmp: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_str)
            tmp = f.name
        result = subprocess.run(
            ["cloud-init", "schema", "--config-file", tmp],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return _CommandValidationResult(
            warnings=["cloud-init is not installed; skipping schema validation"],
        )
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    if result.returncode != 0:
        return _CommandValidationResult(
            errors=[f"schema: {line}" for line in _command_output_lines(result.stdout, result.stderr)],
        )
    return _CommandValidationResult()


def _command_output_lines(*chunks: str) -> List[str]:
    output = "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())
    lines = [line for line in output.splitlines() if line.strip()]
    return list(lines) if lines else ["command failed without output"]


def _run_semantic_checks(parsed: dict[str, Any], user_prompt: str | None) -> _CommandValidationResult:
    if not user_prompt:
        return _CommandValidationResult()

    errors: List[str] = []
    warnings: List[str] = []

    ssh_keys_in_yaml = _collect_ssh_authorized_keys(parsed)
    ssh_keys_in_prompt = [key.strip() for key in SSH_PUBLIC_KEY_RE.findall(user_prompt)]

    if PASSWORDLESS_SUDO_RE.search(user_prompt) and not _has_passwordless_sudo(parsed):
        errors.append("Prompt requests passwordless sudo, but no user defines sudo with NOPASSWD")

    if SSH_KEY_REQUEST_RE.search(user_prompt):
        if ssh_keys_in_prompt:
            if not ssh_keys_in_yaml:
                errors.append("Prompt includes an SSH public key, but output does not add it under ssh_authorized_keys")
            elif not any(prompt_key in ssh_keys_in_yaml for prompt_key in ssh_keys_in_prompt):
                errors.append("Output did not preserve the SSH public key from the prompt")
        else:
            if ssh_keys_in_yaml:
                errors.append("Prompt mentions an SSH key but does not include public key material; do not invent ssh_authorized_keys values")
            else:
                warnings.append("Prompt mentions an SSH key but does not include a public key; add one manually to ssh_authorized_keys")

    if any(SSH_KEY_PLACEHOLDER_RE.search(key) for key in ssh_keys_in_yaml):
        errors.append("ssh_authorized_keys contains a placeholder or example value; supply a real public key")

    return _CommandValidationResult(errors=errors, warnings=warnings)


def _collect_ssh_authorized_keys(node: Any) -> List[str]:
    values: List[str] = []

    if isinstance(node, dict):
        for key, value in node.items():
            if key == "ssh_authorized_keys":
                values.extend(_coerce_string_list(value))
            else:
                values.extend(_collect_ssh_authorized_keys(value))
    elif isinstance(node, list):
        for item in node:
            values.extend(_collect_ssh_authorized_keys(item))

    return values


def _coerce_string_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str)]
    return []


def _has_passwordless_sudo(parsed: dict[str, Any]) -> bool:
    users = parsed.get("users")
    if not isinstance(users, list):
        return False

    for user in users:
        if not isinstance(user, dict):
            continue
        sudo_value = user.get("sudo")
        if _contains_nopasswd(sudo_value):
            return True
    return False


def _contains_nopasswd(value: Any) -> bool:
    if isinstance(value, str):
        return "NOPASSWD" in value.upper()
    if isinstance(value, list):
        return any(isinstance(item, str) and "NOPASSWD" in item.upper() for item in value)
    return False
