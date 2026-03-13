#!/usr/bin/env python3
"""
Simple GUI validator for ecmc startup projects.

The tool opens a startup file, shows it in an editor, and validates local
project references such as YAML, PLC, and nested script files. Validation is
intentionally conservative: it focuses on file existence and known hardware
descriptors without trying to fully execute IOC shell logic.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_EXTENSIONS = {".cmd", ".script", ".iocsh"}
PATH_SUFFIXES = {
    ".ax",
    ".cfg",
    ".cmd",
    ".iocsh",
    ".pax",
    ".plc",
    ".req",
    ".script",
    ".subs",
    ".substitutions",
    ".template",
    ".txt",
    ".yaml",
    ".yml",
}
COMMENT_PREFIXES = ("#", "#-")
SCRIPT_EXEC_MARKERS = ("${SCRIPTEXEC}", "$(SCRIPTEXEC)", "iocshLoad", "runScript")
KNOWN_IOCSH_COMMANDS = {
    "dbLoadDatabase",
    "dbLoadRecords",
    "dbLoadTemplate",
    "ecmcConfig",
    "ecmcConfigOrDie",
    "ecmcEpicsEnvSetCalc",
    "ecmcEpicsEnvSetCalcTernary",
    "ecmcExit",
    "ecmcFileExist",
    "epicsEnvSet",
    "epicsEnvShow",
    "epicsEnvUnset",
    "iocshLoad",
    "on",
    "require",
    "runScript",
    "system",
}

PAIR_RE = re.compile(
    r"(?P<key>[A-Z_]+)\s*=\s*(?P<value>\"[^\"]*\"|'[^']*'|[^,\s)]+)",
    re.IGNORECASE,
)
MACRO_REF_RE = re.compile(r"\$\{([A-Za-z0-9_]+)(=([^}]*))?\}|\$\(([A-Za-z0-9_]+)(=([^\)]*))?\)")
EC_LINK_RE = re.compile(r"\bec(?P<master>\d+)\.s(?P<slave>\d+)\.(?P<entry>[A-Za-z_][A-Za-z0-9_]*)")
GENERIC_EC_ENTRY_NAMES = {"ONE", "ZERO", "slavestatus"}


@dataclass(frozen=True)
class FileReference:
    source: Path
    target: Path
    kind: str
    line: int
    exists: bool


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    source: Path
    line: int
    message: str
    target: Path | None = None


@dataclass
class ValidationResult:
    issues: list[ValidationIssue]
    references: list[FileReference]
    visited_files: list[Path]


@dataclass
class RepositoryInventory:
    ecmccfg_root: Path | None
    module_scripts: dict[str, list[Path]]
    module_macro_specs: dict[str, "MacroSpec"]
    module_macro_usage: dict[str, "FileMacroUsage"]
    hardware_descs: set[str]
    hardware_configs: dict[str, list[Path]]
    hardware_entries: dict[str, set[str]]
    known_commands: set[str]
    ecb_schema: dict[str, object] | None


@dataclass
class MacroSpec:
    allowed: set[str]
    required: set[str]


@dataclass
class FileMacroUsage:
    used: set[str]
    required: set[str]


@dataclass
class ParsedMappingLine:
    path: str
    value: str | None
    line: int


@dataclass(frozen=True)
class ExpandedTextLine:
    source: Path
    line: int
    text: str


def _find_ecmccfg_root(anchor: Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if anchor is not None:
        resolved_anchor = anchor.resolve()
        candidates.extend([resolved_anchor, *resolved_anchor.parents])

    script_dir = Path(__file__).resolve().parent
    candidates.extend([script_dir, *script_dir.parents])

    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "hardware").is_dir() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _index_by_name(paths: list[Path]) -> dict[str, list[Path]]:
    indexed: dict[str, list[Path]] = {}
    for path in sorted(paths):
        indexed.setdefault(path.name, []).append(path)
    return indexed


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    single = False
    double = False
    brace_depth = 0

    for char in text:
        if char == "'" and not double:
            single = not single
        elif char == '"' and not single:
            double = not double
        elif char in "({[" and not single and not double:
            brace_depth += 1
        elif char in ")}]" and not single and not double and brace_depth > 0:
            brace_depth -= 1

        if char == sep and not single and not double and brace_depth == 0:
            piece = "".join(current).strip()
            if piece:
                parts.append(piece)
            current = []
            continue

        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_argument_header(text: str) -> MacroSpec:
    match = re.search(r"^#-\s*Arguments:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return MacroSpec(set(), set())

    allowed: set[str] = set()
    required: set[str] = set()
    remainder = match.group(1).strip()
    optional_ranges = [(m.start(), m.end()) for m in re.finditer(r"\[[^\]]*\]", remainder)]

    def is_optional(index: int) -> bool:
        return any(start <= index < end for start, end in optional_ranges)

    for part in _split_top_level(remainder):
        token = part.strip()
        if not token:
            continue
        optional = is_optional(remainder.find(token))
        token = token.strip("[] ").strip()
        if "=" in token:
            token = token.split("=", 1)[0].strip()
        if token.startswith("["):
            token = token[1:].strip()
        if token.endswith("]"):
            token = token[:-1].strip()
        if token.lower() in {"n/a", "none"}:
            continue
        if not token:
            continue
        allowed.add(token)
        if not optional:
            required.add(token)
    return MacroSpec(allowed, required)


def _parse_param_names(text: str) -> set[str]:
    params: set[str] = set()
    for line in text.splitlines():
        match = re.search(r"\\param\s+([A-Z0-9_]+)", line)
        if match:
            params.add(match.group(1).strip())
    return params


def _parse_optional_macro_doc_names(text: str) -> set[str]:
    params: set[str] = set()
    in_block = False
    for line in text.splitlines():
        if re.search(r"Macros\s*\(optional\)", line, re.IGNORECASE):
            in_block = True
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if not stripped.startswith("#-d"):
            break
        match = re.search(r"#-d\s+([A-Z0-9_]+)\s*:", stripped)
        if match:
            params.add(match.group(1).strip())
            continue
        if stripped == "#-d":
            continue
        if params:
            break
    return params


def _build_macro_spec(path: Path) -> MacroSpec:
    try:
        text = _read_text(path)
    except Exception:
        return MacroSpec(set(), set())

    header_spec = _parse_argument_header(text)
    param_names = _parse_param_names(text)
    optional_macro_names = _parse_optional_macro_doc_names(text)
    allowed = set(header_spec.allowed) | param_names | optional_macro_names
    required = set(header_spec.required)
    return MacroSpec(allowed, required)


def _build_macro_usage(path: Path) -> FileMacroUsage:
    try:
        return _scan_file_macro_usage(_read_text(path))
    except Exception:
        return FileMacroUsage(set(), set())


def _build_repository_inventory(ecmccfg_root: Path | None) -> RepositoryInventory:
    if ecmccfg_root is None:
        return RepositoryInventory(
            ecmccfg_root=None,
            module_scripts={},
            module_macro_specs={},
            module_macro_usage={},
            hardware_descs=set(),
            hardware_configs={},
            hardware_entries={},
            known_commands=set(KNOWN_IOCSH_COMMANDS),
            ecb_schema=None,
        )

    module_script_paths = sorted((ecmccfg_root / "scripts").rglob("*.cmd"))
    startup_cmd = ecmccfg_root / "startup.cmd"
    if startup_cmd.exists():
        module_script_paths.append(startup_cmd)
    hardware_paths = sorted((ecmccfg_root / "hardware").rglob("ecmc*.cmd"))

    hardware_descs: set[str] = set()
    for path in hardware_paths:
        stem = path.stem
        if stem.lower().startswith("ecmc") and len(stem) > 4:
            hardware_descs.add(stem[4:])

    schema_path = ecmccfg_root / "scripts" / "jinja2" / "ecbSchema.json"
    ecb_schema = None
    if schema_path.exists():
        try:
            ecb_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            ecb_schema = None

    hardware_index = _index_by_name(hardware_paths)

    return RepositoryInventory(
        ecmccfg_root=ecmccfg_root.resolve(),
        module_scripts=_index_by_name(module_script_paths),
        module_macro_specs={path.name: _build_macro_spec(path) for path in module_script_paths},
        module_macro_usage={path.name: _build_macro_usage(path) for path in module_script_paths},
        hardware_descs=hardware_descs,
        hardware_configs=hardware_index,
        hardware_entries=_build_hardware_entry_inventory(hardware_index),
        known_commands=_scan_known_commands(ecmccfg_root),
        ecb_schema=ecb_schema,
    )


def _extract_cfg_call_args(text: str, call_name: str) -> list[str]:
    marker = f"Cfg.{call_name}("
    start = text.find(marker)
    if start < 0:
        return []
    remainder = text[start + len(marker) :]
    end = remainder.rfind(")")
    if end < 0:
        return []
    return _split_top_level(remainder[:end])


def _looks_like_entry_name(token: str) -> bool:
    cleaned = _strip_wrapper_pairs(_normalize_value(token))
    if not cleaned:
        return False
    if re.fullmatch(r"[-+]?(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?)", cleaned):
        return False
    return bool(re.search(r"[A-Za-z_]", cleaned) or "${" in cleaned or "$(" in cleaned)


def _extract_named_cfg_argument(args: list[str]) -> str:
    for token in reversed(args):
        cleaned = _strip_wrapper_pairs(_normalize_value(token))
        if _looks_like_entry_name(cleaned):
            return cleaned
    return ""


def _extract_hardware_entry_names(
    hardware_path: Path,
    hardware_index: dict[str, list[Path]],
    active_stack: tuple[Path, ...] = (),
) -> set[str]:
    resolved = hardware_path.resolve()
    if resolved in active_stack:
        return set()

    try:
        text = _read_text(resolved)
    except Exception:
        return set()

    entries: set[str] = set()
    child_stack = (*active_stack, resolved)

    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue

        for call_name in ("EcAddEntryComplete", "EcAddEntryDT", "EcAddDataDT", "WriteEcEntryIDString"):
            args = _extract_cfg_call_args(line, call_name)
            if not args:
                continue
            name = _extract_named_cfg_argument(args)
            if name:
                entries.add(name)

        if "addEcDataItem.cmd" in line:
            payload = _extract_script_call_macro_text(line)
            payload_pairs, _malformed = _parse_macro_payload(payload)
            name = next((value for key, value in payload_pairs if key == "NAME" and value), "")
            if name:
                entries.add(name)

        nested_target = _extract_script_target(line)
        nested_name = _extract_module_script_name(nested_target)
        if nested_name in hardware_index:
            for nested_path in hardware_index[nested_name]:
                entries.update(_extract_hardware_entry_names(nested_path, hardware_index, child_stack))

    return entries


def _build_hardware_entry_inventory(hardware_index: dict[str, list[Path]]) -> dict[str, set[str]]:
    inventory: dict[str, set[str]] = {}

    for file_name, paths in hardware_index.items():
        stem = Path(file_name).stem
        if not stem.lower().startswith("ecmc") or len(stem) <= 4:
            continue
        hw_desc = stem[4:]
        hw_entries = inventory.setdefault(hw_desc, set())
        for path in paths:
            hw_entries.update(_extract_hardware_entry_names(path, hardware_index))

    return inventory


def _normalize_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1].strip()
    return cleaned.strip("'\"").strip()


def _expand_text_macros(text: str, macros: dict[str, str], max_passes: int = 10) -> str:
    result = text
    for _ in range(max_passes):
        changed = False

        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            name = match.group(1) or match.group(4) or ""
            default = match.group(3) if match.group(1) else match.group(6)
            replacement = macros.get(name)
            if replacement is None or replacement == "":
                replacement = default
            if replacement is None:
                return match.group(0)
            replacement = str(replacement)
            if replacement != match.group(0):
                changed = True
            return replacement

        expanded = MACRO_REF_RE.sub(replace, result)
        result = expanded
        if not changed:
            break
    return result


def _parse_int_value(value: str) -> int | None:
    cleaned = _strip_wrapper_pairs(_normalize_value(value))
    if not cleaned:
        return None
    try:
        return int(cleaned, 0)
    except ValueError:
        return None


def _strip_wrapper_pairs(value: str) -> str:
    cleaned = value.strip()
    while len(cleaned) >= 2:
        if (cleaned[0], cleaned[-1]) in {("(", ")"), ('"', '"'), ("'", "'")}:
            cleaned = cleaned[1:-1].strip()
            continue
        break
    return cleaned


def _strip_inline_comment(line: str) -> str:
    single = False
    double = False
    for index, char in enumerate(line):
        if char == "'" and not double:
            single = not single
        elif char == '"' and not single:
            double = not double
        elif char == "#" and not single and not double:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def _parse_require_macro_pairs(line: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for match in re.finditer(r'"([^"]*)"|\'([^\']*)\'', line):
        payload = match.group(1) if match.group(1) is not None else match.group(2) or ""
        payload_pairs, _malformed = _parse_macro_payload(payload)
        pairs.extend(payload_pairs)
    return pairs


def _iter_key_values(line: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for match in PAIR_RE.finditer(line):
        key = match.group("key").strip().upper()
        value = _normalize_value(match.group("value"))
        pairs.append((key, value))
    return pairs


def _read_token(text: str, start: int) -> tuple[str, int]:
    length = len(text)
    while start < length and text[start].isspace():
        start += 1
    if start >= length:
        return "", start

    quote = text[start] if text[start] in {"'", '"'} else ""
    if quote:
        end = start + 1
        while end < length and text[end] != quote:
            end += 1
        token = text[start : min(end + 1, length)]
        return token, min(end + 1, length)

    depth = 0
    end = start
    while end < length:
        char = text[end]
        if char in "({[":
            depth += 1
        elif char in ")}]" and depth > 0:
            depth -= 1
        elif depth == 0 and (char.isspace() or char == ","):
            break
        end += 1
    return text[start:end], end


def _extract_script_target(line: str) -> str:
    for marker in SCRIPT_EXEC_MARKERS:
        offset = line.find(marker)
        if offset < 0:
            continue
        token, _ = _read_token(line, offset + len(marker))
        return _strip_wrapper_pairs(_normalize_value(token))
    return ""


def _extract_script_call_macro_text(line: str) -> str:
    for marker in SCRIPT_EXEC_MARKERS:
        offset = line.find(marker)
        if offset < 0:
            continue
        _, token_end = _read_token(line, offset + len(marker))
        remaining = line[token_end:].strip()
        if remaining.startswith(","):
            remaining = remaining[1:].strip()
        if not remaining:
            return ""
        payload, _ = _read_token(remaining, 0)
        return _strip_wrapper_pairs(_normalize_value(payload))
    return ""


def _strip_leading_macro_prefixes(line: str) -> str:
    remaining = line.lstrip()
    while remaining:
        if any(remaining.startswith(marker) for marker in SCRIPT_EXEC_MARKERS):
            return remaining
        if remaining.startswith("${"):
            end = remaining.find("}")
            if end < 0:
                return remaining
            remaining = remaining[end + 1 :].lstrip()
            continue
        if remaining.startswith("$("):
            end = remaining.find(")")
            if end < 0:
                return remaining
            remaining = remaining[end + 1 :].lstrip()
            continue
        break
    return remaining


def _extract_command_name(line: str) -> str:
    remaining = _strip_leading_macro_prefixes(line)
    for marker in SCRIPT_EXEC_MARKERS:
        if remaining.startswith(marker):
            return marker
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", remaining)
    return match.group(1) if match else ""


def _extract_module_script_name(target: str) -> str:
    cleaned = _strip_wrapper_pairs(_normalize_value(target))
    patterns = [
        r"(?:\$\{ecmccfg_DIR\}|\$\(ecmccfg_DIR\))(?P<name>[A-Za-z0-9_./-]+\.cmd)$",
        r"(?:\$\{ECMC_CONFIG_ROOT\}|\$\(ECMC_CONFIG_ROOT\))(?P<name>[A-Za-z0-9_./-]+\.cmd)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return Path(match.group("name")).name
    return ""


def _extract_epics_env_assignment(line: str) -> tuple[str, str] | None:
    match = re.match(r'epicsEnvSet\(\s*"?([A-Za-z0-9_]+)"?\s*,\s*(.+)\)\s*$', line)
    if not match:
        return None
    name = match.group(1).strip()
    value = _strip_wrapper_pairs(_normalize_value(match.group(2).strip()))
    return name, value


def _extract_epics_env_unset(line: str) -> str:
    match = re.match(r'epicsEnvUnset\(\s*"?([A-Za-z0-9_]+)"?\s*\)\s*$', line)
    return match.group(1).strip() if match else ""


def _parse_macro_payload(payload: str) -> tuple[list[tuple[str, str]], list[str]]:
    pairs: list[tuple[str, str]] = []
    malformed: list[str] = []
    if not payload:
        return pairs, malformed

    for part in _split_top_level(payload):
        token = part.strip()
        if not token:
            continue
        if "=" not in token:
            malformed.append(token)
            continue
        key, value = token.split("=", 1)
        key = key.strip().upper()
        value = _normalize_value(value)
        if not key or not re.fullmatch(r"[A-Z0-9_]+", key):
            malformed.append(token)
            continue
        pairs.append((key, value))
    return pairs, malformed


def _is_yaml_loader_script(module_script_name: str) -> bool:
    return module_script_name in {"loadYamlAxis.cmd", "loadYamlEnc.cmd", "loadYamlPlc.cmd"}


def _yaml_loader_schema_kind(module_script_name: str) -> str:
    mapping = {
        "loadYamlAxis.cmd": "axis",
        "loadYamlEnc.cmd": "encoder",
        "loadYamlPlc.cmd": "plc",
    }
    return mapping.get(module_script_name, "")


def _scan_file_macro_usage(text: str) -> FileMacroUsage:
    used: set[str] = set()
    required: set[str] = set()
    patterns = [
        re.compile(r"\$\{([A-Z0-9_]+)(=([^}]*))?\}"),
        re.compile(r"\$\(([A-Z0-9_]+)(=([^\)]*))?\)"),
    ]

    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue
        for pattern in patterns:
            for match in pattern.finditer(line):
                name = match.group(1).strip()
                has_default = match.group(2) is not None
                used.add(name)
                if not has_default:
                    required.add(name)
    return FileMacroUsage(used=used, required=required)


def _read_text_from_buffers(path: Path, buffer_lookup: dict[Path, str] | None) -> str | None:
    resolved = path.resolve()
    if buffer_lookup and resolved in buffer_lookup:
        return buffer_lookup[resolved]
    if resolved.exists():
        return _read_text(resolved)
    return None


def _resolve_plc_include_reference(include_name: str, current_dir: Path, include_paths: list[Path]) -> Path | None:
    cleaned = _normalize_value(include_name)
    if not cleaned or "${" in cleaned or "$(" in cleaned:
        return None

    candidate = Path(cleaned)
    if candidate.is_absolute():
        return candidate.resolve()

    search_dirs = [current_dir.resolve(), *[path.resolve() for path in include_paths]]
    for directory in search_dirs:
        candidates = [directory / cleaned]
        if directory.name != "plc_lib":
            candidates.append(directory / "plc_lib" / cleaned)
        for resolved_candidate in candidates:
            resolved = resolved_candidate.resolve()
            if resolved.exists():
                return resolved
        if "/" not in cleaned and "\\" not in cleaned:
            recursive_roots = [directory]
            if directory.name != "plc_lib":
                recursive_roots.append(directory / "plc_lib")
            for recursive_root in recursive_roots:
                if not recursive_root.exists() or not recursive_root.is_dir():
                    continue
                matches = sorted(recursive_root.rglob(cleaned))
                if matches:
                    return matches[0].resolve()

    return (current_dir / cleaned).resolve()


def _scan_plc_tree(
    plc_path: Path,
    include_paths: list[Path],
    macro_scope: dict[str, str],
    buffer_lookup: dict[Path, str] | None,
    active_stack: tuple[Path, ...] = (),
) -> tuple[list[ExpandedTextLine], FileMacroUsage, FileMacroUsage, list[ValidationIssue]]:
    resolved = plc_path.resolve()
    if resolved in active_stack:
        return (
            [],
            FileMacroUsage(used=set(), required=set()),
            FileMacroUsage(used=set(), required=set()),
            [
                ValidationIssue(
                    severity="warning",
                    source=resolved,
                    line=1,
                    message=f"Recursive PLC include detected for {resolved.name}",
                    target=resolved,
                )
            ],
        )

    text = _read_text_from_buffers(resolved, buffer_lookup)
    if text is None:
        return (
            [],
            FileMacroUsage(used=set(), required=set()),
            FileMacroUsage(used=set(), required=set()),
            [
                ValidationIssue(
                    severity="error",
                    source=resolved,
                    line=1,
                    message=f"Cannot inspect PLC include because file is missing: {resolved.name}",
                    target=resolved,
                )
            ],
        )

    expanded_lines: list[ExpandedTextLine] = []
    raw_used: set[str] = set()
    raw_required: set[str] = set()
    unresolved_used: set[str] = set()
    unresolved_required: set[str] = set()
    issues: list[ValidationIssue] = []
    pending_substitute: dict[str, str] = {}
    child_stack = (*active_stack, resolved)

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_inline_comment(raw_line)
        stripped = line.strip()
        if not stripped:
            continue

        substitute_match = re.match(r'substitute\s+"([^"]*)"\s*$', stripped)
        if substitute_match:
            substitute_pairs, malformed = _parse_macro_payload(substitute_match.group(1))
            pending_substitute = {key: value for key, value in substitute_pairs}
            for malformed_token in malformed:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=resolved,
                        line=line_no,
                        message=f"Malformed PLC substitute segment: {malformed_token}",
                        target=resolved,
                    )
                )
            continue

        include_match = re.match(r'include\s+"([^"]+)"\s*$', stripped)
        if include_match:
            include_target = _resolve_plc_include_reference(include_match.group(1), resolved.parent, include_paths)
            if include_target is None:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=resolved,
                        line=line_no,
                        message=f"Unable to resolve PLC include path: {include_match.group(1)}",
                    )
                )
            elif not include_target.exists():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        source=resolved,
                        line=line_no,
                        message=f"Missing PLC include: {include_match.group(1)}",
                        target=include_target,
                    )
                )
            else:
                child_scope = dict(macro_scope)
                child_scope.update(pending_substitute)
                child_lines, child_raw_usage, child_unresolved_usage, child_issues = _scan_plc_tree(
                    include_target,
                    include_paths,
                    child_scope,
                    buffer_lookup,
                    child_stack,
                )
                expanded_lines.extend(child_lines)
                raw_used.update(child_raw_usage.used)
                raw_required.update(child_raw_usage.required)
                unresolved_used.update(child_unresolved_usage.used)
                unresolved_required.update(child_unresolved_usage.required)
                issues.extend(child_issues)
            pending_substitute = {}
            continue

        expanded_line = _expand_text_macros(raw_line, macro_scope)
        expanded_lines.append(ExpandedTextLine(source=resolved, line=line_no, text=expanded_line))
        raw_usage = _scan_file_macro_usage(raw_line)
        unresolved_usage = _scan_file_macro_usage(expanded_line)
        raw_used.update(raw_usage.used)
        raw_required.update(raw_usage.required)
        unresolved_used.update(unresolved_usage.used)
        unresolved_required.update(unresolved_usage.required)

    return (
        expanded_lines,
        FileMacroUsage(used=raw_used, required=raw_required),
        FileMacroUsage(used=unresolved_used, required=unresolved_required),
        issues,
    )


def _entry_template_matches(entry_name: str, entry_template: str) -> bool:
    pattern = re.escape(entry_template)
    pattern = MACRO_REF_RE.sub(r"[A-Za-z0-9_:-]+", pattern)
    return bool(re.fullmatch(pattern, entry_name))


def _hardware_entry_exists(entry_name: str, hw_desc: str, inventory: RepositoryInventory) -> tuple[bool, bool]:
    if entry_name in GENERIC_EC_ENTRY_NAMES:
        return True, True

    if hw_desc not in inventory.hardware_entries:
        return False, False

    entry_templates = inventory.hardware_entries[hw_desc]
    return any(_entry_template_matches(entry_name, template) for template in entry_templates), True


def _validate_expanded_ec_links(
    lines: list[ExpandedTextLine],
    current_master_id: int,
    slave_hw_desc_by_id: dict[int, str],
    inventory: RepositoryInventory,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for expanded_line in lines:
        line = _strip_inline_comment(expanded_line.text)
        if not line.strip():
            continue

        for match in EC_LINK_RE.finditer(line):
            master_id = int(match.group("master"))
            slave_id = int(match.group("slave"))
            entry_name = match.group("entry")

            if entry_name == "mm":
                continue

            if master_id != current_master_id:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=expanded_line.source,
                        line=expanded_line.line,
                        message=(
                            f"EtherCAT link 'ec{master_id}.s{slave_id}.{entry_name}' uses master {master_id}, "
                            f"but the active master is {current_master_id}"
                        ),
                        target=expanded_line.source,
                    )
                )
                continue

            hw_desc = slave_hw_desc_by_id.get(slave_id)
            if hw_desc is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        source=expanded_line.source,
                        line=expanded_line.line,
                        message=(
                            f"EtherCAT link 'ec{master_id}.s{slave_id}.{entry_name}' refers to slave {slave_id}, "
                            "but that slave was not added with addSlave.cmd or configureSlave.cmd before this load"
                        ),
                        target=expanded_line.source,
                    )
                )
                continue

            exists, known_hw = _hardware_entry_exists(entry_name, hw_desc, inventory)
            if not known_hw:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=expanded_line.source,
                        line=expanded_line.line,
                        message=(
                            f"Cannot validate EtherCAT entry '{entry_name}' for HW_DESC '{hw_desc}' because no "
                            "hardware entry inventory is available"
                        ),
                        target=expanded_line.source,
                    )
                )
            elif not exists:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        source=expanded_line.source,
                        line=expanded_line.line,
                        message=(
                            f"EtherCAT entry '{entry_name}' is not defined by HW_DESC '{hw_desc}' "
                            f"for slave {slave_id}"
                        ),
                        target=expanded_line.source,
                    )
                )

    return issues


def _parse_simple_yaml_paths(text: str) -> list[ParsedMappingLine]:
    entries: list[ParsedMappingLine] = []
    stack: list[tuple[int, str]] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("- "):
            continue
        if ":" not in stripped:
            continue

        key, remainder = stripped.split(":", 1)
        key = key.strip().strip("'\"")
        if not key:
            continue

        while stack and indent <= stack[-1][0]:
            stack.pop()

        path_parts = [item[1] for item in stack] + [key]
        path = ".".join(path_parts)
        value = remainder.strip() or None
        entries.append(ParsedMappingLine(path=path, value=value, line=line_no))

        if value is None:
            stack.append((indent, key))

    return entries


def _schema_key_type_matches(value: str, declared_types: str) -> bool:
    if "${" in value or "$(" in value or "{{" in value:
        return True

    options = {item.strip().lower() for item in declared_types.split() if item.strip()}
    lowered = _normalize_value(value).strip().lower()
    if "string" in options:
        return True
    if "boolean" in options and lowered in {"true", "false", "yes", "no", "0", "1"}:
        return True
    if "integer" in options and re.fullmatch(r"[-+]?\d+", value.strip()):
        return True
    if "float" in options and re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value.strip()):
        return True
    return not options


def _get_schema_selector_default(schema: dict[str, object], selector_path: str) -> str | None:
    for schema_name, schema_info in schema.items():
        if not isinstance(schema_info, dict):
            continue
        schema_map = schema_info.get("schema")
        if not isinstance(schema_map, dict):
            continue
        selector_info = schema_map.get(selector_path)
        if isinstance(selector_info, dict) and "default" in selector_info:
            return str(selector_info["default"])
    return None


def _normalize_schema_selector_value(selector_path: str, value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip("'\" ").lower()
    if selector_path == "axis.type":
        aliases = {
            "joint": "1",
            "endeffector": "2",
        }
        return aliases.get(normalized, normalized)
    return normalized


def _select_grand_schema_variant(
    schema_kind: str,
    parsed_entries: list[ParsedMappingLine],
    ecb_schema: dict[str, object],
) -> dict[str, list[str]]:
    grand_schema = ecb_schema.get("grandSchema", {})
    kind_entries = grand_schema.get(schema_kind, {}) if isinstance(grand_schema, dict) else {}
    if not isinstance(kind_entries, dict):
        return {"required": [], "optional": []}

    values = {entry.path: entry.value for entry in parsed_entries if entry.value is not None}
    if len(kind_entries) == 1:
        only_value = next(iter(kind_entries.values()))
        if isinstance(only_value, dict):
            return {
                "required": str(only_value.get("required", "")).split(),
                "optional": str(only_value.get("optional", "")).split(),
            }
        return {"required": [], "optional": []}

    for selector, section_data in kind_entries.items():
        if not isinstance(section_data, dict) or "=" not in selector:
            continue
        selector_path, expected_value = selector.split("=", 1)
        actual_value = values.get(selector_path)
        if actual_value is None:
            actual_value = _get_schema_selector_default(ecb_schema, selector_path)
        normalized_actual = _normalize_schema_selector_value(selector_path, actual_value)
        normalized_expected = _normalize_schema_selector_value(selector_path, expected_value)
        if normalized_actual is not None and normalized_actual == normalized_expected:
            return {
                "required": str(section_data.get("required", "")).split(),
                "optional": str(section_data.get("optional", "")).split(),
            }
    return {"required": [], "optional": []}


def _validate_ecb_yaml(
    yaml_path: Path,
    yaml_text: str,
    schema_kind: str,
    ecb_schema: dict[str, object] | None,
) -> list[ValidationIssue]:
    if ecb_schema is None:
        return []

    parsed_entries = _parse_simple_yaml_paths(yaml_text)
    if not parsed_entries:
        return [
            ValidationIssue(
                severity="warning",
                source=yaml_path,
                line=1,
                message=f"Unable to parse YAML structure for ECB schema validation ({schema_kind})",
                target=yaml_path,
            )
        ]

    active = _select_grand_schema_variant(schema_kind, parsed_entries, ecb_schema)
    schema_names = active["required"] + active["optional"]
    schema_defs: dict[str, dict[str, object]] = {}
    allow_any_prefixes: set[str] = set()
    required_keys: dict[str, tuple[str, str]] = {}
    required_identifiers: dict[str, str] = {}

    for schema_name in schema_names:
        schema_info = ecb_schema.get(schema_name)
        if not isinstance(schema_info, dict):
            continue
        identifier = str(schema_info.get("identifier", "")).strip()
        if identifier:
            if schema_name in active["required"]:
                required_identifiers[identifier] = schema_name
        if schema_info.get("allowAnySubkey") and identifier:
            allow_any_prefixes.add(identifier)
        schema_map = schema_info.get("schema")
        if not isinstance(schema_map, dict):
            continue
        for key_path, key_info in schema_map.items():
            if not isinstance(key_info, dict):
                continue
            schema_defs[str(key_path)] = key_info
            if key_info.get("required"):
                required_keys[str(key_path)] = (schema_name, identifier)

    issues: list[ValidationIssue] = []
    line_by_path = {entry.path: entry.line for entry in parsed_entries}
    value_by_path = {entry.path: entry.value for entry in parsed_entries if entry.value is not None}
    top_level_keys = {entry.path for entry in parsed_entries if "." not in entry.path}

    for identifier, schema_name in required_identifiers.items():
        if identifier not in top_level_keys:
            issues.append(
                ValidationIssue(
                    severity="error",
                    source=yaml_path,
                    line=1,
                    message=f"Missing required YAML section '{identifier}' for {schema_kind} ({schema_name})",
                    target=yaml_path,
                )
            )

    for required_key, (schema_name, identifier) in required_keys.items():
        identifier_present = any(
            existing_path == identifier or existing_path.startswith(f"{identifier}.")
            for existing_path in line_by_path
        )
        if identifier_present and required_key not in value_by_path:
            issues.append(
                ValidationIssue(
                    severity="error",
                    source=yaml_path,
                    line=line_by_path.get(required_key.rsplit(".", 1)[0], 1),
                    message=f"Missing required YAML key '{required_key}' for {schema_kind} ({schema_name})",
                    target=yaml_path,
                )
            )

    for entry in parsed_entries:
        if entry.value is None:
            continue
        exact = schema_defs.get(entry.path)
        if exact is None:
            if not any(entry.path == prefix or entry.path.startswith(f"{prefix}.") for prefix in allow_any_prefixes):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=yaml_path,
                        line=entry.line,
                        message=f"YAML key '{entry.path}' is not defined in ECB schema '{schema_kind}'",
                        target=yaml_path,
                    )
                )
            continue

        declared_types = str(exact.get("type", "")).strip()
        if declared_types and not _schema_key_type_matches(entry.value, declared_types):
            issues.append(
                ValidationIssue(
                    severity="warning",
                    source=yaml_path,
                    line=entry.line,
                    message=f"YAML value for '{entry.path}' does not match ECB schema type '{declared_types}'",
                    target=yaml_path,
                )
            )

    return issues


def _scan_known_commands(ecmccfg_root: Path) -> set[str]:
    known = set(KNOWN_IOCSH_COMMANDS) | set(SCRIPT_EXEC_MARKERS)
    candidate_files: list[Path] = []

    startup_cmd = ecmccfg_root / "startup.cmd"
    if startup_cmd.exists():
        candidate_files.append(startup_cmd)

    for rel_dir in ("scripts", "general", "motion", "naming", "hardware", "examples"):
        base = ecmccfg_root / rel_dir
        if not base.exists():
            continue
        candidate_files.extend(sorted(base.rglob("*.cmd")))
        candidate_files.extend(sorted(base.rglob("*.script")))

    for candidate in candidate_files:
        try:
            text = _read_text(candidate)
        except Exception:
            continue
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith(COMMENT_PREFIXES):
                continue
            line = _strip_inline_comment(raw_line)
            if not line.strip():
                continue
            command_name = _extract_command_name(line)
            if command_name:
                known.add(command_name)

    return known


def _looks_like_local_path(value: str) -> bool:
    if not value or "${" in value or "$(" in value:
        return False
    if value.startswith("-"):
        return False
    if value.startswith(("./", "../", "/")):
        return True
    if "/" in value:
        return True
    suffix = Path(value).suffix.lower()
    return suffix in PATH_SUFFIXES


def _resolve_reference(value: str, base_dir: Path) -> Path | None:
    cleaned = _normalize_value(value)
    if not _looks_like_local_path(cleaned):
        return None
    path = Path(cleaned)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _resolve_inc_paths(value: str, base_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for chunk in value.split(":"):
        candidate = chunk.strip()
        if not candidate or candidate == ".":
            paths.append(base_dir.resolve())
            continue
        resolved = _resolve_reference(candidate, base_dir)
        if resolved is not None:
            paths.append(resolved)
    return paths


def _is_project_script(path: Path) -> bool:
    return path.suffix.lower() in SCRIPT_EXTENSIONS


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _validate_single_file(
    path: Path,
    text: str,
    inventory: RepositoryInventory,
    buffer_lookup: dict[Path, str] | None,
) -> tuple[list[ValidationIssue], list[FileReference], list[Path]]:
    issues: list[ValidationIssue] = []
    references: list[FileReference] = []
    nested_scripts: list[Path] = []
    base_dir = path.parent
    env_values: dict[str, str] = {}
    if inventory.ecmccfg_root is not None:
        config_root = inventory.ecmccfg_root.resolve() / "scripts"
        if not config_root.exists():
            config_root = inventory.ecmccfg_root.resolve()
        root_str = str(config_root)
        if not root_str.endswith("/"):
            root_str = f"{root_str}/"
        env_values["ecmccfg_DIR"] = root_str
        env_values["ECMC_CONFIG_ROOT"] = root_str
    current_master_id = 0
    next_slave_id = 0
    slave_hw_desc_by_id: dict[int, str] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue

        line = _strip_inline_comment(raw_line)
        if not line.strip():
            continue

        command_name = _extract_command_name(line)
        if command_name and command_name not in inventory.known_commands:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    source=path,
                    line=line_no,
                    message=f"Command '{command_name}' is not recognized as a valid startup command",
                )
            )

        if command_name == "require":
            for key, value in _parse_require_macro_pairs(line):
                expanded_value = _expand_text_macros(value, env_values)
                env_values[key] = expanded_value
                if key == "MASTER_ID":
                    master_id = _parse_int_value(expanded_value)
                    if master_id is not None:
                        current_master_id = master_id
                        env_values["MASTER_ID"] = str(master_id)
                        env_values["ECMC_EC_MASTER_ID"] = str(master_id)

        env_assignment = _extract_epics_env_assignment(line)
        if env_assignment is not None:
            env_name, env_value = env_assignment
            expanded_env_value = _expand_text_macros(env_value, env_values)
            env_values[env_name] = expanded_env_value
            numeric_env_value = _parse_int_value(expanded_env_value)
            if env_name in {"MASTER_ID", "ECMC_EC_MASTER_ID"} and numeric_env_value is not None:
                current_master_id = numeric_env_value
                env_values["MASTER_ID"] = str(numeric_env_value)
                env_values["ECMC_EC_MASTER_ID"] = str(numeric_env_value)
            elif env_name == "SLAVE_ID" and numeric_env_value is not None:
                next_slave_id = numeric_env_value

        unset_name = _extract_epics_env_unset(line)
        if unset_name:
            env_values.pop(unset_name, None)

        command_target = _extract_script_target(line)
        module_script_name = _extract_module_script_name(command_target)
        macro_payload = _extract_script_call_macro_text(line)
        payload_pairs, malformed_macros = _parse_macro_payload(macro_payload)
        if malformed_macros and module_script_name:
            for malformed in malformed_macros:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        source=path,
                        line=line_no,
                        message=f"Malformed macro segment for '{module_script_name}': {malformed}",
                    )
                )

        key_values = payload_pairs if macro_payload else _iter_key_values(line)
        key_map = {key: value for key, value in key_values if value}
        expanded_key_map = {key: _expand_text_macros(value, env_values) for key, value in key_map.items()}

        if module_script_name == "addMaster.cmd":
            master_id = _parse_int_value(expanded_key_map.get("MASTER_ID", env_values.get("MASTER_ID", "0")))
            if master_id is not None:
                current_master_id = master_id
                env_values["MASTER_ID"] = str(master_id)
                env_values["ECMC_EC_MASTER_ID"] = str(master_id)

        hw_desc = expanded_key_map.get("HW_DESC", env_values.get("HW_DESC", ""))
        if module_script_name in {"addSlave.cmd", "configureSlave.cmd"}:
            requested_slave_id = expanded_key_map.get("SLAVE_ID", env_values.get("SLAVE_ID", str(next_slave_id)))
            assigned_slave_id = _parse_int_value(requested_slave_id)
            if assigned_slave_id is None:
                assigned_slave_id = next_slave_id
            next_slave_id = assigned_slave_id + 1
            env_values["ECMC_EC_SLAVE_NUM"] = str(assigned_slave_id)
            env_values["SLAVE_ID"] = str(next_slave_id)
            if hw_desc:
                env_values["HW_DESC"] = hw_desc
                slave_hw_desc_by_id[assigned_slave_id] = hw_desc

        if hw_desc and "${" not in hw_desc and "$(" not in hw_desc and hw_desc not in inventory.hardware_descs:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    source=path,
                    line=line_no,
                    message=f"HW_DESC '{hw_desc}' was not found in hardware/",
                )
            )

        for key, value in key_values:
            expanded_value = _expand_text_macros(value, env_values)
            if key == "FILE" or key == "LOCAL_CONFIG":
                resolved = _resolve_reference(expanded_value, base_dir)
                if resolved is None:
                    continue
                exists = resolved.exists()
                references.append(FileReference(path, resolved, key.lower(), line_no, exists))
                if not exists:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            source=path,
                            line=line_no,
                            message=f"Missing {key.lower()} reference: {expanded_value}",
                            target=resolved,
                        )
                    )
                elif _is_project_script(resolved):
                    nested_scripts.append(resolved)
            elif key == "CONFIG":
                resolved = _resolve_reference(expanded_value, base_dir)
                if resolved is not None:
                    exists = resolved.exists()
                    references.append(FileReference(path, resolved, "config", line_no, exists))
                    if not exists:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                source=path,
                                line=line_no,
                                message=f"Missing config reference: {expanded_value}",
                                target=resolved,
                            )
                        )
                    elif _is_project_script(resolved):
                        nested_scripts.append(resolved)
                    continue

                if (
                    hw_desc
                    and "${" not in hw_desc
                    and "$(" not in hw_desc
                    and "${" not in expanded_value
                    and "$(" not in expanded_value
                ):
                    config_name = f"ecmc{hw_desc}{expanded_value}.cmd"
                    config_matches = inventory.hardware_configs.get(config_name, [])
                    config_target = config_matches[0] if config_matches else Path(config_name)
                    exists = bool(config_matches)
                    references.append(FileReference(path, config_target, "hardware-config", line_no, exists))
                    if not exists:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                source=path,
                                line=line_no,
                                message=f"Missing hardware config '{config_name}' in hardware/",
                                target=config_target,
                            )
                        )
            elif key == "INC":
                for inc_path in _resolve_inc_paths(expanded_value, base_dir):
                    exists = inc_path.exists()
                    references.append(FileReference(path, inc_path, "include-path", line_no, exists))
                    if not exists:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                source=path,
                                line=line_no,
                                message=f"Missing include path: {inc_path}",
                                target=inc_path,
                            )
                        )

        yaml_macro_usage: FileMacroUsage | None = None
        yaml_target = None
        if module_script_name and _is_yaml_loader_script(module_script_name):
            file_value = expanded_key_map.get("FILE", "")
            yaml_target = _resolve_reference(file_value, base_dir) if file_value else None
            if yaml_target is not None:
                yaml_text = _read_text_from_buffers(yaml_target, buffer_lookup)
                if yaml_text is not None:
                    yaml_macro_usage = _scan_file_macro_usage(yaml_text)
                    schema_kind = _yaml_loader_schema_kind(module_script_name)
                    if schema_kind:
                        issues.extend(_validate_ecb_yaml(yaml_target, yaml_text, schema_kind, inventory.ecb_schema))
                    yaml_scope = dict(env_values)
                    yaml_scope.update(expanded_key_map)
                    expanded_yaml_text = _expand_text_macros(yaml_text, yaml_scope)
                    yaml_lines = [
                        ExpandedTextLine(source=yaml_target, line=index, text=expanded_line)
                        for index, expanded_line in enumerate(expanded_yaml_text.splitlines(), start=1)
                    ]
                    issues.extend(
                        _validate_expanded_ec_links(yaml_lines, current_master_id, slave_hw_desc_by_id, inventory)
                    )
                else:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            source=path,
                            line=line_no,
                            message=f"Cannot inspect YAML macros because file is missing: {file_value}",
                            target=yaml_target,
                        )
                    )

        plc_raw_macro_usage: FileMacroUsage | None = None
        plc_unresolved_macro_usage: FileMacroUsage | None = None
        plc_target = None
        plc_macro_pairs: list[tuple[str, str]] = []
        if module_script_name == "loadPLCFile.cmd":
            file_value = expanded_key_map.get("FILE", "")
            plc_target = _resolve_reference(file_value, base_dir) if file_value else None
            plc_payload = expanded_key_map.get("PLC_MACROS", "")
            if plc_payload:
                plc_macro_pairs, malformed_plc_macros = _parse_macro_payload(plc_payload)
                for malformed in malformed_plc_macros:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            source=path,
                            line=line_no,
                            message=f"Malformed PLC_MACROS segment for 'loadPLCFile.cmd': {malformed}",
                            target=plc_target,
                        )
                    )
            if plc_target is not None:
                if _read_text_from_buffers(plc_target, buffer_lookup) is None:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            source=path,
                            line=line_no,
                            message=f"Cannot inspect PLC macros because file is missing: {file_value}",
                            target=plc_target,
                        )
                    )
                else:
                    plc_scope = dict(env_values)
                    plc_scope.update({key: value for key, value in plc_macro_pairs})
                    plc_id = _normalize_value(expanded_key_map.get("PLC_ID", env_values.get("ECMC_PLC_ID", "0"))) or "0"
                    plc_scope["SELF_ID"] = plc_id
                    plc_scope["SELF"] = f"plc{plc_id}"
                    plc_scope["M_ID"] = str(current_master_id)
                    plc_scope["M"] = f"ec{current_master_id}"
                    plc_include_paths = _resolve_inc_paths(expanded_key_map.get("INC", ""), base_dir)
                    if not plc_include_paths:
                        plc_include_paths = [plc_target.parent.resolve()]
                    plc_lines, plc_raw_macro_usage, plc_unresolved_macro_usage, plc_tree_issues = _scan_plc_tree(
                        plc_target,
                        plc_include_paths,
                        plc_scope,
                        buffer_lookup,
                    )
                    issues.extend(plc_tree_issues)
                    issues.extend(
                        _validate_expanded_ec_links(plc_lines, current_master_id, slave_hw_desc_by_id, inventory)
                    )

        if module_script_name:
            module_matches = inventory.module_scripts.get(module_script_name, [])
            if not module_matches:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        source=path,
                        line=line_no,
                        message=f"Script '{module_script_name}' was not found in scripts/",
                        target=Path(module_script_name),
                    )
                )
            else:
                macro_spec = inventory.module_macro_specs.get(module_script_name, MacroSpec(set(), set()))
                command_macro_usage = inventory.module_macro_usage.get(module_script_name, FileMacroUsage(set(), set()))
                command_defined_keys = set(macro_spec.allowed) | command_macro_usage.used
                passed_keys = {key for key, _value in payload_pairs}
                yaml_used_keys = yaml_macro_usage.used if yaml_macro_usage is not None else set()
                yaml_required_keys = yaml_macro_usage.required if yaml_macro_usage is not None else set()

                allowed_keys = set(command_defined_keys)
                if _is_yaml_loader_script(module_script_name):
                    allowed_keys |= yaml_used_keys

                if not _is_yaml_loader_script(module_script_name):
                    for unknown_key in sorted(passed_keys - allowed_keys):
                        if allowed_keys:
                            issues.append(
                                ValidationIssue(
                                    severity="warning",
                                    source=path,
                                    line=line_no,
                                    message=f"Macro '{unknown_key}' is not defined for '{module_script_name}'",
                                )
                            )
                for missing_key in sorted(macro_spec.required - passed_keys):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            source=path,
                            line=line_no,
                            message=f"Missing required macro '{missing_key}' for '{module_script_name}'",
                        )
                    )
                if _is_yaml_loader_script(module_script_name) and yaml_macro_usage is not None:
                    defined_keys = passed_keys | set(env_values.keys())
                    for missing_key in sorted(yaml_required_keys - defined_keys):
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                source=path,
                                line=line_no,
                                message=(
                                    f"Missing YAML macro '{missing_key}' required by "
                                    f"{yaml_target.name if yaml_target is not None else 'loaded YAML'} "
                                    f"for '{module_script_name}'"
                                ),
                                target=yaml_target,
                            )
                        )
                    extra_passed_keys = passed_keys - command_defined_keys
                    for unused_key in sorted(extra_passed_keys - yaml_used_keys):
                        issues.append(
                            ValidationIssue(
                                severity="warning",
                                source=path,
                                line=line_no,
                                message=(
                                    f"Macro '{unused_key}' is passed to '{module_script_name}' but not used "
                                    f"in {yaml_target.name if yaml_target is not None else 'the loaded YAML file'}"
                                ),
                                target=yaml_target,
                            )
                        )
                if module_script_name == "loadPLCFile.cmd" and plc_unresolved_macro_usage is not None:
                    reserved_plc_keys = {"SELF_ID", "SELF", "M_ID", "M"}
                    passed_plc_keys = {key for key, _value in plc_macro_pairs}
                    defined_plc_keys = passed_plc_keys | reserved_plc_keys | set(env_values.keys())
                    for missing_key in sorted(plc_unresolved_macro_usage.required - defined_plc_keys):
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                source=path,
                                line=line_no,
                                message=(
                                    f"Missing PLC macro '{missing_key}' required by "
                                    f"{plc_target.name if plc_target is not None else 'the loaded PLC file'} "
                                    "for 'loadPLCFile.cmd'"
                                ),
                                target=plc_target,
                            )
                        )
                    raw_used_keys = plc_raw_macro_usage.used if plc_raw_macro_usage is not None else set()
                    for unused_key in sorted(passed_plc_keys - raw_used_keys - command_defined_keys):
                        issues.append(
                            ValidationIssue(
                                severity="warning",
                                source=path,
                                line=line_no,
                                message=(
                                    f"PLC macro '{unused_key}' is passed to 'loadPLCFile.cmd' but not used "
                                    f"in {plc_target.name if plc_target is not None else 'the loaded PLC file'}"
                                ),
                                target=plc_target,
                            )
                        )

        resolved_command = _resolve_reference(_expand_text_macros(command_target, env_values), base_dir)
        if resolved_command is not None and not module_script_name:
            exists = resolved_command.exists()
            references.append(FileReference(path, resolved_command, "script", line_no, exists))
            if not exists:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        source=path,
                        line=line_no,
                        message=f"Missing nested script: {command_target}",
                        target=resolved_command,
                    )
                )
            elif _is_project_script(resolved_command):
                nested_scripts.append(resolved_command)

    return issues, references, nested_scripts


def validate_project(
    startup_path: Path,
    startup_text: str,
    inventory: RepositoryInventory,
    buffer_lookup: dict[Path, str] | None = None,
) -> ValidationResult:
    issues: list[ValidationIssue] = []
    references: list[FileReference] = []
    visited: list[Path] = []
    queued: list[Path] = [startup_path.resolve()]
    seen: set[Path] = set()
    buffer_lookup = buffer_lookup or {}

    while queued:
        current = queued.pop(0)
        if current in seen:
            continue
        seen.add(current)
        visited.append(current)

        if current == startup_path.resolve():
            text = startup_text
        elif current in buffer_lookup:
            text = buffer_lookup[current]
        elif current.exists():
            text = _read_text(current)
        else:
            issues.append(
                ValidationIssue(
                    severity="error",
                    source=current,
                    line=1,
                    message=f"Referenced file does not exist: {current}",
                    target=current,
                )
            )
            continue

        file_issues, file_refs, nested_scripts = _validate_single_file(current, text, inventory, buffer_lookup)
        issues.extend(file_issues)
        references.extend(file_refs)
        for nested in nested_scripts:
            resolved_nested = nested.resolve()
            if resolved_nested not in seen:
                queued.append(resolved_nested)

    return ValidationResult(issues=issues, references=references, visited_files=visited)


class ValidatorApp:
    def __init__(self, root, initial_startup: Path | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.title("ecmc Validator")
        self.root.geometry("1480x900")

        self.ecmccfg_root = _find_ecmccfg_root(initial_startup)
        self.inventory = _build_repository_inventory(self.ecmccfg_root)

        self.startup_var = tk.StringVar(value=str(initial_startup) if initial_startup else "")
        self.editor_file_var = tk.StringVar(value="(no file selected)")
        self.status_var = tk.StringVar(value="Ready")
        self.inventory_var = tk.StringVar(
            value=(
                f"scripts/: {len(self.inventory.module_scripts)} commands, "
                f"hardware/: {len(self.inventory.hardware_descs)} HW_DESC values"
            )
        )

        self.file_buffers: dict[Path, str] = {}
        self.current_edit_path: Path | None = None
        self.latest_result: ValidationResult | None = None
        self.issue_item_map: dict[str, ValidationIssue] = {}
        self.reference_item_map: dict[str, FileReference] = {}

        self._build_ui()

        if initial_startup is not None:
            self._open_startup(initial_startup.resolve(), validate_now=True)

    def _build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        top = ttk.Frame(self.root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Startup file").grid(row=0, column=0, sticky=tk.W)
        startup_entry = ttk.Entry(top, textvariable=self.startup_var, width=96)
        startup_entry.grid(row=0, column=1, sticky=tk.EW, padx=6)
        startup_entry.bind("<Return>", lambda _event: self._load_startup_from_entry())
        ttk.Button(top, text="Browse...", command=self._browse_startup).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(top, text="Open", command=self._load_startup_from_entry).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(top, text="Save", command=self._save_current_file).grid(row=0, column=4, padx=(0, 6))
        ttk.Button(top, text="Validate", command=self._validate_current_project).grid(row=0, column=5)
        ttk.Label(top, textvariable=self.inventory_var).grid(row=1, column=1, sticky=tk.W, padx=6, pady=(6, 0))
        top.columnconfigure(1, weight=1)

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Panedwindow(body, orient=tk.VERTICAL)
        right = ttk.Frame(body)
        body.add(left, weight=3)
        body.add(right, weight=5)

        issues_frame = ttk.Frame(left)
        files_frame = ttk.Frame(left)
        left.add(issues_frame, weight=3)
        left.add(files_frame, weight=2)

        ttk.Label(issues_frame, text="Validation Issues").pack(anchor=tk.W, pady=(0, 4))
        self.issue_tree = ttk.Treeview(
            issues_frame,
            columns=("severity", "location", "message"),
            show="headings",
        )
        self.issue_tree.heading("severity", text="Severity", anchor=tk.W)
        self.issue_tree.heading("location", text="Location", anchor=tk.W)
        self.issue_tree.heading("message", text="Message", anchor=tk.W)
        self.issue_tree.column("severity", width=90, stretch=False, anchor=tk.W)
        self.issue_tree.column("location", width=220, stretch=False, anchor=tk.W)
        self.issue_tree.column("message", width=520, stretch=True, anchor=tk.W)
        self.issue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        issue_scroll = ttk.Scrollbar(issues_frame, orient=tk.VERTICAL, command=self.issue_tree.yview)
        issue_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.issue_tree.configure(yscrollcommand=issue_scroll.set)
        self.issue_tree.bind("<<TreeviewSelect>>", self._on_issue_selected)
        self.issue_tree.tag_configure("error", foreground="#8b0000")
        self.issue_tree.tag_configure("warning", foreground="#8a5a00")
        self.issue_tree.tag_configure("info", foreground="#005a9c")

        ttk.Label(files_frame, text="Project Files").pack(anchor=tk.W, pady=(0, 4))
        self.reference_tree = ttk.Treeview(
            files_frame,
            columns=("kind", "status", "source"),
            show="tree headings",
        )
        self.reference_tree.heading("#0", text="Path", anchor=tk.W)
        self.reference_tree.heading("kind", text="Kind", anchor=tk.W)
        self.reference_tree.heading("status", text="Status", anchor=tk.W)
        self.reference_tree.heading("source", text="Referenced From", anchor=tk.W)
        self.reference_tree.column("#0", width=380, stretch=True, anchor=tk.W)
        self.reference_tree.column("kind", width=110, stretch=False, anchor=tk.W)
        self.reference_tree.column("status", width=90, stretch=False, anchor=tk.W)
        self.reference_tree.column("source", width=200, stretch=False, anchor=tk.W)
        self.reference_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ref_scroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.reference_tree.yview)
        ref_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.reference_tree.configure(yscrollcommand=ref_scroll.set)
        self.reference_tree.bind("<<TreeviewSelect>>", self._on_reference_selected)

        ttk.Label(right, text="Editor").pack(anchor=tk.W)
        editor_header = ttk.Frame(right)
        editor_header.pack(fill=tk.X, pady=(4, 4))
        ttk.Label(editor_header, textvariable=self.editor_file_var).pack(side=tk.LEFT)
        ttk.Button(editor_header, text="Reload From Disk", command=self._reload_current_from_disk).pack(side=tk.RIGHT)

        self.editor_text = tk.Text(right, wrap=tk.NONE, undo=True)
        self.editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.editor_text.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll = ttk.Scrollbar(right, orient=tk.HORIZONTAL, command=self.editor_text.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.editor_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.editor_text.tag_configure("current_line", background="#fff3bf")

        bottom = ttk.Frame(self.root, padding=(8, 4))
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Quit", command=self.root.destroy).pack(side=tk.RIGHT)

    def _browse_startup(self) -> None:
        from tkinter import filedialog

        current = self.startup_var.get().strip() or "."
        picked = filedialog.askopenfilename(
            title="Select ecmc startup file",
            initialdir=str(Path(current).expanduser().parent if current else Path.cwd()),
            filetypes=[
                ("Startup files", "*.cmd *.script *.iocsh"),
                ("All files", "*"),
            ],
        )
        if picked:
            self.startup_var.set(picked)
            self._load_startup_from_entry()

    def _load_startup_from_entry(self) -> None:
        from tkinter import messagebox

        value = self.startup_var.get().strip()
        if not value:
            messagebox.showerror("Missing startup file", "Select a startup file first.")
            return

        path = Path(value).expanduser()
        if not path.is_absolute():
            path = path.resolve()
        self._open_startup(path, validate_now=True)

    def _open_startup(self, path: Path, validate_now: bool) -> None:
        from tkinter import messagebox

        if not path.exists():
            messagebox.showerror("Startup file missing", f"File not found:\n{path}")
            return

        self.startup_var.set(str(path))
        self._open_file_in_editor(path)
        if validate_now:
            self._validate_current_project()

    def _remember_current_buffer(self) -> None:
        if self.current_edit_path is None:
            return
        self.file_buffers[self.current_edit_path] = self.editor_text.get("1.0", "end-1c")

    def _open_file_in_editor(self, path: Path, line: int | None = None) -> None:
        from tkinter import messagebox

        resolved = path.resolve()
        self._remember_current_buffer()

        if resolved in self.file_buffers:
            content = self.file_buffers[resolved]
        elif resolved.exists():
            content = _read_text(resolved)
            self.file_buffers[resolved] = content
        else:
            messagebox.showerror("File missing", f"Cannot open missing file:\n{resolved}")
            return

        self.current_edit_path = resolved
        self.editor_file_var.set(str(resolved))
        self.editor_text.delete("1.0", "end")
        self.editor_text.insert("1.0", content)
        self._highlight_editor_line(line)
        self.status_var.set(f"Opened {resolved.name}")

    def _highlight_editor_line(self, line: int | None) -> None:
        self.editor_text.tag_remove("current_line", "1.0", "end")
        if line is None or line <= 0:
            return
        start = f"{line}.0"
        end = f"{line}.0 lineend"
        self.editor_text.tag_add("current_line", start, end)
        self.editor_text.mark_set("insert", start)
        self.editor_text.see(start)

    def _save_current_file(self) -> None:
        from tkinter import messagebox

        if self.current_edit_path is None:
            messagebox.showerror("No file open", "There is no file loaded in the editor.")
            return

        self._remember_current_buffer()
        content = self.file_buffers[self.current_edit_path]
        self.current_edit_path.write_text(content, encoding="utf-8")
        self.status_var.set(f"Saved {self.current_edit_path.name}")

    def _reload_current_from_disk(self) -> None:
        from tkinter import messagebox

        if self.current_edit_path is None:
            messagebox.showerror("No file open", "There is no file loaded in the editor.")
            return
        if not self.current_edit_path.exists():
            messagebox.showerror("File missing", f"File not found:\n{self.current_edit_path}")
            return

        content = _read_text(self.current_edit_path)
        self.file_buffers[self.current_edit_path] = content
        self.editor_text.delete("1.0", "end")
        self.editor_text.insert("1.0", content)
        self.status_var.set(f"Reloaded {self.current_edit_path.name}")

    def _validate_current_project(self) -> None:
        from tkinter import messagebox

        startup_value = self.startup_var.get().strip()
        if not startup_value:
            messagebox.showerror("Missing startup file", "Select a startup file first.")
            return

        startup_path = Path(startup_value).expanduser()
        if not startup_path.is_absolute():
            startup_path = startup_path.resolve()
        if not startup_path.exists():
            messagebox.showerror("Startup file missing", f"File not found:\n{startup_path}")
            return

        self._remember_current_buffer()
        if startup_path not in self.file_buffers:
            self.file_buffers[startup_path] = _read_text(startup_path)
        startup_text = self.file_buffers[startup_path]

        result = validate_project(
            startup_path=startup_path,
            startup_text=startup_text,
            inventory=self.inventory,
            buffer_lookup=self.file_buffers,
        )
        self.latest_result = result
        self._populate_issues(startup_path, result)
        self._populate_references(startup_path, result)

        error_count = sum(1 for issue in result.issues if issue.severity == "error")
        warning_count = sum(1 for issue in result.issues if issue.severity == "warning")
        self.status_var.set(
            f"Validated {startup_path.name}: {error_count} error(s), {warning_count} warning(s), "
            f"{len(result.references)} reference(s)"
        )

    def _populate_issues(self, startup_path: Path, result: ValidationResult) -> None:
        self.issue_item_map.clear()
        for item in self.issue_tree.get_children():
            self.issue_tree.delete(item)

        sorted_issues = sorted(
            result.issues,
            key=lambda issue: (0 if issue.severity == "error" else 1, str(issue.source), issue.line, issue.message),
        )
        if not sorted_issues:
            info_issue = ValidationIssue(
                severity="info",
                source=startup_path,
                line=1,
                message="No validation issues found.",
            )
            sorted_issues = [info_issue]

        for index, issue in enumerate(sorted_issues):
            relative_source = self._relative_display(issue.source)
            location = f"{relative_source}:{issue.line}"
            item_id = self.issue_tree.insert(
                "",
                "end",
                values=(issue.severity.upper(), location, issue.message),
                tags=(issue.severity,),
            )
            self.issue_item_map[item_id] = issue
            if index == 0:
                self.issue_tree.selection_set(item_id)

    def _populate_references(self, startup_path: Path, result: ValidationResult) -> None:
        self.reference_item_map.clear()
        for item in self.reference_tree.get_children():
            self.reference_tree.delete(item)

        startup_item = self.reference_tree.insert(
            "",
            "end",
            text=self._relative_display(startup_path),
            values=("startup", "OK", "-"),
        )
        self.reference_item_map[startup_item] = FileReference(
            source=startup_path,
            target=startup_path,
            kind="startup",
            line=1,
            exists=True,
        )

        unique_refs: dict[tuple[Path, str, int], FileReference] = {}
        for ref in result.references:
            unique_refs[(ref.target, ref.kind, ref.line)] = ref

        for ref in sorted(unique_refs.values(), key=lambda item: (str(item.target), item.line, item.kind)):
            item_id = self.reference_tree.insert(
                "",
                "end",
                text=self._relative_display(ref.target),
                values=(
                    ref.kind,
                    "OK" if ref.exists else "MISSING",
                    f"{self._relative_display(ref.source)}:{ref.line}",
                ),
                tags=("missing",) if not ref.exists else (),
            )
            self.reference_item_map[item_id] = ref

    def _relative_display(self, path: Path) -> str:
        if self.ecmccfg_root is not None:
            try:
                return str(path.resolve().relative_to(self.ecmccfg_root.resolve()))
            except ValueError:
                pass
        startup_value = self.startup_var.get().strip()
        if startup_value:
            try:
                return str(path.resolve().relative_to(Path(startup_value).expanduser().resolve().parent))
            except ValueError:
                pass
        return str(path)

    def _on_issue_selected(self, _event=None) -> None:
        selected = self.issue_tree.selection()
        if not selected:
            return
        issue = self.issue_item_map.get(selected[0])
        if issue is None or issue.severity == "info":
            return
        self._open_file_in_editor(issue.source, line=issue.line)

    def _on_reference_selected(self, _event=None) -> None:
        selected = self.reference_tree.selection()
        if not selected:
            return
        ref = self.reference_item_map.get(selected[0])
        if ref is None or not ref.exists:
            return
        line = ref.line if ref.target == ref.source else None
        self._open_file_in_editor(ref.target, line=line)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GUI validator for ecmc startup projects.")
    parser.add_argument(
        "--startup",
        default="",
        help="Startup file to open immediately.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    initial_startup = Path(args.startup).expanduser().resolve() if args.startup else None

    try:
        import tkinter as tk
    except Exception as exc:
        print(f"GUI unavailable: {exc}", file=sys.stderr)
        return 2

    root = tk.Tk()
    ValidatorApp(root, initial_startup=initial_startup)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
