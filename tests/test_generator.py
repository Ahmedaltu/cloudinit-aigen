from cloudinit_aigen.agent.generator import Generator
from cloudinit_aigen.agent.planner import ModulePlan, Plan
from cloudinit_aigen.backends.base import BaseBackend


class MockBackend(BaseBackend):
    def __init__(self, response: str):
        self._response = response

    def complete(self, system: str, user: str) -> str:
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

    result = generator.fix("#cloud-config\nusers: []\n", ["example"])

    assert result == "#cloud-config\nusers:\n  - name: deploy\n"
