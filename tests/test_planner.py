import json
from cloudinit_aigen.agent.planner import Planner
from cloudinit_aigen.backends.base import BaseBackend

class MockBackend(BaseBackend):
    def __init__(self, response: str):
        self._response = response
    def complete(self, system: str, user: str) -> str:
        return self._response

def test_planner_parses_response():
    resp = json.dumps({"modules": [{"name": "packages", "reason": "nginx"}, {"name": "runcmd", "reason": "enable"}]})
    plan = Planner(MockBackend(resp)).plan("nginx server")
    assert len(plan.modules) == 2
    assert plan.modules[0].name == "packages"

def test_planner_handles_markdown_fences():
    resp = '```json\n{"modules": [{"name": "users", "reason": "deploy user"}]}\n```'
    plan = Planner(MockBackend(resp)).plan("VM with deploy user")
    assert plan.modules[0].name == "users"


def test_planner_handles_preamble_before_fenced_json():
    resp = 'Sure, here is the JSON:\n```json\n{"modules": [{"name": "packages", "reason": "nginx"}]}\n```'
    plan = Planner(MockBackend(resp)).plan("nginx server")
    assert plan.modules[0].name == "packages"
