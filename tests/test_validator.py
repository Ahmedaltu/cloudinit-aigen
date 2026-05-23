from cloudinit_aigen.tools.validator import validate_yaml
import cloudinit_aigen.tools.validator as validator

VALID = "#cloud-config\npackages:\n  - nginx\n"
NO_HEADER = "packages:\n  - nginx\n"
BAD_YAML = "#cloud-config\npackages:\n  - nginx\n  invalid: [unclosed\n"

def test_valid_passes():
    assert validate_yaml(VALID).ok

def test_missing_header_fails():
    r = validate_yaml(NO_HEADER)
    assert not r.ok
    assert any("cloud-config" in e for e in r.errors)

def test_invalid_yaml_fails():
    assert not validate_yaml(BAD_YAML).ok


def test_missing_external_tools_are_reported_as_warnings(monkeypatch):
    def missing_command(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(validator.subprocess, "run", missing_command)
    result = validate_yaml(VALID)

    assert result.ok
    assert any("yamllint" in warning for warning in result.warnings)
    assert any("cloud-init" in warning for warning in result.warnings)
