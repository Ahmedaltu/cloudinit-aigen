# Tests

Unit tests for every component of the agentic pipeline. No LLM or network needed — backends are stubbed, so the suite runs offline in a couple of seconds.

## Run

```bash
pip install -e ".[dev]"
pytest
```

## What's covered

| File | Covers |
|------|--------|
| `test_cli.py` | Argument validation, warning output |
| `test_planner.py` | Parsing LLM plan responses (plain JSON, markdown fences, preamble text) |
| `test_generator.py` | YAML normalization from LLM output, SSH-key hint injection |
| `test_orchestrator.py` | Retry limits, failed-validation annotation keeps `#cloud-config` header |
| `test_validator.py` | Header/syntax checks, missing yamllint/cloud-init fallbacks, passwordless-sudo and SSH-key semantic rules (no invented keys) |
| `test_module_docs.py` | Module reference lookup, unknown module handling |
