from cloudinit_aigen.tools.module_docs import lookup_module

def test_known_module():
    assert "packages:" in lookup_module("packages")

def test_unknown_module():
    assert "No inline docs" in lookup_module("nonexistent")
