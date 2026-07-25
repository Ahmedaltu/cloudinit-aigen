from cloudinit_aigen.agent.generator import Generator
from cloudinit_aigen.agent.planner import ModulePlan, Plan
from cloudinit_aigen.backends.base import BaseBackend


class MockBackend(BaseBackend):
    def __init__(self, response: str):
        self._response = response
        self.last_system = ""
        self.last_user = ""

    def complete(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        return self._response


def test_generate_strips_preamble_and_preserves_trailing_newline():
    response = "Here is the YAML:\n\n#cloud-config\npackages:\n  - nginx"
    generator = Generator(MockBackend(response))
    plan = Plan(modules=[ModulePlan(name="packages", reason="nginx")])

    result = generator.generate("nginx server", plan)

    assert result == "#cloud-config\npackages:\n  - nginx\n"


def test_fix_extracts_fenced_yaml_and_preserves_trailing_newline():
    response = "```yaml\nHere is the corrected YAML:\n\n#cloud-config\nusers:\n  - name: deploy\n```"
    generator = Generator(MockBackend(response))

    result = generator.fix("#cloud-config\nusers: []\n", "deploy user", ["example"])

    assert result == "#cloud-config\nusers:\n  - name: deploy\n"


def test_generate_adds_missing_ssh_key_hint_to_prompt():
    backend = MockBackend("#cloud-config\nusers: []\n")
    generator = Generator(backend)
    plan = Plan(modules=[ModulePlan(name="users", reason="deploy user")])

    generator.generate("Ubuntu server with a deploy user and my SSH key", plan)

    assert "Do not fabricate one." in backend.last_user
    assert "sudo: ALL=(ALL) NOPASSWD:ALL" in backend.last_user
