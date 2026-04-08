#!/usr/bin/env python3

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SCALAR_DECL_RE = re.compile(
    r"^\s*(?:const\s+)?([A-Za-z_][A-Za-z0-9_:]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\{[^;]*\}|=\s*[^;]*)?;\s*$",
    re.MULTILINE,
)
C_ARRAY_DECL_RE = re.compile(
    r"^\s*(?:const\s+)?([A-Za-z_][A-Za-z0-9_:]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]\s*(?:\{[^;]*\}|=\s*[^;]*)?;\s*$",
    re.MULTILINE,
)
STD_ARRAY_DECL_RE = re.compile(
    r"^\s*std::array<\s*([A-Za-z_][A-Za-z0-9_:]*)\s*,\s*(\d+)\s*>\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\{[^;]*\}|=\s*[^;]*)?;\s*$",
    re.MULTILINE,
)
EXPORT_CALL_RE = re.compile(
<<<<<<< HEAD
    r'(?:epics\.|\.)'
    r'(readOnly|writable|readOnlyArray|writableArray)\('
    r'\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)'
=======
    r'epics\.(readOnly|writable|readOnlyArray|writableArray)\(\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)'
>>>>>>> ad579a2f16f87df52b66f1eaf0dab26f1b6c3e66
)


@dataclass
class VarInfo:
    cpp_type: str
    count: int


@dataclass
class TemplateSpec:
    template: str
    columns: tuple[str, ...]
    values: dict[str, str]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate substitutions by scanning cpp_logic source exports."
    )
    parser.add_argument("--source", required=True, help="Input C++ source file")
    parser.add_argument("--output", required=True, help="Output substitutions file")
    parser.add_argument(
        "--param-prefix",
        default="",
        help="Optional asyn parameter prefix prepended to each exported variable name",
    )
    parser.add_argument(
        "--logic-name",
        default="",
        help="Optional logic name for substitutions header",
    )
    return parser.parse_args()


def sanitize_record_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") or "unnamed"


def type_to_ecmc(cpp_type: str) -> int:
    mapping = {
        "bool": 1,
        "int8_t": 2,
        "uint8_t": 3,
        "int16_t": 4,
        "uint16_t": 5,
        "int32_t": 6,
        "uint32_t": 7,
        "float": 8,
        "double": 9,
        "uint64_t": 10,
        "int64_t": 11,
    }
    if cpp_type not in mapping:
        raise ValueError(f"Unsupported exported type: {cpp_type}")
    return mapping[cpp_type]


def type_to_ftvl(value_type: int) -> str:
    if value_type in (1, 3):
        return "UCHAR"
    if value_type == 2:
        return "CHAR"
    if value_type == 4:
        return "SHORT"
    if value_type == 5:
        return "USHORT"
    if value_type in (6, 7):
        return "LONG"
    if value_type == 8:
        return "FLOAT"
    return "DOUBLE"


def scalar_template(value_type: int, writable: bool) -> str:
    if value_type == 1:
        return "ecmcCppLogicBo.template" if writable else "ecmcCppLogicBi.template"
    if value_type in (2, 3, 4, 5, 6, 7, 10, 11):
        return "ecmcCppLogicLongOut.template" if writable else "ecmcCppLogicLongIn.template"
    return "ecmcCppLogicAo.template" if writable else "ecmcCppLogicAi.template"


def collect_variables(source: str) -> dict[str, VarInfo]:
    variables: dict[str, VarInfo] = {}

    for cpp_type, name, count in C_ARRAY_DECL_RE.findall(source):
        variables[name] = VarInfo(cpp_type=cpp_type, count=int(count))

    for cpp_type, count, name in STD_ARRAY_DECL_RE.findall(source):
        variables[name] = VarInfo(cpp_type=cpp_type, count=int(count))

    for cpp_type, name in SCALAR_DECL_RE.findall(source):
        variables.setdefault(name, VarInfo(cpp_type=cpp_type, count=1))

    return variables


def build_specs(source_path: Path, param_prefix: str, logic_name: str) -> tuple[str, list[TemplateSpec]]:
    source = source_path.read_text(encoding="utf-8")
    variables = collect_variables(source)
    specs: list[TemplateSpec] = []

    for mode, export_name, variable_name in EXPORT_CALL_RE.findall(source):
        info = variables.get(variable_name)
        if info is None:
            raise ValueError(f"Could not resolve exported variable '{variable_name}' from source")

        writable = mode in ("writable", "writableArray")
        value_type = type_to_ecmc(info.cpp_type)
        param_name = f"{param_prefix}{export_name}" if param_prefix else export_name
        rec_name = sanitize_record_name(export_name)

        if info.count > 1 or mode in ("readOnlyArray", "writableArray"):
            template = (
                "ecmcCppLogicWaveformOut.template"
                if writable
                else "ecmcCppLogicWaveformIn.template"
            )
            specs.append(
                TemplateSpec(
                    template=template,
                    columns=("REC", "PARAM", "DESC", "NELM", "FTVL"),
                    values={
                        "REC": rec_name,
                        "PARAM": param_name,
                        "DESC": export_name,
                        "NELM": str(info.count),
                        "FTVL": type_to_ftvl(value_type),
                    },
                )
            )
            continue

        template = scalar_template(value_type, writable)
        values = {
            "REC": rec_name,
            "PARAM": param_name,
            "DESC": export_name,
        }
        columns = ("REC", "PARAM", "DESC")
        if template in ("ecmcCppLogicAi.template", "ecmcCppLogicAo.template"):
            values["PREC"] = "3"
            columns = ("REC", "PARAM", "DESC", "PREC")
        specs.append(TemplateSpec(template=template, columns=columns, values=values))

    resolved_logic_name = logic_name or source_path.stem
    return resolved_logic_name, specs


def render_substitutions(logic_name: str, specs: list[TemplateSpec]) -> str:
    lines = [
        "# Auto-generated C++ logic substitutions",
        f"# Logic: {logic_name}",
        'global { P = "$(P)" PORT = "$(PORT)" }',
        "",
    ]

    grouped: dict[str, list[TemplateSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.template, []).append(spec)

    for template, template_specs in grouped.items():
        columns = template_specs[0].columns
        lines.append(f"file {template} {{")
        lines.append("  pattern { " + ", ".join(columns) + " }")
        for spec in template_specs:
            row = ", ".join(f'"{spec.values[column]}"' for column in columns)
            lines.append(f"  {{ {row} }}")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


def main():
    args = parse_args()
    logic_name, specs = build_specs(Path(args.source), args.param_prefix, args.logic_name)
    Path(args.output).write_text(render_substitutions(logic_name, specs), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
