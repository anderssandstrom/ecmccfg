#!/usr/bin/env python3
"""Generate a grouped Markdown product-id summary from hardware snippets."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


PRODUCT_ID_RE = re.compile(r'epicsEnvSet\("ECMC_EC_PRODUCT_ID"\s+"([^"]+)"\)')


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def extract_product_id(cmd_file: Path) -> str | None:
    for line in cmd_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = PRODUCT_ID_RE.search(line)
        if match:
            return match.group(1).lower()
    return None


def collect_entries(hardware_dir: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for cmd_file in sorted(hardware_dir.rglob("*.cmd")):
        product_id = extract_product_id(cmd_file)
        if product_id is None:
            continue
        entries.append((product_id, cmd_file.relative_to(hardware_dir.parent).as_posix()))
    return entries


def markdown_cell(value: str) -> str:
    return value.replace("|", r"\|")


def write_grouped_summary(output_path: Path, entries: list[tuple[str, str]]) -> None:
    grouped: dict[str, list[str]] = defaultdict(list)
    for product_id, rel_path in entries:
        grouped[product_id].append(rel_path)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# Hardware Product ID Summary\n\n")
        handle.write("Generated from `hardware/**/*.cmd`.\n\n")
        handle.write("| # | Product ID | Count | Paths |\n")
        handle.write("| ---: | --- | ---: | --- |\n")
        for index, product_id in enumerate(sorted(grouped), start=1):
            paths = sorted(grouped[product_id])
            paths_text = "<br>".join(f"`{markdown_cell(path)}`" for path in paths)
            handle.write(
                f"| {index} | `{markdown_cell(product_id)}` | {len(paths)} | {paths_text} |\n"
            )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    default_hardware_dir = root / "hardware"
    parser = argparse.ArgumentParser(
        description="Summarize ECMC_EC_PRODUCT_ID usage in hardware snippets."
    )
    parser.add_argument(
        "--hardware-dir",
        type=Path,
        default=default_hardware_dir,
        help=f"Hardware directory to scan (default: {default_hardware_dir})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_hardware_dir / "product_id_summary.md",
        help="Output Markdown path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hardware_dir = args.hardware_dir.resolve()
    output_path = args.output.resolve()

    if not hardware_dir.is_dir():
        print(f"Hardware directory not found: {hardware_dir}", file=sys.stderr)
        return 1

    entries = collect_entries(hardware_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_grouped_summary(output_path, entries)

    print(f"Wrote {output_path} from {len(entries)} hardware snippets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
