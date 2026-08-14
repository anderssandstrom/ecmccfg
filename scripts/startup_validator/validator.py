from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True, order=True)
class Diagnostic:
    line: int
    column: int
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    diagnostics: tuple[Diagnostic, ...]
    script_calls: int
    command_calls: int
    references: tuple[str, ...]

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.diagnostics)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.diagnostics)


_FILE_MACROS = {"FILE", "PLC_FILE", "LUT_FILE", "SUBST_FILE", "TEMPLATE_FILE", "LOCAL_CONFIG"}
_EXECUTOR_RE = re.compile(r"^(?:\$\{[^}]+\})*\s*(\$\{SCRIPTEXEC\}|\$\(SCRIPTEXEC\)|iocshLoad)(?![A-Za-z0-9_])")


def _code_part(line: str) -> str:
    single = False
    double = False
    macro_closers: list[str] = []
    previous = ""
    for index, character in enumerate(line):
        pair = previous + character
        if not single and not double and pair == "${":
            macro_closers.append("}")
        elif not single and not double and pair == "$(":
            macro_closers.append(")")
        elif macro_closers and character == macro_closers[-1]:
            macro_closers.pop()
        elif character == "'" and not double:
            single = not single
        elif character == '"' and not single:
            double = not double
        elif character == "#" and not single and not double and not macro_closers:
            return line[:index]
        previous = character
    return line


def _quoted_segments(line: str) -> tuple[list[tuple[int, str]], bool]:
    segments: list[tuple[int, str]] = []
    quote: str | None = None
    start = 0
    value: list[str] = []
    for index, character in enumerate(line):
        if quote is None and character in ("'", '"'):
            quote = character
            start = index
            value = []
        elif quote == character:
            segments.append((start, "".join(value)))
            quote = None
        elif quote is not None:
            value.append(character)
    return segments, quote is not None


def _split_macros(value: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    single = False
    for character in value:
        if character == "'":
            single = not single
            current.append(character)
        elif character == "," and not single:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    parts.append("".join(current).strip())
    return parts


def _parse_macro_list(value: str, line: int, column: int) -> tuple[dict[str, str], list[Diagnostic]]:
    macros: dict[str, str] = {}
    diagnostics: list[Diagnostic] = []
    for item in _split_macros(value):
        if not item:
            diagnostics.append(Diagnostic(line, column, "warning", "W201", "empty item in macro list"))
            continue
        if "=" not in item:
            diagnostics.append(Diagnostic(line, column, "error", "E201", f"malformed macro item: {item}"))
            continue
        key, macro_value = item.split("=", 1)
        key = key.strip()
        macro_value = macro_value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            diagnostics.append(Diagnostic(line, column, "error", "E202", f"invalid macro name: {key or '<empty>'}"))
            continue
        if key in macros:
            diagnostics.append(Diagnostic(line, column, "error", "E203", f"duplicate macro: {key}"))
        macros[key] = macro_value.strip("'")
    return macros, diagnostics


def _macro_balance(line: str) -> bool:
    stack: list[str] = []
    index = 0
    while index < len(line):
        pair = line[index:index + 2]
        if pair == "${":
            stack.append("}")
            index += 2
            continue
        if pair == "$(":
            stack.append(")")
            index += 2
            continue
        if stack and line[index] == stack[-1]:
            stack.pop()
        index += 1
    return not stack


def _looks_local(key: str, value: str) -> bool:
    if not value or "$" in value or Path(value).is_absolute() or value.startswith("'"):
        return False
    if key in {"SUBST_FILE", "TEMPLATE_FILE"} and "/" not in value:
        return False
    return True


def validate(path: Path) -> ValidationResult:
    path = path.resolve()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        diagnostic = Diagnostic(1, 1, "error", "E001", f"cannot read file: {error}")
        return ValidationResult(path, (diagnostic,), 0, 0, ())

    diagnostics: list[Diagnostic] = []
    references: set[str] = set()
    script_calls = 0
    command_calls = 0
    for line_number, raw_line in enumerate(lines, start=1):
        code = _code_part(raw_line).strip()
        if not code:
            continue
        command_calls += 1
        if not _macro_balance(code):
            diagnostics.append(Diagnostic(line_number, 1, "error", "E101", "unbalanced EPICS macro expression"))
        segments, unterminated = _quoted_segments(code)
        if unterminated:
            diagnostics.append(Diagnostic(line_number, 1, "error", "E102", "unterminated quoted string"))

        executor_match = _EXECUTOR_RE.match(code)
        if executor_match is None:
            continue
        script_calls += 1
        if "configureSlave.cmd" in code:
            diagnostics.append(Diagnostic(line_number, 1, "warning", "W301", "legacy configureSlave.cmd; prefer addSlave.cmd plus applyComponent.cmd"))

        macro_segment: tuple[int, str] | None = None
        if len(segments) >= 2 and "=" in segments[-1][1]:
            macro_segment = segments[-1]
        elif len(segments) == 1 and "=" in segments[0][1]:
            text_before_quote = code[executor_match.end():segments[0][0]].strip().rstrip(",").strip()
            if text_before_quote:
                macro_segment = segments[0]
        if macro_segment is None:
            continue
        column, macro_text = macro_segment
        macros, macro_diagnostics = _parse_macro_list(macro_text, line_number, column + 1)
        diagnostics.extend(macro_diagnostics)
        for key, value in macros.items():
            if key not in _FILE_MACROS or not _looks_local(key, value):
                continue
            references.add(value)
            if not (path.parent / value).is_file():
                diagnostics.append(Diagnostic(line_number, column + 1, "error", "E301", f"referenced file does not exist: {value}"))

    return ValidationResult(path, tuple(sorted(set(diagnostics))), script_calls, command_calls, tuple(sorted(references)))
