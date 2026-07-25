"""
Agentic orchestrator: plan -> generate -> validate -> fix loop.

The core of the agentic pipeline:
1. Planner identifies which cloud-init modules are needed
2. Generator writes YAML for those modules
3. Validator checks with yamllint + cloud-init schema
4. If validation fails, errors are fed back to Generator for self-correction
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from cloudinit_aigen.agent.generator import Generator
from cloudinit_aigen.agent.planner import Planner
from cloudinit_aigen.tools.validator import ValidationResult, validate_yaml

if TYPE_CHECKING:
    from cloudinit_aigen.backends.base import BaseBackend


class Orchestrator:
    """Runs the full agentic plan -> generate -> validate -> fix loop."""

    def __init__(self, backend: "BaseBackend", verbose: bool = False, max_retries: int = 3):
        if max_retries < 1:
            raise ValueError("max_retries must be at least 1")
        self.backend = backend
        self.verbose = verbose
        self.max_retries = max_retries
        self.planner = Planner(backend)
        self.generator = Generator(backend)
        self.last_validation_result: ValidationResult | None = None

    def _log(self, msg: str):
        if self.verbose:
            print(f"[agent] {msg}", file=sys.stderr)

    def run(self, user_prompt: str, dry_run: bool = False) -> str:
        self.last_validation_result = None

        # Step 1: Plan
        self._log("Planning cloud-init modules...")
        plan = self.planner.plan(user_prompt)
        self._log(f"Plan: {[m.name for m in plan.modules]}")

        if dry_run:
            lines = ["# cloudinit-aigen dry-run plan", ""]
            for i, module in enumerate(plan.modules, 1):
                lines.append(f"{i}. {module.name}: {module.reason}")
            return "\n".join(lines)

        # Step 2: Generate
        self._log("Generating YAML...")
        yaml_str = self.generator.generate(user_prompt, plan)

        # Step 3: Validate + fix loop
        result: ValidationResult | None = None
        for attempt in range(self.max_retries):
            result = validate_yaml(yaml_str, user_prompt=user_prompt)
            self.last_validation_result = result
            if result.ok:
                if result.warnings:
                    self._log(f"Validation warnings: {result.warnings}")
                self._log(f"Validation passed on attempt {attempt + 1}")
                return yaml_str

            self._log(f"Validation failed (attempt {attempt + 1}/{self.max_retries}): {result.errors}")
            if attempt < self.max_retries - 1:
                self._log("Asking LLM to fix errors...")
                yaml_str = self.generator.fix(yaml_str, user_prompt, result.errors)

        assert result is not None
        return self._annotate_yaml(
            yaml_str,
            [
                "WARNING: Could not fully validate output",
                *[f"Validation error: {error}" for error in result.errors],
            ],
        )

    @staticmethod
    def _annotate_yaml(yaml_str: str, comments: list[str]) -> str:
        comment_lines = [f"# {comment}" for comment in comments]
        lines = yaml_str.splitlines()
        if lines and lines[0].strip() == "#cloud-config":
            annotated_lines = [lines[0], *comment_lines, ""]
            annotated_lines.extend(lines[1:])
        else:
            annotated_lines = [*comment_lines, "", *lines]

        annotated = "\n".join(annotated_lines)
        if yaml_str.endswith("\n"):
            return annotated + "\n"
        return annotated
