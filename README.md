# cloudinit-aigen

> Generate valid cloud-init `user-data` YAML from natural language using a local or cloud LLM.

```bash
$ cloudinit-aigen "Ubuntu VM with Docker, a non-root user called deploy, and my SSH key"
```

```yaml
#cloud-config
users:
  - name: deploy
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
packages:
  - docker.io
runcmd:
  - systemctl enable docker
  - usermod -aG docker deploy
```

## Features

- **Agentic loop** — plans modules, generates YAML, validates, self-corrects
- **Local-first** — defaults to Ollama (free, offline)
- **Optional cloud backend** — Anthropic Claude for higher quality
- **Schema validation** — yamllint + cloud-init schema on every generation
- **Installable via PPA** — `sudo apt install cloudinit-aigen`

## Install

```bash
# Via PPA (Ubuntu/Debian)
sudo add-apt-repository ppa:ahmedaltu/cloudinit-aigen
sudo apt install cloudinit-aigen

# Via pip
pip install cloudinit-aigen

# From source
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

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

## License

MIT
