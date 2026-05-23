"""CLI entry point for cloudinit-aigen."""
import argparse
import sys
from cloudinit_aigen.agent.orchestrator import Orchestrator
from cloudinit_aigen.backends.factory import get_backend


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def main():
    parser = argparse.ArgumentParser(
        prog="cloudinit-aigen",
        description="Generate cloud-init user-data YAML from natural language.",
    )
    parser.add_argument("prompt", help="Natural language description of the VM")
    parser.add_argument("--backend", choices=["ollama", "anthropic"], default="ollama")
    parser.add_argument("--model", default=None)
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-retries", type=_positive_int, default=3)
    args = parser.parse_args()

    backend = get_backend(args.backend, model=args.model)
    orchestrator = Orchestrator(backend=backend, verbose=args.verbose, max_retries=args.max_retries)
    result = orchestrator.run(args.prompt, dry_run=args.dry_run)
    validation_result = orchestrator.last_validation_result

    if validation_result and validation_result.warnings:
        for warning in validation_result.warnings:
            print(f"Warning: {warning}", file=sys.stderr)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)
