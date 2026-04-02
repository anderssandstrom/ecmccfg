#!/usr/bin/env python3
"""Generate grouped Markdown hardware summaries from hardware snippets."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


HW_DESC_RE = re.compile(r'epicsEnvSet\("ECMC_EC_HWTYPE"\s+"([^"]+)"\)')
PRODUCT_ID_RE = re.compile(r'epicsEnvSet\("ECMC_EC_PRODUCT_ID"\s+"([^"]+)"\)')


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def git_output(*args: str) -> str:
    return subprocess.check_output(args, cwd=repo_root(), text=True).strip()


def github_blob_base_url() -> str:
    try:
        remote_url = git_output("git", "config", "--get", "remote.origin.url")
    except subprocess.CalledProcessError:
        return ""

    match = re.match(r"git@github\.com:(?P<repo>.+?)(?:\.git)?$", remote_url)
    if not match:
        match = re.match(r"https://github\.com/(?P<repo>.+?)(?:\.git)?$", remote_url)
    if not match:
        return ""

    repo_name = match.group("repo")
    return f"https://github.com/{repo_name}/blob/master/"


def extract_metadata(cmd_file: Path) -> tuple[str | None, str | None]:
    hw_desc = None
    product_id = None

    for line in cmd_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith("#"):
            continue
        hw_desc_match = HW_DESC_RE.search(line)
        if hw_desc_match and hw_desc is None:
            hw_desc = hw_desc_match.group(1)
        product_id_match = PRODUCT_ID_RE.search(line)
        if product_id_match and product_id is None:
            product_id = product_id_match.group(1).lower()
        if hw_desc is not None and product_id is not None:
            break

    return hw_desc, product_id


def collect_entries(hardware_dir: Path) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for cmd_file in sorted(hardware_dir.rglob("*.cmd")):
        hw_desc, product_id = extract_metadata(cmd_file)
        if product_id is None:
            continue
        rel_path = cmd_file.relative_to(hardware_dir.parent).as_posix()
        entries.append((hw_desc or cmd_file.stem, product_id, rel_path))
    return entries


def markdown_cell(value: str) -> str:
    return value.replace("|", r"\|")


def markdown_link(label: str, target: str) -> str:
    return f"[`{markdown_cell(label)}`]({target})"


def display_subdir_name(rel_path: str) -> str:
    top_level = rel_path.split("/", 2)[1]
    if top_level.lower().endswith("_slaves"):
        return top_level[:-7]
    return top_level


def format_path_link(rel_path: str, github_base_url: str) -> str:
    if github_base_url:
        return markdown_link(rel_path, github_base_url + rel_path)
    return f"`{markdown_cell(rel_path)}`"


def build_summary_markdown(
    entries: list[tuple[str, str, str]], include_front_matter: bool = False
) -> str:
    github_base_url = github_blob_base_url()
    grouped: dict[str, dict[str, list[str] | set[str]]] = defaultdict(
        lambda: {"hw_descs": set(), "subdirs": set(), "paths": []}
    )
    for hw_desc, product_id, rel_path in entries:
        grouped[product_id]["hw_descs"].add(hw_desc)
        grouped[product_id]["subdirs"].add(display_subdir_name(rel_path))
        grouped[product_id]["paths"].append(rel_path)

    parts: list[str] = []
    if include_front_matter:
        parts.extend(
            [
                "+++",
                'title = "Supported Slaves"',
                "weight = 17",
                "chapter = false",
                "+++",
                "",
            ]
        )

    parts.extend(
        [
            "# Supported Slaves",
            "",
            "Generated from `hardware/**/*.cmd`.",
            "",
            "| # | HW_DESC | Vendor/type | Product ID | Count | Paths |",
            "| ---: | --- | --- | --- | ---: | --- |",
        ]
    )
    for index, product_id in enumerate(sorted(grouped), start=1):
        hw_descs = sorted(grouped[product_id]["hw_descs"])
        subdirs = sorted(grouped[product_id]["subdirs"])
        paths = sorted(grouped[product_id]["paths"])
        subdirs_text = "<br>".join(f"`{markdown_cell(subdir)}`" for subdir in subdirs)
        hw_descs_text = "<br>".join(f"`{markdown_cell(hw_desc)}`" for hw_desc in hw_descs)
        paths_text = "<br>".join(
            format_path_link(path, github_base_url=github_base_url) for path in paths
        )
        parts.append(
            f"| {index} | {hw_descs_text} | {subdirs_text} | `{markdown_cell(product_id)}` | {len(paths)} | {paths_text} |"
        )

    return "\n".join(parts) + "\n"


def write_grouped_summary(
    output_path: Path, entries: list[tuple[str, str, str]], include_front_matter: bool = False
) -> None:
    output_path.write_text(
        build_summary_markdown(entries, include_front_matter=include_front_matter),
        encoding="utf-8",
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
    parser.add_argument(
        "--manual-output",
        type=Path,
        default=root / "hugo" / "content" / "manual" / "general_cfg" / "supported_slaves.md",
        help="Generated Hugo manual page path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    hardware_dir = args.hardware_dir.resolve()
    output_path = args.output.resolve()
    manual_output_path = args.manual_output.resolve()

    if not hardware_dir.is_dir():
        print(f"Hardware directory not found: {hardware_dir}", file=sys.stderr)
        return 1

    entries = collect_entries(hardware_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manual_output_path.parent.mkdir(parents=True, exist_ok=True)

    write_grouped_summary(output_path, entries)
    write_grouped_summary(manual_output_path, entries, include_front_matter=True)

    print(f"Wrote {output_path} from {len(entries)} hardware snippets.")
    print(f"Wrote {manual_output_path} from {len(entries)} hardware snippets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
