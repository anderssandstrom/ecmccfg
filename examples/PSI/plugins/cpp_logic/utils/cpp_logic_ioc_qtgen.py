#!/usr/bin/env python3

import argparse
import csv
import io
import pathlib
import re
import sys


FILE_RE = re.compile(r'^\s*file\s+([^\s{]+)\s*\{\s*$')
PATTERN_RE = re.compile(r'^\s*pattern\s*\{\s*([^}]*)\s*\}\s*$')
ROW_RE = re.compile(r'^\s*\{(.*)\}\s*$')
GLOBAL_RE = re.compile(r'^\s*global\s*\{\s*(.*?)\s*\}\s*$')
GLOBAL_ASSIGN_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"')
MACRO_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a simple IOC-local caQtDM panel from cpp_logic substitutions."
    )
    parser.add_argument("--input", required=True, help="Input substitutions file")
    parser.add_argument("--output", required=True, help="Output .ui file")
    parser.add_argument("--title", default="", help="Optional panel title")
    parser.add_argument(
        "--pv-prefix",
        default="",
        help="Optional explicit PV prefix, for example IOC:",
    )
    return parser.parse_args()


def parse_csv_row(text: str):
    reader = csv.reader(io.StringIO(text), skipinitialspace=True)
    return next(reader)


def substitute_macros(value: str, macros: dict):
    def repl(match):
        key = match.group(1)
        return macros.get(key, match.group(0))

    return MACRO_RE.sub(repl, value)


def row_kind(template_name: str):
    if template_name in ("ecmcCppLogicAo.template", "ecmcCppLogicLongOut.template"):
        return "w_scalar"
    if template_name == "ecmcCppLogicBo.template":
        return "w_bool"
    if template_name in ("ecmcCppLogicAi.template", "ecmcCppLogicLongIn.template"):
        return "r_scalar"
    if template_name == "ecmcCppLogicBi.template":
        return "r_bool"
    if template_name == "ecmcCppLogicStringIn.template":
        return "r_string"
    if template_name == "ecmcCppLogicWaveformIn.template":
        return "r_array"
    if template_name == "ecmcCppLogicWaveformOut.template":
        return "w_array"
    return ""


def parse_substitutions(path: pathlib.Path):
    macros = {}
    records = []
    current_template = ""
    current_pattern = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = GLOBAL_RE.match(line)
        if match:
            for key, value in GLOBAL_ASSIGN_RE.findall(match.group(1)):
                macros[key] = value
            continue

        match = FILE_RE.match(line)
        if match:
            current_template = pathlib.Path(match.group(1)).name
            current_pattern = []
            continue

        match = PATTERN_RE.match(line)
        if match:
            current_pattern = [part.strip() for part in match.group(1).split(",")]
            continue

        if line == "}":
            current_template = ""
            current_pattern = []
            continue

        match = ROW_RE.match(line)
        if match and current_template and current_pattern:
            values = [
                substitute_macros(value, macros).strip()
                for value in parse_csv_row(match.group(1))
            ]
            row = dict(zip(current_pattern, values))
            kind = row_kind(current_template)
            if not kind:
                continue
            records.append(
                {
                    "template": current_template,
                    "kind": kind,
                    "rec": row.get("REC", ""),
                    "desc": row.get("DESC", row.get("REC", "")),
                }
            )

    return macros, records


def esc(text: str):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def row_height(kind: str):
    if kind in ("r_array", "w_array"):
        return 104
    return 30


def widget_xml(record: dict, index: int, y: int, pv_prefix: str):
    label = esc(record["rec"])
    desc = esc(record["desc"])
    pv = esc(f"{pv_prefix}{record['rec']}")
    kind = record["kind"]

    parts = []
    if kind in ("r_array", "w_array"):
        parts.append(
            f'''  <widget class="caLabel" name="caLabelName{index}">
   <property name="geometry"><rect><x>10</x><y>{y + 2}</y><width>210</width><height>18</height></rect></property>
   <property name="text"><string>{label}</string></property>
  </widget>'''
        )
        parts.append(
            f'''  <widget class="caLabel" name="caLabelDesc{index}">
   <property name="geometry"><rect><x>10</x><y>{y + 22}</y><width>210</width><height>34</height></rect></property>
   <property name="text"><string>{desc}</string></property>
   <property name="wordWrap"><bool>true</bool></property>
  </widget>'''
        )
        parts.append(
            f'''  <widget class="caWaveTable" name="caWaveTable{index}">
   <property name="geometry"><rect><x>240</x><y>{y}</y><width>350</width><height>82</height></rect></property>
   <property name="channel" stdset="0"><string notr="true">{pv}</string></property>
   <property name="numberOfColumns"><number>1</number></property>
   <row/>
   <column/>
   <item row="0" column="0">
    <property name="font"><font/></property>
    <property name="textAlignment"><set>AlignLeft|AlignLeading</set></property>
   </item>
  </widget>'''
        )
        return "\n".join(parts)

    parts.append(
        f'''  <widget class="caLabel" name="caLabelName{index}">
   <property name="geometry"><rect><x>10</x><y>{y + 4}</y><width>220</width><height>18</height></rect></property>
   <property name="text"><string>{label}</string></property>
  </widget>'''
    )

    if kind == "w_scalar":
        parts.append(
            f'''  <widget class="caTextEntry" name="caTextEntry{index}">
   <property name="geometry"><rect><x>240</x><y>{y}</y><width>120</width><height>22</height></rect></property>
   <property name="channel" stdset="0"><string notr="true">{pv}</string></property>
  </widget>'''
        )
    elif kind == "w_bool":
        parts.append(
            f'''  <widget class="caToggleButton" name="caToggleButton{index}">
   <property name="geometry"><rect><x>240</x><y>{y}</y><width>90</width><height>22</height></rect></property>
   <property name="text"><string>set</string></property>
   <property name="channel" stdset="0"><string notr="true">{pv}</string></property>
  </widget>'''
        )
    else:
        parts.append(
            f'''  <widget class="caLineEdit" name="caLineEdit{index}">
   <property name="geometry"><rect><x>240</x><y>{y}</y><width>120</width><height>22</height></rect></property>
   <property name="channel" stdset="0"><string notr="true">{pv}</string></property>
   <property name="colorMode"><enum>caLineEdit::Static</enum></property>
   <property name="precisionMode"><enum>caLineEdit::Channel</enum></property>
   <property name="limitsMode"><enum>caLineEdit::Channel</enum></property>
   <property name="unitsEnabled"><bool>true</bool></property>
  </widget>'''
        )

    parts.append(
        f'''  <widget class="caLabel" name="caLabelDesc{index}">
   <property name="geometry"><rect><x>375</x><y>{y + 4}</y><width>215</width><height>18</height></rect></property>
   <property name="text"><string>{desc}</string></property>
  </widget>'''
    )
    return "\n".join(parts)


def generate_ui(title: str, records: list, pv_prefix: str):
    header_height = 56
    width = 610
    body_height = 24
    if records:
        body_height += sum(row_height(record["kind"]) for record in records)
    else:
        body_height += 36
    total_height = header_height + body_height

    widgets = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>{width}</width>
    <height>{total_height}</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>{esc(title)}</string>
  </property>
  <widget class="caLabel" name="caLabelTitle">
   <property name="geometry"><rect><x>10</x><y>10</y><width>480</width><height>21</height></rect></property>
   <property name="text"><string>{esc(title)}</string></property>
   <property name="font"><font><pointsize>12</pointsize><bold>true</bold></font></property>
  </widget>
  <widget class="caLabel" name="caLabelHint">
   <property name="geometry"><rect><x>10</x><y>34</y><width>560</width><height>16</height></rect></property>
   <property name="text"><string>Auto-generated from cpp_logic substitutions</string></property>
  </widget>'''
    ]

    y = header_height
    if records:
        for index, record in enumerate(records):
            widgets.append(widget_xml(record, index, y, pv_prefix))
            y += row_height(record["kind"])
    else:
        widgets.append(
            f'''  <widget class="caLabel" name="caLabelEmpty">
   <property name="geometry"><rect><x>10</x><y>{y}</y><width>400</width><height>18</height></rect></property>
   <property name="text"><string>No exported epics.* records found in substitutions</string></property>
  </widget>'''
        )

    widgets.append(
        """ </widget>
 <customwidgets>
  <customwidget>
   <class>caLabel</class>
   <extends>QWidget</extends>
   <header>caLabel</header>
  </customwidget>
  <customwidget>
   <class>caLineEdit</class>
   <extends>QLineEdit</extends>
   <header>caLineEdit</header>
  </customwidget>
  <customwidget>
   <class>caTextEntry</class>
   <extends>caLineEdit</extends>
   <header>caTextEntry</header>
  </customwidget>
  <customwidget>
   <class>caToggleButton</class>
   <extends>QWidget</extends>
   <header>caToggleButton</header>
  </customwidget>
  <customwidget>
   <class>caWaveTable</class>
   <extends>QTableWidget</extends>
   <header>caWaveTable</header>
  </customwidget>
 </customwidgets>
 <resources/>
 <connections/>
</ui>
"""
    )
    return "\n".join(widgets)


def main():
    args = parse_args()
    input_path = pathlib.Path(args.input)
    output_path = pathlib.Path(args.output)
    macros, records = parse_substitutions(input_path)

    pv_prefix = args.pv_prefix or macros.get("P", "")
    title = args.title or f"{input_path.stem} cpp_logic PVs"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_ui(title, records, pv_prefix), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
