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


def test_passwordless_sudo_request_requires_nopasswd(monkeypatch):
    def missing_command(*args, **kwargs):
        raise FileNotFoundError

    yaml_str = "#cloud-config\nusers:\n  - name: deploy\n    groups: [sudo]\n"
    monkeypatch.setattr(validator.subprocess, "run", missing_command)
    result = validate_yaml(yaml_str, user_prompt="Ubuntu server with a deploy user and passwordless sudo")

    assert not result.ok
    assert any("passwordless sudo" in error for error in result.errors)


def test_prompt_ssh_key_without_key_material_warns_when_output_omits_it(monkeypatch):
    def missing_command(*args, **kwargs):
        raise FileNotFoundError

    yaml_str = "#cloud-config\nusers:\n  - name: deploy\n"
    monkeypatch.setattr(validator.subprocess, "run", missing_command)
    result = validate_yaml(yaml_str, user_prompt="Ubuntu server with my SSH key")

    assert result.ok
    assert any("does not include a public key" in warning for warning in result.warnings)


def test_invented_ssh_key_is_rejected(monkeypatch):
    def missing_command(*args, **kwargs):
        raise FileNotFoundError

    yaml_str = "#cloud-config\nusers:\n  - name: deploy\n    ssh_authorized_keys:\n      - ssh-rsa AAAArealisticlookingkeymaterial comment\n"
    monkeypatch.setattr(validator.subprocess, "run", missing_command)
    result = validate_yaml(yaml_str, user_prompt="Ubuntu server with my SSH key")

    assert not result.ok
    assert any("do not invent ssh_authorized_keys values" in error for error in result.errors)
