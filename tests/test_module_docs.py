from cloudinit_aigen.tools.module_docs import lookup_module

def test_known_module():
    assert "packages:" in lookup_module("packages")

def test_ssh_authorized_keys_module():
    assert "ssh_authorized_keys:" in lookup_module("ssh_authorized_keys")

def test_unknown_module():
    assert "No inline docs" in lookup_module("nonexistent")
