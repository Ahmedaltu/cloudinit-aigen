"""
Validator tool: runs yamllint and cloud-init schema checks on generated YAML.
Errors are fed back to the LLM for self-correction (ReAct loop).
"""
from __future__ import annotations
import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from typing import List
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


def validate_yaml(yaml_str: str) -> ValidationResult:
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
