from __future__ import annotations

import argparse
import json
from pathlib import Path

from .validator import ValidationResult, validate


def _print_diagnostics(result: ValidationResult) -> None:
    for item in result.diagnostics:
        print(f"{result.path}:{item.line}:{item.column}: {item.severity} {item.code}: {item.message}")


def _json_result(result: ValidationResult) -> str:
    return json.dumps(
        {
            "path": str(result.path),
            "errors": result.errors,
            "warnings": result.warnings,
            "scriptCalls": result.script_calls,
            "commandLines": result.command_calls,
            "references": list(result.references),
            "diagnostics": [item.__dict__ for item in result.diagnostics],
        },
        indent=2,
        sort_keys=True,
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="ecmccfg-validate", description="Statically validate an ecmccfg IOC startup file")
    result.add_argument("startup", type=Path)
    result.add_argument("--format", choices=("text", "json"), default="text")
    result.add_argument("--warnings-as-errors", action="store_true")
    return result


def run(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = validate(args.startup)
    if args.format == "json":
        print(_json_result(result))
    else:
        _print_diagnostics(result)
        print(f"{result.errors} error(s), {result.warnings} warning(s), {result.script_calls} script call(s)")
    return 1 if result.errors or args.warnings_as_errors and result.warnings else 0


def main() -> None:
    raise SystemExit(run())
