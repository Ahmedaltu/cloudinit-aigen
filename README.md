# cloudinit-aigen

> Generate valid cloud-init `user-data` YAML from natural language using a local or cloud LLM.

## What it does

You describe a server in plain English; it gives you a ready-to-use `user-data` config file.
Paste that file into the "user data" / "cloud-init" field when creating a VM (AWS, DigitalOcean, Hetzner, multipass, …) and the server sets itself up on first boot — users, packages, keys, all of it. No manual SSH-and-configure needed.

## Features

- **Agentic loop** — plans modules, generates YAML, validates, self-corrects
- **Local-first** — defaults to Ollama (free, offline)
- **Optional cloud backend** — Anthropic Claude for higher quality
- **Schema validation** — yamllint + cloud-init schema on every generation

## Install

Install from source:

```bash
git clone https://github.com/Ahmedaltu/cloudinit-aigen
cd cloudinit-aigen
pip install -e .
```

## Usage

```bash
# Basic (uses Ollama/llama3 by default)
cloudinit-aigen "nginx server with a deploy user"

# Use Anthropic backend
cloudinit-aigen --backend anthropic "nginx server with a deploy user"

# Save to file
cloudinit-aigen "docker host" -o user-data.yaml

# Verbose: show agent reasoning steps
cloudinit-aigen --verbose "k3s node with monitoring"

# Dry-run: show plan without generating
cloudinit-aigen --dry-run "LAMP stack"
```

## Backends

| Backend | Model | Requires |
|---------|-------|----------|
| `ollama` (default) | llama3 / mistral | Ollama running locally |
| `anthropic` | claude-sonnet | `ANTHROPIC_API_KEY` env var |

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│         Orchestrator            │
│  plan → generate → validate     │
│         └── fix loop ──┘        │
└─────────────────────────────────┘
    │           │           │
    ▼           ▼           ▼
PlanTool   GenerateTool  ValidateTool
(LLM)      (LLM)         (yamllint +
                          schema check)
```

## Roadmap

- Planned: PyPI and Launchpad PPA distribution (currently source-install only)

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

## License

MIT
