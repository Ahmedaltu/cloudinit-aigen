from cloudinit_aigen.backends.base import BaseBackend

def get_backend(name: str, model: str | None = None) -> BaseBackend:
    if name == "ollama":
        from cloudinit_aigen.backends.ollama import OllamaBackend
        return OllamaBackend(model=model or "llama3")
    elif name == "anthropic":
        from cloudinit_aigen.backends.anthropic import AnthropicBackend
        return AnthropicBackend(model=model or "claude-sonnet-4-20250514")
    raise ValueError(f"Unknown backend: {name}")
