import pytest

import cloudinit_aigen.agent.orchestrator as orchestrator_module
from cloudinit_aigen.agent.orchestrator import Orchestrator
from cloudinit_aigen.backends.base import BaseBackend
from cloudinit_aigen.tools.validator import ValidationResult


class StubBackend(BaseBackend):
    def complete(self, system: str, user: str) -> str:
        if "identify which cloud-init modules are needed" in system:
            return '{"modules": [{"name": "packages", "reason": "nginx"}]}'
        return "#cloud-config\npackages:\n  - nginx\n"


def test_orchestrator_rejects_non_positive_retries():
    with pytest.raises(ValueError, match="at least 1"):
        Orchestrator(StubBackend(), max_retries=0)


def test_failed_validation_keeps_cloud_config_header(monkeypatch):
    monkeypatch.setattr(
        orchestrator_module,
        "validate_yaml",
        lambda yaml_str, user_prompt=None: ValidationResult(ok=False, errors=["boom"]),
    )

    result = Orchestrator(StubBackend(), max_retries=1).run("nginx server")
    lines = result.splitlines()

    assert lines[0] == "#cloud-config"
    assert lines[1] == "# WARNING: Could not fully validate output"
    assert lines[2] == "# Validation error: boom"
