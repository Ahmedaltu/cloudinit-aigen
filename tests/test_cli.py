import argparse
import sys

from cloudinit_aigen import cli
from cloudinit_aigen.tools.validator import ValidationResult


def test_positive_int_rejects_zero():
    try:
        cli._positive_int("0")
    except argparse.ArgumentTypeError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected an ArgumentTypeError for zero retries")


def test_cli_prints_validation_warnings(monkeypatch, capsys):
    class FakeOrchestrator:
        def __init__(self, backend, verbose: bool, max_retries: int):
            self.last_validation_result = ValidationResult(
                ok=True,
                warnings=["yamllint is not installed; skipping YAML lint validation"],
            )

        def run(self, prompt: str, dry_run: bool = False) -> str:
            return "#cloud-config\npackages:\n  - nginx\n"

    monkeypatch.setattr(cli, "get_backend", lambda name, model=None: object())
    monkeypatch.setattr(cli, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(sys, "argv", ["cloudinit-aigen", "nginx server"])

    cli.main()

    captured = capsys.readouterr()
    assert "#cloud-config" in captured.out
    assert "yamllint is not installed" in captured.err
