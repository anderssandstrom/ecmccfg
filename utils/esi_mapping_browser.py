#!/usr/bin/env python3
"""
Browse available PDO mappings in EtherCAT ESI XML files.

This tool is intentionally small and dependency-free (stdlib only).
It supports:
1) GUI mode (Tkinter): browse slaves and their PDO mappings.
2) CLI mode (--no-gui): print mappings to stdout.

For slaves that define <AlternativeSmMapping>, those mappings are shown.
For simpler slaves without alternatives (for example many EL1xxx terminals),
an implicit default mapping is built from RxPdo/TxPdo entries with @Sm.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path


ENTRY_TOKEN_MAP = {
    "Status": "Stat",
    "Control": "Ctrl",
    "Feedback": "Fb",
    "Digital Input": "BI",
    "digital Input": "BI",
    "Digital Output": "BO",
    "digital Output": "BO",
    "Outputs Output": "BO",
    "Inputs": "Inp",
    "Input": "Inp",
    "Outputs": "Outp",
    "Output": "Outp",
    "Event": "Evt",
    "Cycle": "Cycl",
    "Counter": "Cntr",
    "Buffer": "Buff",
    "Short": "Shrt",
    "Circuit": "Circ",
    "Overflow": "Ovrflw",
    "Underflow": "Undrflw",
    "Order": "Ordr",
    "State": "State",
    "Manual": "Man",
    "Extern": "Ext",
    "Latch": "Ltch",
    "Error": "Err",
    "Value": "Val",
    "Toggle": "Tgl",
    "Timestamp": "Tme",
    "Time": "Tme",
    "Warning": "Wrn",
    "Moving": "Mov",
    "Positive": "Pos",
    "Negative": "Neg",
    "Torque": "Trq",
    "Reduced": "Red",
    "Reduce": "Red",
    "Done": "Dne",
    "Of": "",
    "Ready": "Rdy",
    "Enable": "Ena",
    "Extrapolation": "Ext",
    "Stall": "Stl",
    "InfoData": "InfDta",
    "Edge": "Edg",
    "Reset": "Rst",
    "Position": "Pos",
    "Setpoint": "Set",
    "Actual Value": "Act",
    "Actual": "Act",
    "Valid": "Vld",
    "Inp": "BI",
    "Busy": "Bsy",
    "Channel": "Ch",
    "Overtemperature": "OvrTmp",
    "Overcurrent": "OvrCurr",
    "Open": "Opn",
    "Load": "Ld",
    "Force": "Frce",
    "Operation": "Op",
    "Statword": "Stat",
    "Ctrlword": "Ctrl",
    "Target": "Trg",
    "Following": "Fllw",
    "Velocity": "Vel",
    "Commutation": "Com",
    "Angle": "Angl",
}

PDO_OUT_MAP = {
    "DIG": "BO",
    "ENC": "ENC",
    "MTI": "BI",
    "MTO": "BO",
    "POS": "POS",
    "STM": "DRV",
    "Latch": "LTCH",
    "Channel": "BO",
}

PDO_IN_MAP = {
    "DIG": "BI",
    "ENC": "ENC",
    "MTI": "BI",
    "MTO": "BO",
    "POS": "POS",
    "STM": "DRV",
    "Latch": "LTCH",
    "Channel": "BI",
}

DEV_NEEDS_INDEX = {"ENC", "MTI", "MTO", "POS", "STM", "DRV"}
SINGLE_CH_NEEDS_INDEX = {"AI", "AO", "BI", "BO"}
REMOVE_LAST_MAP = {"Outp-Outp": "", "Inp-Inp": ""}


def _text(node: ET.Element | None) -> str:
    return (node.text or "").strip() if node is not None else ""


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_hexish(value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    if value.lower().startswith("#x"):
        try:
            return int(value[2:], 16)
        except ValueError:
            return None
    if value.lower().startswith("0x"):
        try:
            return int(value, 16)
        except ValueError:
            return None
    try:
        return int(value)
    except ValueError:
        return None


def _norm_hex(value: str | None) -> str:
    parsed = _parse_hexish(value)
    if parsed is None:
        return ""
    return f"0x{parsed:x}"


def _norm_subindex(value: str | None) -> str:
    norm = _norm_hex(value)
    if norm:
        return norm
    return "0x0"


def _extract_subidx_from_text(value: str) -> str:
    match = re.search(r"(\d+)$", value.strip())
    if not match:
        return ""
    return f"0x{int(match.group(1)):x}"


def _is_generic_subindex_name(name: str) -> bool:
    return bool(re.fullmatch(r"SubIndex\s+\d+", name.strip(), re.IGNORECASE))


def _normalize_pattern_items(pattern_expr: str | None) -> list[str]:
    if pattern_expr is None:
        return ["*"]

    raw = [part.strip() for part in pattern_expr.split(",")]
    patterns = [part for part in raw if part]
    if not patterns:
        return ["*"]

    normalized: list[str] = []
    for pattern in patterns:
        pat = pattern
        if pat.lower().startswith("#x"):
            pat = "0x" + pat[2:]

        has_glob = any(ch in pat for ch in "*?[")
        if not has_glob:
            parsed = _parse_hexish(pat)
            if parsed is not None and (pat.lower().startswith("0x") or pat.isdigit()):
                # Canonicalize fixed revision patterns, e.g. #x00120000 -> 0x120000.
                pat = f"0x{parsed:x}"
            elif "x" in pat or "X" in pat:
                # Support Beckhoff-style family patterns like "EL1xxx".
                pat = "".join("?" if ch in "xX" else ch for ch in pat)

        normalized.append(pat)

    return normalized or ["*"]


def _match_pattern(value: str, pattern_expr: str | None) -> bool:
    value_l = value.lower()
    for pat in _normalize_pattern_items(pattern_expr):
        if fnmatch.fnmatch(value_l, pat.lower()):
            return True
    return False


@dataclass
class SmPdoGroup:
    sm_no: str
    pdos: list[str] = field(default_factory=list)


@dataclass
class PdoMapping:
    name: str
    is_default: bool
    source: str
    sm_groups: list[SmPdoGroup] = field(default_factory=list)


@dataclass
class SdoField:
    index: str
    subindex: str
    name: str
    data_type: str
    bit_size: int | None
    object_name: str = ""


@dataclass
class PdoEntry:
    index: str
    subindex: str
    bitlen: int
    data_type: str
    raw_name: str
    resolved_name: str


@dataclass
class PdoInfo:
    direction: str
    sm: str
    index: str
    name: str
    entries: list[PdoEntry] = field(default_factory=list)


@dataclass
class GeneratedEntry:
    direction: str
    sm_no: str
    pdo_index: str
    entry_index: str
    entry_subindex: str
    dt: str
    source_name: str
    desc: str
    packed: bool = False
    bit_comment: str = ""


@dataclass
class PdoChoice:
    pdo: PdoInfo
    sm_no: str
    is_default: bool


@dataclass
class DcModeInfo:
    name: str
    assign_activate: str
    cycle_time_sync0: str = ""
    shift_time_sync0: str = ""
    cycle_time_sync1: str = ""
    shift_time_sync1: str = ""


@dataclass
class SlaveInfo:
    type_name: str
    display_name: str
    product_code: str
    revision: str
    mappings: list[PdoMapping] = field(default_factory=list)
    pdo_by_index: dict[str, PdoInfo] = field(default_factory=dict)
    sdo_fields: dict[tuple[str, str], SdoField] = field(default_factory=dict)
    dc_modes: list[DcModeInfo] = field(default_factory=list)

    @property
    def short_label(self) -> str:
        shown_type = self.type_name or "UnknownType"
        shown_rev = self.revision or "unknown-rev"
        shown_name = self.display_name or "Unnamed slave"
        return f"{shown_type} {shown_rev} - {shown_name}"


def _extract_alternative_mappings(device: ET.Element) -> list[PdoMapping]:
    mappings: list[PdoMapping] = []
    for idx, alt in enumerate(device.findall(".//AlternativeSmMapping"), start=1):
        name = _text(alt.find("Name")) or f"Alternative mapping {idx}"
        is_default = (alt.get("Default") or "").strip() == "1"
        groups: list[SmPdoGroup] = []
        for sm in alt.findall("Sm"):
            sm_no = (sm.get("No") or "").strip()
            pdos = [_norm_hex(_text(pdo)) for pdo in sm.findall("Pdo")]
            pdos = [pdo for pdo in pdos if pdo]
            groups.append(SmPdoGroup(sm_no=sm_no, pdos=pdos))
        mappings.append(
            PdoMapping(
                name=name,
                is_default=is_default,
                source="AlternativeSmMapping",
                sm_groups=groups,
            )
        )
    return mappings


def _extract_implicit_mapping(device: ET.Element) -> PdoMapping | None:
    sm_map: OrderedDict[str, list[str]] = OrderedDict()

    for pdo in list(device.findall("RxPdo")) + list(device.findall("TxPdo")):
        sm_no = (pdo.get("Sm") or "").strip()
        if not sm_no:
            continue
        index_hex = _norm_hex(_text(pdo.find("Index")))
        if not index_hex:
            continue
        if sm_no not in sm_map:
            sm_map[sm_no] = []
        if index_hex not in sm_map[sm_no]:
            sm_map[sm_no].append(index_hex)

    if not sm_map:
        return None

    groups: list[SmPdoGroup] = []
    for sm_no, pdos in sm_map.items():
        pdos_sorted = sorted(pdos, key=lambda idx: (_parse_hexish(idx) is None, _parse_hexish(idx) or 0, idx))
        groups.append(SmPdoGroup(sm_no=sm_no, pdos=pdos_sorted))
    return PdoMapping(
        name="Implicit default mapping",
        is_default=True,
        source="RxPdo/TxPdo @Sm",
        sm_groups=groups,
    )


def _extract_sdo_lookup(device: ET.Element) -> dict[tuple[str, str], SdoField]:
    data_types: dict[str, dict[str, SdoField]] = {}

    for dt in device.findall("./Profile/Dictionary/DataTypes/DataType"):
        dt_name = _text(dt.find("Name"))
        if not dt_name:
            continue

        sub_lookup: dict[str, SdoField] = {}
        for sub in dt.findall("SubItem"):
            subidx = _norm_subindex(_text(sub.find("SubIdx")))
            sub_lookup[subidx] = SdoField(
                index="",
                subindex=subidx,
                name=_text(sub.find("Name")),
                data_type=_text(sub.find("Type")),
                bit_size=_parse_int(_text(sub.find("BitSize"))),
            )
        data_types[dt_name] = sub_lookup

    lookup: dict[tuple[str, str], SdoField] = {}
    for obj in device.findall("./Profile/Dictionary/Objects/Object"):
        obj_index = _norm_hex(_text(obj.find("Index")))
        if not obj_index:
            continue

        obj_name = _text(obj.find("Name"))
        obj_type = _text(obj.find("Type"))
        obj_bit_size = _parse_int(_text(obj.find("BitSize")))

        dt_fields = data_types.get(obj_type, {})
        for subidx, dt_field in dt_fields.items():
            field_name = dt_field.name or obj_name
            lookup[(obj_index, subidx)] = SdoField(
                index=obj_index,
                subindex=subidx,
                name=field_name,
                data_type=dt_field.data_type,
                bit_size=dt_field.bit_size,
                object_name=obj_name,
            )

        # Fallback: some files only provide SubItem names under Object/Info.
        for sub in obj.findall("./Info/SubItem"):
            sub_name = _text(sub.find("Name"))
            if not sub_name:
                continue
            subidx = _extract_subidx_from_text(sub_name)
            if not subidx:
                continue
            key = (obj_index, subidx)
            if key not in lookup:
                lookup[key] = SdoField(
                    index=obj_index,
                    subindex=subidx,
                    name=sub_name,
                    data_type="",
                    bit_size=obj_bit_size,
                    object_name=obj_name,
                )

    return lookup


def _resolve_entry_name(entry_name: str, sdo_field: SdoField | None) -> str:
    if sdo_field is not None:
        if sdo_field.name and not _is_generic_subindex_name(sdo_field.name):
            return sdo_field.name
    return entry_name


def _parse_pdo_definitions(
    device: ET.Element,
    sdo_lookup: dict[tuple[str, str], SdoField],
) -> dict[str, PdoInfo]:
    pdo_by_index: dict[str, PdoInfo] = {}

    for tag, direction in (("TxPdo", "tx"), ("RxPdo", "rx")):
        for pdo in device.findall(tag):
            pdo_index = _norm_hex(_text(pdo.find("Index")))
            if not pdo_index:
                continue

            sm = (pdo.get("Sm") or "").strip()
            pdo_name = _text(pdo.find("Name"))
            entries: list[PdoEntry] = []
            for entry in pdo.findall("Entry"):
                entry_index = _norm_hex(_text(entry.find("Index")))
                if not entry_index:
                    continue
                entry_subindex = _norm_subindex(_text(entry.find("SubIndex")))
                entry_bitlen = _parse_int(_text(entry.find("BitLen"))) or 0
                entry_dtype = _text(entry.find("DataType"))
                entry_name = _text(entry.find("Name"))

                sdo_field = sdo_lookup.get((entry_index, entry_subindex))
                resolved_name = _resolve_entry_name(entry_name, sdo_field)

                entries.append(
                    PdoEntry(
                        index=entry_index,
                        subindex=entry_subindex,
                        bitlen=entry_bitlen,
                        data_type=entry_dtype,
                        raw_name=entry_name,
                        resolved_name=resolved_name,
                    )
                )

            if pdo_index not in pdo_by_index:
                pdo_by_index[pdo_index] = PdoInfo(
                    direction=direction,
                    sm=sm,
                    index=pdo_index,
                    name=pdo_name,
                    entries=entries,
                )
            elif not pdo_by_index[pdo_index].entries and entries:
                pdo_by_index[pdo_index].entries = entries

    return pdo_by_index


def _extract_dc_modes(device: ET.Element) -> list[DcModeInfo]:
    modes: list[DcModeInfo] = []
    for dc in device.findall("Dc"):
        for opmode in dc.findall("OpMode"):
            modes.append(
                DcModeInfo(
                    name=_text(opmode.find("Name")),
                    assign_activate=_norm_hex(_text(opmode.find("AssignActivate"))),
                    cycle_time_sync0=_text(opmode.find("CycleTimeSync0")),
                    shift_time_sync0=_text(opmode.find("ShiftTimeSync0")),
                    cycle_time_sync1=_text(opmode.find("CycleTimeSync1")),
                    shift_time_sync1=_text(opmode.find("ShiftTimeSync1")),
                )
            )
    return modes


def _device_names_for_match(device: ET.Element, type_name: str, display_name: str) -> list[str]:
    names = [type_name, display_name]
    for n in device.findall("Name"):
        n_text = _text(n)
        if n_text:
            names.append(n_text)
    return [n for n in names if n]


def parse_esi_file(
    file_path: Path, name_pattern: str = "*", rev_pattern: str = "*"
) -> list[SlaveInfo]:
    root = ET.parse(file_path).getroot()
    devices = root.findall(".//Descriptions/Devices/Device")

    slaves: list[SlaveInfo] = []
    for device in devices:
        type_elem = device.find("Type")
        type_name = _text(type_elem)
        revision = _norm_hex(type_elem.get("RevisionNo") if type_elem is not None else None)
        product_code = _norm_hex(type_elem.get("ProductCode") if type_elem is not None else None)

        display_name = ""
        names = device.findall("Name")
        for n in names:
            if (n.get("LcId") or "").strip() == "1033":
                display_name = _text(n)
                break
        if not display_name and names:
            display_name = _text(names[0])

        match_names = _device_names_for_match(device, type_name, display_name)
        name_ok = any(_match_pattern(n, name_pattern) for n in match_names)
        rev_ok = _match_pattern(revision or "", rev_pattern)
        if not (name_ok and rev_ok):
            continue

        mappings = _extract_alternative_mappings(device)
        if not mappings:
            implicit = _extract_implicit_mapping(device)
            if implicit is not None:
                mappings = [implicit]

        sdo_lookup = _extract_sdo_lookup(device)
        pdo_by_index = _parse_pdo_definitions(device, sdo_lookup)
        dc_modes = _extract_dc_modes(device)

        slaves.append(
            SlaveInfo(
                type_name=type_name,
                display_name=display_name,
                product_code=product_code,
                revision=revision,
                mappings=mappings,
                pdo_by_index=pdo_by_index,
                sdo_fields=sdo_lookup,
                dc_modes=dc_modes,
            )
        )

    slaves.sort(key=lambda d: (d.type_name, _parse_hexish(d.revision) or 0, d.display_name))
    return slaves


def print_mappings(slaves: list[SlaveInfo]) -> None:
    if not slaves:
        print("No slaves matched.")
        return

    for idx, slave in enumerate(slaves, start=1):
        print(f"{idx:3d}. {slave.short_label}")
        if not slave.mappings:
            print("     (no PDO mappings found)")
            continue
        for midx, mapping in enumerate(slave.mappings, start=1):
            default_str = " default" if mapping.is_default else ""
            print(f"     {midx:2d}. {mapping.name} [{mapping.source}{default_str}]")
            if not mapping.sm_groups:
                print("          (no SM/PDO entries)")
                continue
            for group in mapping.sm_groups:
                pdo_str = ", ".join(group.pdos) if group.pdos else "(none)"
                print(f"          SM{group.sm_no}: {pdo_str}")
            optional_count = len(optional_pdos_for_mapping(slave, mapping))
            if optional_count > 0:
                print(f"          optional selectable PDOs: {optional_count}")


def _entry_to_ecmc_dt(entry: PdoEntry) -> str:
    dt = entry.data_type.upper()
    mapping = {
        "BOOL": "B1",
        "USINT": "U8",
        "UINT": "U16",
        "UDINT": "U32",
        "ULINT": "U64",
        "SINT": "S8",
        "INT": "S16",
        "DINT": "S32",
        "LINT": "S64",
    }
    if dt in mapping:
        if dt == "BOOL" and entry.bitlen > 1:
            return f"B{entry.bitlen}"
        return mapping[dt]

    if entry.bitlen == 8:
        return "U8"
    if entry.bitlen == 16:
        return "U16"
    if entry.bitlen == 32:
        return "U32"
    if entry.bitlen == 64:
        return "U64"
    if entry.bitlen > 0:
        return f"B{entry.bitlen}"
    return "U8"


def _snake(text: str) -> str:
    text = text.strip().replace("%", "pct")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        return "var"
    if text[0].isdigit():
        text = "_" + text
    return text


def _replace_tokens(text: str, replacements: dict[str, str]) -> str:
    result = text
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def _chars_after_space_to_upper(text: str) -> str:
    result = []
    prev = ""
    for ch in text:
        if prev == " ":
            ch = ch.upper()
        result.append(ch)
        prev = ch
    return "".join(result)


def _if_digit_last_make_it_2wide(text: str) -> str:
    i = len(text) - 1
    while i >= 0 and text[i].isdigit():
        i -= 1
    if i < len(text) - 1:
        prefix = text[: i + 1]
        number = text[i + 1 :]
        return f"{prefix}{int(number):02d}"
    return text


def _remove_trailing_hyphen(text: str) -> str:
    return text[:-1] if text.endswith("-") else text


def _is_single_channel_slave(slave: SlaveInfo | None) -> bool:
    if slave is None:
        return False
    text = f"{slave.display_name} {slave.type_name}".lower()
    return bool(re.search(r"\b1\s*ch\.?\b", text))


def _pdo_type_and_prefix(pdo: PdoInfo, slave: SlaveInfo | None = None) -> tuple[str, str]:
    words = pdo.name.split()
    if not words:
        return ("Dev", "Dev")

    raw = words[0]
    mapped = _replace_tokens(raw, PDO_IN_MAP if pdo.direction == "rx" else PDO_OUT_MAP)

    channel_no: int | None = None
    for idx in range(len(words) - 1):
        if words[idx].lower() == "channel" and words[idx + 1].isdigit():
            channel_no = int(words[idx + 1])
            break

    if channel_no is None and raw.upper() in DEV_NEEDS_INDEX:
        channel_no = 1

    # Some single-channel terminals (for example EL3001) have PDO names
    # without explicit "Channel 1" text; force *_01 style prefixes.
    if channel_no is None and mapped in SINGLE_CH_NEEDS_INDEX and _is_single_channel_slave(slave):
        channel_no = 1

    prefix = mapped if channel_no is None else f"{mapped}{channel_no:02d}"
    return (mapped, prefix)


def _entry_record_name(pdo: PdoInfo, entry_name: str, slave: SlaveInfo | None = None) -> str:
    dev, prefix = _pdo_type_and_prefix(pdo, slave=slave)
    text = _chars_after_space_to_upper(entry_name)
    text = _replace_tokens(text, ENTRY_TOKEN_MAP)
    text = text.replace("__", "-")
    text = text.replace(" ", "")
    text = text.replace(dev, "")
    text = f"{prefix}-{text}"
    text = text.replace("--", "-")
    text = _if_digit_last_make_it_2wide(text)
    text = _remove_trailing_hyphen(text)
    text = _replace_tokens(text, REMOVE_LAST_MAP)
    return text


def _record_to_source_name(record_name: str) -> str:
    # Keep underscores in hardware snippet symbols for ecmc PLC compatibility.
    return record_name.replace("-", "_")


def _channel_from_pdo_name(pdo_name: str) -> int | None:
    match = re.search(r"(?:channel|ch\.?)[^0-9]*([0-9]+)", pdo_name, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _build_hwtype(slave: SlaveInfo, mapping_index: int, mapping_count: int) -> str:
    del mapping_index
    del mapping_count
    base = slave.type_name or "unknown_hw"
    return _snake(base)


def _resolve_hwtype(
    slave: SlaveInfo, mapping_index: int, mapping_count: int, hwtype_override: str | None = None
) -> str:
    if hwtype_override and hwtype_override.strip():
        return _snake(hwtype_override)
    return _build_hwtype(slave, mapping_index, mapping_count)


def _unique_symbol(candidate: str, used: dict[str, int]) -> str:
    count = used.get(candidate, 0) + 1
    used[candidate] = count
    if count == 1:
        return candidate
    return f"{candidate}_{count:02d}"


def _symbol_with_direction(base_name: str, direction: str, used: dict[str, int]) -> str:
    del direction
    return _unique_symbol(_snake(base_name), used)


def _entry_symbol(pdo: PdoInfo, entry: PdoEntry, used: dict[str, int], slave: SlaveInfo | None = None) -> str:
    base_name = entry.resolved_name or entry.raw_name or f"{entry.index}_{entry.subindex}"
    record_name = _entry_record_name(pdo, base_name, slave=slave)
    if record_name:
        return _unique_symbol(_record_to_source_name(record_name), used)
    return _symbol_with_direction(base_name, pdo.direction, used)


def _packed_root_name(pdo: PdoInfo) -> str:
    name_l = pdo.name.lower()
    if "control" in name_l:
        return "Ctrl"
    if "status" in name_l:
        return "Stat"
    if "input" in name_l:
        return "Stat"
    if "output" in name_l:
        return "Ctrl"
    return "Stat" if pdo.direction == "tx" else "Ctrl"


def _packed_symbol_name(
    pdo: PdoInfo,
    chunk_idx: int,
    used: dict[str, int],
    slave: SlaveInfo | None = None,
) -> str:
    root = _packed_root_name(pdo)
    _dev, prefix = _pdo_type_and_prefix(pdo, slave=slave)
    record_name = f"{prefix}-{root}"
    if chunk_idx > 1:
        record_name = f"{record_name}{chunk_idx:02d}"
    return _unique_symbol(_record_to_source_name(record_name), used)


def _is_packable_bit_entry(entry: PdoEntry) -> bool:
    if entry.bitlen <= 0:
        return False
    if entry.index == "0x0":
        return True
    return entry.bitlen < 8 and _entry_to_ecmc_dt(entry).startswith("B")


def _bit_range_label(bit_offset: int, bit_width: int) -> str:
    if bit_width <= 1:
        return f"B{bit_offset}"
    return f"B{bit_offset}..B{bit_offset + bit_width - 1}"


def _build_packed_bit_comment(chunk: list[PdoEntry]) -> str:
    # Keep placeholders ("gap") so merged bit layout is explicit and reviewable.
    segments: list[tuple[int, int, str]] = []
    bit_offset = 0
    for entry in chunk:
        bit_width = entry.bitlen if entry.bitlen > 0 else 0
        if bit_width <= 0:
            continue

        if entry.index == "0x0":
            label = "gap"
        else:
            label = (entry.resolved_name or entry.raw_name or entry.index).strip()
            label = re.sub(r"\s+", " ", label) if label else ""
            if not label:
                label = "gap"

        if segments:
            prev_offset, prev_width, prev_label = segments[-1]
            if prev_label == label and (prev_offset + prev_width) == bit_offset:
                segments[-1] = (prev_offset, prev_width + bit_width, prev_label)
            else:
                segments.append((bit_offset, bit_width, label))
        else:
            segments.append((bit_offset, bit_width, label))
        bit_offset += bit_width

    return ", ".join(f"{_bit_range_label(offset, width)}={label}" for offset, width, label in segments)


def _mapping_pdo_set(mapping: PdoMapping) -> set[str]:
    selected: set[str] = set()
    for group in mapping.sm_groups:
        for pdo_index in group.pdos:
            selected.add(pdo_index)
    return selected


def optional_pdos_for_mapping(slave: SlaveInfo, mapping: PdoMapping) -> list[PdoInfo]:
    selected = _mapping_pdo_set(mapping)
    optional = [pdo for idx, pdo in slave.pdo_by_index.items() if idx not in selected]
    optional.sort(key=lambda p: (_parse_hexish(p.index) is None, _parse_hexish(p.index) or 0, p.direction, p.name))
    return optional


def _pdo_choice_sort_key(choice: PdoChoice) -> tuple[int, int, str, str]:
    idx_num = _parse_hexish(choice.pdo.index)
    return (
        1 if idx_num is None else 0,
        idx_num if idx_num is not None else 0,
        0 if choice.is_default else 1,
        choice.pdo.name,
    )


def _is_non_decreasing_pdo_order(indexes: list[str]) -> bool:
    parsed: list[int] = []
    for idx in indexes:
        idx_num = _parse_hexish(idx)
        if idx_num is None:
            return False
        parsed.append(idx_num)
    return all(parsed[i] <= parsed[i + 1] for i in range(len(parsed) - 1))


def pdo_choices_for_mapping(slave: SlaveInfo, mapping: PdoMapping) -> list[PdoChoice]:
    default_choices: list[PdoChoice] = []
    seen: set[str] = set()

    for group in mapping.sm_groups:
        sm_no = group.sm_no
        for pdo_index in group.pdos:
            if pdo_index in seen:
                continue
            pdo = slave.pdo_by_index.get(pdo_index)
            if pdo is None:
                continue
            default_choices.append(PdoChoice(pdo=pdo, sm_no=sm_no, is_default=True))
            seen.add(pdo_index)

    optional_choices: list[PdoChoice] = []
    optional = optional_pdos_for_mapping(slave, mapping)
    for pdo in optional:
        if pdo.index in seen:
            continue
        sm_no = pdo.sm if pdo.sm else _default_sm_for_direction(slave, mapping, pdo.direction)
        optional_choices.append(PdoChoice(pdo=pdo, sm_no=sm_no, is_default=False))
        seen.add(pdo.index)

    # Keep explicit ESI ordering if defaults are intentionally non-monotonic.
    default_indexes = [choice.pdo.index for choice in default_choices]
    if default_indexes and not _is_non_decreasing_pdo_order(default_indexes):
        return default_choices + sorted(optional_choices, key=_pdo_choice_sort_key)

    return sorted(default_choices + optional_choices, key=_pdo_choice_sort_key)


def _default_sm_for_direction(slave: SlaveInfo, mapping: PdoMapping, direction: str) -> str:
    for group in mapping.sm_groups:
        for pdo_index in group.pdos:
            pdo = slave.pdo_by_index.get(pdo_index)
            if pdo is not None and pdo.direction == direction:
                return group.sm_no
    return "2" if direction == "rx" else "3"


def _normalize_dc_time(value: str) -> str:
    if not value:
        return ""
    parsed = _parse_hexish(value)
    if parsed is None:
        return value
    return str(parsed)


def _select_dc_mode(slave: SlaveInfo) -> DcModeInfo | None:
    if not slave.dc_modes:
        return None

    for mode in slave.dc_modes:
        if mode.assign_activate and mode.name.lower() == "dc":
            return mode
    for mode in slave.dc_modes:
        if mode.assign_activate:
            return mode
    return None


def generate_hw_snippet(
    slave: SlaveInfo,
    mapping: PdoMapping,
    mapping_index: int,
    mapping_count: int,
    optional_pdo_indexes: list[str] | None = None,
    selected_pdo_indexes: list[str] | None = None,
    hwtype_override: str | None = None,
    generated_entries: list[GeneratedEntry] | None = None,
    include_dc: bool = True,
    esi_file: str | None = None,
) -> str:
    rows: list[str] = []
    rows.append(f"#-  ecmc hardware config for: {slave.display_name}")
    rows.append(f"#- {mapping.name}")
    if esi_file:
        rows.append(f"#- source ESI file: {esi_file}")
    rows.append(
        f"#- selected slave: type={slave.type_name or 'unknown'}, product={slave.product_code or 'unknown'}, revision={slave.revision or 'unknown'}"
    )
    rows.append(f"#- selected mapping id: M{mapping_index:02d} of {mapping_count}")
    rows.append("")

    hwtype = _resolve_hwtype(slave, mapping_index, mapping_count, hwtype_override)
    rows.append(f"epicsEnvSet(\"ECMC_EC_HWTYPE\"             \"{hwtype}\")")
    rows.append("epicsEnvSet(\"ECMC_EC_VENDOR_ID\"          \"0x2\")")
    rows.append(f"epicsEnvSet(\"ECMC_EC_PRODUCT_ID\"         \"{slave.product_code}\")")
    rows.append(f"epicsEnvSet(\"ECMC_EC_REVISION\"           \"{slave.revision}\")")
    rows.append("epicsEnvSet(\"ECMC_HW_PANEL\"              \"$(ECMC_EC_HWTYPE)\")")
    rows.append("")

    mapping_pdos = _mapping_pdo_set(mapping)
    mapping_sm_by_pdo: dict[str, str] = {}
    for group in mapping.sm_groups:
        for pdo_index in group.pdos:
            if pdo_index not in mapping_sm_by_pdo:
                mapping_sm_by_pdo[pdo_index] = group.sm_no

    used_symbols: dict[str, int] = {}
    already_added: set[str] = set()

    def _emit_pdo(pdo_index: str, sm_no: str, is_optional: bool) -> None:
        pdo = slave.pdo_by_index.get(pdo_index)
        if pdo is None:
            if is_optional:
                rows.append(f"#- WARNING: selected optional PDO {pdo_index} not found")
            else:
                rows.append(f"#- WARNING: mapping references missing PDO {pdo_index} on SM{sm_no}")
            return

        direction = "1" if sm_no in ("0", "2") else "2"
        if is_optional:
            rows.append(f"#- OPTIONAL {pdo.direction.upper()} PDO {pdo.index}: {pdo.name} (SM{sm_no})")
        else:
            rows.append(f"#- {pdo.direction.upper()} PDO {pdo.index}: {pdo.name}")

        def _emit_entry_line(
            entry_index: str,
            entry_subindex: str,
            dt: str,
            symbol: str,
            desc: str,
            packed: bool = False,
            bit_comment: str = "",
        ) -> None:
            rows.append(
                "ecmcConfigOrDie \"Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},"
                "${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},"
                f"{direction},{sm_no},{pdo.index},{entry_index},{entry_subindex},{dt},{symbol})\""
            )
            if generated_entries is not None:
                generated_entries.append(
                    GeneratedEntry(
                        direction=direction,
                        sm_no=sm_no,
                        pdo_index=pdo.index,
                        entry_index=entry_index,
                        entry_subindex=entry_subindex,
                        dt=dt,
                        source_name=symbol,
                        desc=desc,
                        packed=packed,
                        bit_comment=bit_comment,
                    )
                )

        entries = pdo.entries
        entry_i = 0
        packed_group_idx = 0
        while entry_i < len(entries):
            entry = entries[entry_i]
            if entry.index == "0x0":
                entry_i += 1
                continue

            # Merge contiguous bit-level fields (including padding gaps) within the PDO run.
            if _is_packable_bit_entry(entry):
                run_entries: list[PdoEntry] = []
                run_j = entry_i
                while run_j < len(entries):
                    curr = entries[run_j]
                    if curr.bitlen <= 0:
                        run_j += 1
                        continue
                    if curr.index == "0x0":
                        run_entries.append(curr)
                        run_j += 1
                        continue
                    if not _is_packable_bit_entry(curr):
                        break
                    run_entries.append(curr)
                    run_j += 1

                run_non_padding = [it for it in run_entries if it.index != "0x0"]
                if len(run_non_padding) >= 2:
                    cursor = 0
                    while cursor < len(run_entries):
                        bits = 0
                        chunk: list[PdoEntry] = []
                        while cursor < len(run_entries):
                            curr = run_entries[cursor]
                            if curr.bitlen <= 0:
                                cursor += 1
                                continue
                            if bits > 0 and (bits + curr.bitlen) > 16:
                                break
                            chunk.append(curr)
                            bits += curr.bitlen
                            cursor += 1
                            if bits >= 16:
                                break

                        if not chunk:
                            continue

                        chunk_non_padding = [it for it in chunk if it.index != "0x0"]
                        if len(chunk_non_padding) < 2:
                            for single in chunk_non_padding:
                                symbol = _entry_symbol(pdo, single, used_symbols, slave=slave)
                                dt = _entry_to_ecmc_dt(single)
                                desc = single.resolved_name or single.raw_name or single.index
                                _emit_entry_line(single.index, single.subindex, dt, symbol, desc, packed=False)
                            continue

                        packed_group_idx += 1
                        packed_dt = "U8" if bits <= 8 else "U16"
                        packed_entry = chunk_non_padding[0]
                        packed_symbol = _packed_symbol_name(pdo, packed_group_idx, used_symbols, slave=slave)
                        bit_comment = _build_packed_bit_comment(chunk)
                        _emit_entry_line(
                            packed_entry.index,
                            packed_entry.subindex,
                            packed_dt,
                            packed_symbol,
                            f"{pdo.name} packed bits",
                            packed=True,
                            bit_comment=bit_comment,
                        )
                        rows.append(
                            f"#- NOTE: packed {len(chunk_non_padding)} bit entries ({bits} bits) into {packed_dt}"
                        )
                        if bit_comment:
                            rows.append(f"#-      bits: {bit_comment}")

                    entry_i = run_j
                    continue

            symbol = _entry_symbol(pdo, entry, used_symbols, slave=slave)
            dt = _entry_to_ecmc_dt(entry)
            desc = entry.resolved_name or entry.raw_name or entry.index
            _emit_entry_line(entry.index, entry.subindex, dt, symbol, desc, packed=False)
            entry_i += 1

        rows.append("")
        already_added.add(pdo_index)

    if selected_pdo_indexes is None:
        include_mapping_pdos = set(mapping_pdos)
        include_optional_pdos = optional_pdo_indexes or []

        for group in mapping.sm_groups:
            sm_no = group.sm_no
            for pdo_index in group.pdos:
                if pdo_index not in include_mapping_pdos:
                    continue
                _emit_pdo(pdo_index, sm_no, is_optional=False)

        if include_optional_pdos:
            rows.append("#- Optional PDOs selected by user")
            for pdo_index in include_optional_pdos:
                if pdo_index in already_added:
                    continue
                pdo = slave.pdo_by_index.get(pdo_index)
                if pdo is None:
                    _emit_pdo(pdo_index, "", is_optional=True)
                    continue
                sm_no = pdo.sm if pdo.sm else _default_sm_for_direction(slave, mapping, pdo.direction)
                _emit_pdo(pdo_index, sm_no, is_optional=True)
    else:
        ordered_selected: list[str] = []
        seen_selected: set[str] = set()
        for idx in selected_pdo_indexes:
            if idx and idx not in seen_selected:
                ordered_selected.append(idx)
                seen_selected.add(idx)

        has_optional_header = False
        for pdo_index in ordered_selected:
            if pdo_index in already_added:
                continue
            if pdo_index in mapping_pdos:
                pdo = slave.pdo_by_index.get(pdo_index)
                sm_no = mapping_sm_by_pdo.get(pdo_index, "")
                if not sm_no and pdo is not None:
                    sm_no = pdo.sm if pdo.sm else _default_sm_for_direction(slave, mapping, pdo.direction)
                _emit_pdo(pdo_index, sm_no, is_optional=False)
            else:
                if not has_optional_header:
                    rows.append("#- Optional PDOs selected by user")
                    has_optional_header = True
                pdo = slave.pdo_by_index.get(pdo_index)
                if pdo is None:
                    _emit_pdo(pdo_index, "", is_optional=True)
                    continue
                sm_no = pdo.sm if pdo.sm else _default_sm_for_direction(slave, mapping, pdo.direction)
                _emit_pdo(pdo_index, sm_no, is_optional=True)

    dc_mode = _select_dc_mode(slave)
    if include_dc and dc_mode and dc_mode.assign_activate:
        sync0_cycle = _normalize_dc_time(dc_mode.cycle_time_sync0)
        sync0_shift = _normalize_dc_time(dc_mode.shift_time_sync0)
        sync1_cycle = _normalize_dc_time(dc_mode.cycle_time_sync1)
        sync1_shift = _normalize_dc_time(dc_mode.shift_time_sync1)

        # Use Sync0 values directly from ESI; fallback to 0 if missing.
        if not sync0_cycle:
            sync0_cycle = "0"
        if not sync0_shift:
            sync0_shift = "0"
        if not sync1_cycle:
            sync1_cycle = "0"
        if not sync1_shift:
            sync1_shift = "0"

        rows.append(f"#- DC mode: {dc_mode.name or 'unnamed'}")
        rows.append("ecmcEpicsEnvSetCalc(\"ECMC_TEMP_PERIOD_NANO_SECS\",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)")

        rows.append(f'# ecmcEpicsEnvSetCalc("ECMC_SYNC_1","${{ECMC_TEMP_PERIOD_NANO_SECS}}-{sync0_cycle}")')
        rows.append("ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)")
        rows.append(
            "${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "
            f"\"ASSIGN_ACTIVATE={dc_mode.assign_activate},SYNC_0_CYCLE={sync0_cycle},"
            f"SYNC_0_SHIFT={sync0_shift},SYNC_1_CYCLE=$(ECMC_SYNC_1={sync1_cycle})\""
        )
        if sync1_shift and sync1_shift != "0":
            rows.append(f"#- NOTE: Sync1 shift from ESI ({sync1_shift}) is not applied by applySlaveDCconfig.cmd")
        rows.append("epicsEnvUnset(ECMC_TEMP_PERIOD_NANO_SECS)")

    return "\n".join(rows).rstrip() + "\n"


def _esc_subst(value: str) -> str:
    return value.replace('"', "'")


def _bit_comment_lines(bit_comment: str) -> list[str]:
    if not bit_comment.strip():
        return []
    return [part.strip() for part in bit_comment.split(",") if part.strip()]


def _entry_to_subst_group(entry: GeneratedEntry) -> str:
    if entry.packed:
        return "mbbo" if entry.direction == "1" else "mbbi"
    if entry.dt == "B1":
        return "bo" if entry.direction == "1" else "bi"
    if entry.dt.startswith("B"):
        return "mbbo" if entry.direction == "1" else "mbbi"
    return "ao" if entry.direction == "1" else "ai"


def generate_substitutions(
    slave: SlaveInfo,
    mapping: PdoMapping,
    mapping_index: int,
    mapping_count: int,
    optional_pdo_indexes: list[str] | None = None,
    selected_pdo_indexes: list[str] | None = None,
    hwtype_override: str | None = None,
    include_dc: bool = True,
    esi_file: str | None = None,
) -> str:
    collected: list[GeneratedEntry] = []
    _ = generate_hw_snippet(
        slave=slave,
        mapping=mapping,
        mapping_index=mapping_index,
        mapping_count=mapping_count,
        optional_pdo_indexes=optional_pdo_indexes,
        selected_pdo_indexes=selected_pdo_indexes,
        hwtype_override=hwtype_override,
        generated_entries=collected,
        include_dc=include_dc,
        esi_file=esi_file,
    )

    groups: dict[str, list[GeneratedEntry]] = {"ai": [], "ao": [], "bi": [], "bo": [], "mbbi": [], "mbbo": []}
    for entry in collected:
        groups[_entry_to_subst_group(entry)].append(entry)

    rows: list[str] = []
    hwtype = _resolve_hwtype(slave, mapping_index, mapping_count, hwtype_override)
    rows.append(f"#-  ecmc database for: {slave.display_name}")
    rows.append(f"#- {mapping.name}")
    if esi_file:
        rows.append(f"#- source ESI file: {esi_file}")
    rows.append(
        f"#- selected slave: type={slave.type_name or 'unknown'}, product={slave.product_code or 'unknown'}, revision={slave.revision or 'unknown'}"
    )
    rows.append(f"#- selected mapping id: M{mapping_index:02d} of {mapping_count}")
    rows.append(f"#-      ECMC_EC_HWTYPE:     {hwtype}")
    rows.append("#-      ECMC_EC_VENDOR_ID:  0x2")
    rows.append(f"#-      ECMC_EC_PRODUCT_ID: {slave.product_code}")
    rows.append(f"#-      ECMC_EC_REVISION:   {slave.revision}")
    rows.append("#-      templates:          db/generic/ecmc_ESI_*.template")
    rows.append("")

    def _add_file_block_ai_ao(template: str, entries: list[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append(f'file "{template}" {{')
        rows.append("    pattern { REC_NAME, DESC , SRC_NAME}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            rows.append(f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "{entry.source_name}"}}')
        rows.append("}")
        rows.append("")

    def _add_file_block_bi_bo(template: str, entries: list[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append(f'file "{template}" {{')
        rows.append("    pattern { REC_NAME, DESC , SRC_NAME}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            rows.append(f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "{entry.source_name}"}}')
        rows.append("}")
        rows.append("")

    def _add_file_block_mbbi(entries: list[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append('file "ecmc_ESI_mbbiDirect.template" {')
        rows.append("    pattern { REC_NAME, DESC, FLNK , SRC_NAME}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            if entry.bit_comment:
                for bit_line in _bit_comment_lines(entry.bit_comment):
                    rows.append(f"        #- {entry.source_name} {bit_line}")
            rows.append(f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "", "{entry.source_name}"}}')
        rows.append("}")
        rows.append("")

    def _add_file_block_mbbo(entries: list[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append('file "ecmc_ESI_mbboDirect.template" {')
        rows.append("    pattern { REC_NAME, DESC , SRC_NAME}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            if entry.bit_comment:
                for bit_line in _bit_comment_lines(entry.bit_comment):
                    rows.append(f"        #- {entry.source_name} {bit_line}")
            rows.append(f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "{entry.source_name}"}}')
        rows.append("}")
        rows.append("")

    _add_file_block_mbbo(groups["mbbo"])
    _add_file_block_mbbi(groups["mbbi"])
    _add_file_block_ai_ao("ecmc_ESI_ai.template", groups["ai"])
    _add_file_block_ai_ao("ecmc_ESI_ao.template", groups["ao"])
    _add_file_block_bi_bo("ecmc_ESI_bi.template", groups["bi"])
    _add_file_block_bi_bo("ecmc_ESI_bo.template", groups["bo"])

    return "\n".join(rows).rstrip() + "\n"


def mapping_details_text(slave: SlaveInfo, mapping: PdoMapping) -> str:
    lines: list[str] = []
    lines.append(f"Name: {mapping.name}")
    lines.append(f"Source: {mapping.source}")
    lines.append(f"Default: {'yes' if mapping.is_default else 'no'}")
    lines.append("")

    if not mapping.sm_groups:
        lines.append("(no SM/PDO data)")
        return "\n".join(lines) + "\n"

    for group in mapping.sm_groups:
        lines.append(f"SM{group.sm_no}")
        for pdo_index in group.pdos:
            pdo = slave.pdo_by_index.get(pdo_index)
            if pdo is None:
                lines.append(f"  - {pdo_index} (missing in RxPdo/TxPdo)")
                continue
            lines.append(f"  - {pdo.index}: {pdo.name} [{pdo.direction.upper()}]")
            for entry in pdo.entries:
                lines.append(
                    f"      {entry.index}:{entry.subindex} {entry.data_type}[{entry.bitlen}] "
                    f"{entry.resolved_name or entry.raw_name}"
                )
        lines.append("")

    optional_count = len(optional_pdos_for_mapping(slave, mapping))
    lines.append(f"Optional selectable PDOs: {optional_count}")
    lines.append("")

    lines.append("DC modes:")
    if not slave.dc_modes:
        lines.append("  (none)")
    else:
        selected = _select_dc_mode(slave)
        for mode in slave.dc_modes:
            mark = "*" if selected is mode else " "
            lines.append(
                f"  {mark} {mode.name or 'unnamed'}: AssignActivate={mode.assign_activate or '(none)'}"
            )
            lines.append(
                f"      Sync0 cycle={_normalize_dc_time(mode.cycle_time_sync0) or '(none)'} shift={_normalize_dc_time(mode.shift_time_sync0) or '0'}"
            )
            lines.append(
                f"      Sync1 cycle={_normalize_dc_time(mode.cycle_time_sync1) or '(none)'} shift={_normalize_dc_time(mode.shift_time_sync1) or '0'}"
            )

    return "\n".join(lines).rstrip() + "\n"


def run_gui(initial_file: Path, initial_name: str, initial_rev: str) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception as exc:
        print(f"GUI unavailable: {exc}", file=sys.stderr)
        return 2

    class BrowserApp:
        def __init__(self, root: tk.Tk) -> None:
            self.root = root
            self.root.title("ESI PDO Mapping Browser")
            self.root.geometry("1280x760")

            self.slaves: list[SlaveInfo] = []
            self.current_mappings: list[PdoMapping] = []
            self.current_pdo_choices: list[PdoChoice] = []
            self.optional_pdo_vars: list[tk.BooleanVar] = []
            self.generated_snippet = ""
            self.generated_substitutions = ""
            self.generated_popup: tk.Toplevel | None = None
            self.generated_hw_text: tk.Text | None = None
            self.generated_db_text: tk.Text | None = None
            self.generated_edit_var: tk.BooleanVar | None = None
            self.custom_hwtype_override = ""
            self.exclude_dc_clock = False
            self.hwtype_label_var = tk.StringVar(value="HWTYPE: auto")

            top = ttk.Frame(root, padding=8)
            top.pack(side=tk.TOP, fill=tk.X)

            ttk.Label(top, text="ESI file").grid(row=0, column=0, sticky=tk.W)
            self.file_var = tk.StringVar(value=str(initial_file))
            file_entry = ttk.Entry(top, textvariable=self.file_var, width=80)
            file_entry.grid(row=0, column=1, sticky=tk.EW, padx=6)
            file_entry.bind("<Return>", lambda _event: self._load())
            ttk.Button(top, text="Browse...", command=self._browse_file).grid(row=0, column=2, padx=4)

            ttk.Label(top, text="Name pattern").grid(row=1, column=0, sticky=tk.W)
            self.name_var = tk.StringVar(value=initial_name)
            name_entry = ttk.Entry(top, textvariable=self.name_var, width=30)
            name_entry.grid(row=1, column=1, sticky=tk.W, padx=6)
            name_entry.bind("<Return>", lambda _event: self._load())

            ttk.Label(top, text="Revision pattern").grid(row=1, column=2, sticky=tk.W, padx=(10, 0))
            self.rev_var = tk.StringVar(value=initial_rev)
            rev_entry = ttk.Entry(top, textvariable=self.rev_var, width=20)
            rev_entry.grid(row=1, column=3, sticky=tk.W, padx=6)
            rev_entry.bind("<Return>", lambda _event: self._load())

            ttk.Button(top, text="Load", command=self._load).grid(row=1, column=4, padx=8)
            top.columnconfigure(1, weight=1)

            body = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
            body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

            left_frame = ttk.Frame(body)
            right_frame = ttk.Frame(body)
            body.add(left_frame, weight=2)
            body.add(right_frame, weight=3)

            ttk.Label(left_frame, text="Slaves").pack(anchor=tk.W, pady=(0, 4))
            self.slave_list = tk.Listbox(left_frame, exportselection=False)
            self.slave_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            slave_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.slave_list.yview)
            slave_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.slave_list.config(yscrollcommand=slave_scroll.set)
            self.slave_list.bind("<<ListboxSelect>>", self._on_slave_select)

            ttk.Label(right_frame, text="PDO mappings").pack(anchor=tk.W, pady=(0, 4))
            self.mapping_list = tk.Listbox(right_frame, exportselection=False, height=6)
            self.mapping_list.pack(fill=tk.X)
            self.mapping_list.bind("<<ListboxSelect>>", self._on_mapping_select)

            ttk.Label(right_frame, text="PDOs (default pre-selected)").pack(anchor=tk.W, pady=(8, 4))
            optional_frame = ttk.Frame(right_frame)
            optional_frame.pack(fill=tk.X)
            self.pdo_list_bg = self.mapping_list.cget("background")
            self.optional_pdo_canvas = tk.Canvas(
                optional_frame,
                height=220,
                highlightthickness=1,
                bg=self.pdo_list_bg,
            )
            self.optional_pdo_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
            optional_scroll = ttk.Scrollbar(
                optional_frame,
                orient=tk.VERTICAL,
                command=self.optional_pdo_canvas.yview,
            )
            optional_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.optional_pdo_canvas.configure(yscrollcommand=optional_scroll.set)
            self.optional_pdo_inner = tk.Frame(self.optional_pdo_canvas, bg=self.pdo_list_bg)
            self.optional_pdo_window = self.optional_pdo_canvas.create_window(
                (0, 0),
                window=self.optional_pdo_inner,
                anchor=tk.NW,
            )
            self.optional_pdo_inner.bind("<Configure>", self._on_optional_inner_configure)
            self.optional_pdo_canvas.bind("<Configure>", self._on_optional_canvas_configure)

            action_row = ttk.Frame(right_frame)
            action_row.pack(fill=tk.X, pady=(6, 4))
            ttk.Button(action_row, text="Generate files", command=self._generate_files_popup).pack(side=tk.LEFT)
            ttk.Button(action_row, text="Options...", command=self._open_options_popup).pack(
                side=tk.LEFT, padx=(6, 0)
            )
            ttk.Label(action_row, textvariable=self.hwtype_label_var).pack(side=tk.RIGHT)

            ttk.Label(right_frame, text="Details").pack(anchor=tk.W, pady=(8, 4))
            self.details = tk.Text(right_frame, wrap=tk.NONE, height=24)
            self.details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            details_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.details.yview)
            details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.details.config(yscrollcommand=details_scroll.set)

            self.status_var = tk.StringVar(value="Load an ESI file to begin.")
            self.busy_var = tk.StringVar(value="Idle")
            status_frame = ttk.Frame(root, padding=(8, 4), relief=tk.SUNKEN, borderwidth=1)
            status_frame.pack(side=tk.BOTTOM, fill=tk.X)
            ttk.Label(status_frame, textvariable=self.busy_var, width=12, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(
                side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8)
            )
            self.progress = ttk.Progressbar(status_frame, mode="determinate", maximum=100, value=0, length=260)
            self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=False)

            self._load()

        def _set_busy(self, busy: bool, message: str | None = None) -> None:
            if message is not None:
                self.status_var.set(message)
            if busy:
                self.busy_var.set("Working...")
                self.progress.configure(mode="indeterminate")
                self.progress.start(12)
                self.root.config(cursor="watch")
            else:
                self.progress.stop()
                self.progress.configure(mode="determinate", value=0)
                self.busy_var.set("Idle")
                self.root.config(cursor="")
            self.root.update_idletasks()

        def _browse_file(self) -> None:
            picked = filedialog.askopenfilename(
                title="Choose ESI XML file",
                filetypes=(("XML files", "*.xml"), ("All files", "*.*")),
            )
            if picked:
                self.file_var.set(picked)
                self._load()

        def _auto_hwtype_for_current_selection(self) -> str:
            slave = self._selected_slave()
            _, mapping_idx0 = self._selected_mapping()
            if slave is None or mapping_idx0 < 0:
                return ""
            return _build_hwtype(slave, mapping_idx0 + 1, max(1, len(slave.mappings)))

        def _update_hwtype_indicator(self) -> None:
            dc_state = "off" if self.exclude_dc_clock else "on"
            if self.custom_hwtype_override.strip():
                self.hwtype_label_var.set(f"HWTYPE: custom={_snake(self.custom_hwtype_override)} | DC:{dc_state}")
                return
            auto_hwtype = self._auto_hwtype_for_current_selection()
            if auto_hwtype:
                self.hwtype_label_var.set(f"HWTYPE: auto={auto_hwtype} | DC:{dc_state}")
            else:
                self.hwtype_label_var.set(f"HWTYPE: auto | DC:{dc_state}")

        def _open_options_popup(self) -> None:
            auto_hwtype = self._auto_hwtype_for_current_selection()
            dialog = tk.Toplevel(self.root)
            dialog.title("Generator options")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.resizable(False, False)

            frame = ttk.Frame(dialog, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(
                frame,
                text="Custom HWTYPE (leave empty for automatic):",
            ).grid(row=0, column=0, sticky=tk.W)
            hwtype_var = tk.StringVar(value=self.custom_hwtype_override or auto_hwtype)
            hwtype_entry = ttk.Entry(frame, textvariable=hwtype_var, width=46)
            hwtype_entry.grid(row=1, column=0, sticky=tk.EW, pady=(4, 8))

            exclude_dc_var = tk.BooleanVar(value=self.exclude_dc_clock)
            ttk.Checkbutton(
                frame,
                text="Exclude DC clock config from HW snippet",
                variable=exclude_dc_var,
            ).grid(row=2, column=0, sticky=tk.W)

            btns = ttk.Frame(frame)
            btns.grid(row=3, column=0, sticky=tk.E, pady=(10, 0))

            def _apply_options() -> None:
                value = hwtype_var.get().strip()
                self.custom_hwtype_override = value
                self.exclude_dc_clock = bool(exclude_dc_var.get())
                if value:
                    self.status_var.set(f"Options saved: HWTYPE={_snake(value)}, DC={'off' if self.exclude_dc_clock else 'on'}")
                else:
                    self.status_var.set(f"Options saved: HWTYPE=auto, DC={'off' if self.exclude_dc_clock else 'on'}")
                self._update_hwtype_indicator()
                dialog.destroy()

            ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
            ttk.Button(btns, text="Apply", command=_apply_options).pack(side=tk.RIGHT, padx=(0, 6))

            frame.columnconfigure(0, weight=1)
            hwtype_entry.focus_set()
            dialog.bind("<Return>", lambda _event: _apply_options())
            dialog.bind("<Escape>", lambda _event: dialog.destroy())

        def _selected_slave(self):
            sel = self.slave_list.curselection()
            if not sel:
                return None
            return self.slaves[sel[0]]

        def _selected_mapping(self):
            sel = self.mapping_list.curselection()
            if not sel:
                return None, -1
            idx = sel[0]
            if idx >= len(self.current_mappings):
                return None, -1
            return self.current_mappings[idx], idx

        def _selected_checked_pdo_indexes(self) -> list[str]:
            indexes: list[str] = []
            for idx, var in enumerate(self.optional_pdo_vars):
                if var.get() and 0 <= idx < len(self.current_pdo_choices):
                    indexes.append(self.current_pdo_choices[idx].pdo.index)
            return indexes

        def _on_optional_inner_configure(self, _event) -> None:
            self.optional_pdo_canvas.configure(scrollregion=self.optional_pdo_canvas.bbox("all"))

        def _on_optional_canvas_configure(self, event) -> None:
            self.optional_pdo_canvas.itemconfigure(self.optional_pdo_window, width=event.width)

        def _clear_optional_pdos(self) -> None:
            self.current_pdo_choices = []
            self.optional_pdo_vars = []
            for child in self.optional_pdo_inner.winfo_children():
                child.destroy()
            self.optional_pdo_canvas.yview_moveto(0)

        def _refresh_optional_pdos(self, slave: SlaveInfo, mapping: PdoMapping) -> None:
            self._clear_optional_pdos()
            self.current_pdo_choices = pdo_choices_for_mapping(slave, mapping)

            if self.current_pdo_choices:
                header = tk.Frame(self.optional_pdo_inner, bg=self.pdo_list_bg)
                header.pack(fill=tk.X, padx=4, pady=(2, 1))
                header.grid_columnconfigure(5, weight=1)
                for col, (label_text, width) in enumerate(
                    (
                        ("Sel", 4),
                        ("Type", 9),
                        ("Index", 12),
                        ("Dir", 5),
                        ("SM", 4),
                        ("PDO Name", 0),
                    )
                ):
                    kwargs = {
                        "text": label_text,
                        "anchor": tk.W,
                        "bg": self.pdo_list_bg,
                        "font": ("TkDefaultFont", 9, "bold"),
                    }
                    if width > 0:
                        kwargs["width"] = width
                    tk.Label(header, **kwargs).grid(row=0, column=col, sticky=tk.W, padx=(0, 6))

            for choice in self.current_pdo_choices:
                pdo = choice.pdo
                row = tk.Frame(self.optional_pdo_inner, bg=self.pdo_list_bg)
                row.pack(fill=tk.X, padx=4, pady=1)
                row.grid_columnconfigure(5, weight=1)

                var = tk.BooleanVar(value=choice.is_default)
                self.optional_pdo_vars.append(var)

                tk.Checkbutton(
                    row,
                    variable=var,
                    bg=self.pdo_list_bg,
                    activebackground=self.pdo_list_bg,
                    highlightthickness=0,
                    relief=tk.FLAT,
                    padx=0,
                    pady=0,
                ).grid(row=0, column=0, sticky=tk.W, padx=(0, 6))

                row_type = "DEFAULT" if choice.is_default else "OPTIONAL"
                tk.Label(row, text=row_type, width=9, anchor=tk.W, bg=self.pdo_list_bg).grid(
                    row=0, column=1, sticky=tk.W, padx=(0, 6)
                )
                tk.Label(row, text=pdo.index, width=12, anchor=tk.W, bg=self.pdo_list_bg).grid(
                    row=0, column=2, sticky=tk.W, padx=(0, 6)
                )
                tk.Label(row, text=pdo.direction.upper(), width=5, anchor=tk.W, bg=self.pdo_list_bg).grid(
                    row=0, column=3, sticky=tk.W, padx=(0, 6)
                )
                tk.Label(row, text=choice.sm_no, width=4, anchor=tk.W, bg=self.pdo_list_bg).grid(
                    row=0, column=4, sticky=tk.W, padx=(0, 6)
                )
                tk.Label(row, text=pdo.name, anchor=tk.W, justify=tk.LEFT, bg=self.pdo_list_bg).grid(
                    row=0, column=5, sticky=tk.W
                )

            if not self.current_pdo_choices:
                tk.Label(
                    self.optional_pdo_inner,
                    text="(No PDOs available for this mapping)",
                    anchor=tk.W,
                    justify=tk.LEFT,
                    bg=self.pdo_list_bg,
                ).pack(anchor=tk.W, padx=4, pady=2)

            self.optional_pdo_canvas.update_idletasks()
            self.optional_pdo_canvas.configure(
                scrollregion=self.optional_pdo_canvas.bbox("all"),
            )

        def _load(self) -> None:
            p = Path(self.file_var.get()).expanduser()
            if not p.exists():
                messagebox.showerror("File not found", f"No such file:\n{p}")
                return
            self._set_busy(True, "Loading and parsing ESI...")
            try:
                try:
                    self.slaves = parse_esi_file(p, self.name_var.get().strip() or "*", self.rev_var.get().strip() or "*")
                except Exception as exc:
                    messagebox.showerror("Parse failed", f"Failed to parse XML:\n{exc}")
                    return

                self.slave_list.delete(0, tk.END)
                self.mapping_list.delete(0, tk.END)
                self._clear_optional_pdos()
                self.details.delete("1.0", tk.END)
                self.current_mappings = []
                self.generated_snippet = ""
                self.generated_substitutions = ""

                for slave in self.slaves:
                    self.slave_list.insert(tk.END, slave.short_label)

                self.status_var.set(f"Loaded {len(self.slaves)} slave(s).")
                if self.slaves:
                    self.slave_list.selection_set(0)
                    self._on_slave_select(None)
                self._update_hwtype_indicator()
            finally:
                self._set_busy(False)

        def _on_slave_select(self, _event) -> None:
            slave = self._selected_slave()
            if slave is None:
                return
            self.current_mappings = slave.mappings
            self.generated_snippet = ""
            self.generated_substitutions = ""

            self.mapping_list.delete(0, tk.END)
            for mapping in self.current_mappings:
                default_str = " (default)" if mapping.is_default else ""
                self.mapping_list.insert(tk.END, f"{mapping.name}{default_str}")

            if self.current_mappings:
                default_idx = next((idx for idx, m in enumerate(self.current_mappings) if m.is_default), 0)
                self.mapping_list.selection_set(default_idx)
                self._on_mapping_select(None)
            else:
                self._clear_optional_pdos()
                self.details.delete("1.0", tk.END)
                self.details.insert(tk.END, "No PDO mappings found for this slave.\n")
                self._update_hwtype_indicator()

        def _on_mapping_select(self, _event) -> None:
            slave = self._selected_slave()
            mapping, _ = self._selected_mapping()
            if slave is None or mapping is None:
                return
            self.generated_snippet = ""
            self.generated_substitutions = ""
            self._refresh_optional_pdos(slave, mapping)
            self.details.delete("1.0", tk.END)
            self.details.insert(tk.END, mapping_details_text(slave, mapping))
            self._update_hwtype_indicator()

        def _show_generated_files_popup(self) -> None:
            if self.generated_popup is not None and self.generated_popup.winfo_exists():
                self.generated_popup.destroy()
            self.generated_popup = None
            self.generated_hw_text = None
            self.generated_db_text = None
            self.generated_edit_var = None

            dialog = tk.Toplevel(self.root)
            dialog.title("Generated files")
            dialog.transient(self.root)
            dialog.geometry("1180x760")
            self.generated_popup = dialog

            outer = ttk.Frame(dialog, padding=8)
            outer.pack(fill=tk.BOTH, expand=True)

            notebook = ttk.Notebook(outer)
            notebook.pack(fill=tk.BOTH, expand=True)

            def _add_tab(tab_title: str, content: str) -> tk.Text:
                tab = ttk.Frame(notebook)
                notebook.add(tab, text=tab_title)
                text = tk.Text(tab, wrap=tk.NONE)
                text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                yscroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=text.yview)
                yscroll.pack(side=tk.RIGHT, fill=tk.Y)
                xscroll = ttk.Scrollbar(tab, orient=tk.HORIZONTAL, command=text.xview)
                xscroll.pack(side=tk.BOTTOM, fill=tk.X)
                text.config(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
                text.insert("1.0", content)
                text.config(state=tk.DISABLED)
                return text

            self.generated_hw_text = _add_tab("HW snippet", self.generated_snippet)
            self.generated_db_text = _add_tab("DB file", self.generated_substitutions)

            btns = ttk.Frame(outer)
            btns.pack(fill=tk.X, pady=(8, 0))
            self.generated_edit_var = tk.BooleanVar(value=False)

            def _set_editable_state() -> None:
                editable = bool(self.generated_edit_var and self.generated_edit_var.get())
                state = tk.NORMAL if editable else tk.DISABLED
                for widget in (self.generated_hw_text, self.generated_db_text):
                    if widget is not None and widget.winfo_exists():
                        widget.config(state=state)

            def _close_popup() -> None:
                self.generated_popup = None
                self.generated_hw_text = None
                self.generated_db_text = None
                self.generated_edit_var = None
                dialog.destroy()

            ttk.Checkbutton(
                btns,
                text="Enable editing",
                variable=self.generated_edit_var,
                command=_set_editable_state,
            ).pack(side=tk.LEFT)
            ttk.Button(btns, text="Save HW snippet...", command=self._save_snippet).pack(side=tk.LEFT)
            ttk.Button(btns, text="Save DB file...", command=self._save_substitutions).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(btns, text="Close", command=_close_popup).pack(side=tk.RIGHT)
            dialog.protocol("WM_DELETE_WINDOW", _close_popup)

        def _sync_generated_texts_from_popup(self) -> None:
            if self.generated_hw_text is not None and self.generated_hw_text.winfo_exists():
                self.generated_snippet = self.generated_hw_text.get("1.0", "end-1c")
            if self.generated_db_text is not None and self.generated_db_text.winfo_exists():
                self.generated_substitutions = self.generated_db_text.get("1.0", "end-1c")

        def _generate_files_popup(self) -> None:
            slave = self._selected_slave()
            mapping, mapping_idx0 = self._selected_mapping()
            if slave is None or mapping is None:
                messagebox.showwarning("Selection missing", "Select a slave and PDO mapping first.")
                return

            self._set_busy(True, "Generating hardware snippet and DB file...")
            try:
                self.generated_snippet = generate_hw_snippet(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    include_dc=not self.exclude_dc_clock,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.generated_substitutions = generate_substitutions(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    include_dc=not self.exclude_dc_clock,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.status_var.set(
                    f"Generated HW + DB for {slave.type_name}, mapping {mapping_idx0 + 1}/{len(slave.mappings)}"
                )
            finally:
                self._set_busy(False)

            self._show_generated_files_popup()

        def _generate_snippet(self) -> None:
            slave = self._selected_slave()
            mapping, mapping_idx0 = self._selected_mapping()
            if slave is None or mapping is None:
                messagebox.showwarning("Selection missing", "Select a slave and PDO mapping first.")
                return

            self._set_busy(True, "Generating hardware snippet...")
            try:
                snippet = generate_hw_snippet(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    include_dc=not self.exclude_dc_clock,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.generated_snippet = snippet
                self.details.delete("1.0", tk.END)
                self.details.insert(tk.END, snippet)
                self.status_var.set(
                    f"Generated snippet for {slave.type_name}, mapping {mapping_idx0 + 1}/{len(slave.mappings)}"
                )
            finally:
                self._set_busy(False)

        def _generate_substitutions(self) -> None:
            slave = self._selected_slave()
            mapping, mapping_idx0 = self._selected_mapping()
            if slave is None or mapping is None:
                messagebox.showwarning("Selection missing", "Select a slave and PDO mapping first.")
                return

            self._set_busy(True, "Generating substitutions...")
            try:
                subst = generate_substitutions(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    include_dc=not self.exclude_dc_clock,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.generated_substitutions = subst
                self.details.delete("1.0", tk.END)
                self.details.insert(tk.END, subst)
                self.status_var.set(
                    f"Generated substitutions for {slave.type_name}, mapping {mapping_idx0 + 1}/{len(slave.mappings)}"
                )
            finally:
                self._set_busy(False)

        def _save_snippet(self) -> None:
            self._sync_generated_texts_from_popup()
            if not self.generated_snippet:
                self._generate_files_popup()
                if not self.generated_snippet:
                    return

            slave = self._selected_slave()
            _, mapping_idx0 = self._selected_mapping()
            default_name = "ecmcSnippet.cmd"
            if slave is not None and mapping_idx0 >= 0:
                hwtype = _resolve_hwtype(
                    slave,
                    mapping_idx0 + 1,
                    max(1, len(slave.mappings)),
                    self.custom_hwtype_override or None,
                )
                default_name = f"ecmc{hwtype}.cmd"

            path = filedialog.asksaveasfilename(
                title="Save hardware snippet",
                defaultextension=".cmd",
                initialfile=default_name,
                filetypes=(("Command files", "*.cmd"), ("All files", "*.*")),
            )
            if not path:
                return
            self._set_busy(True, "Saving snippet...")
            try:
                self._sync_generated_texts_from_popup()
                Path(path).write_text(self.generated_snippet)
                self.status_var.set(f"Saved snippet: {path}")
            finally:
                self._set_busy(False)

        def _save_substitutions(self) -> None:
            self._sync_generated_texts_from_popup()
            if not self.generated_substitutions:
                self._generate_files_popup()
                if not self.generated_substitutions:
                    return

            slave = self._selected_slave()
            _, mapping_idx0 = self._selected_mapping()
            default_name = "ecmc.substitutions"
            if slave is not None and mapping_idx0 >= 0:
                hwtype = _resolve_hwtype(
                    slave,
                    mapping_idx0 + 1,
                    max(1, len(slave.mappings)),
                    self.custom_hwtype_override or None,
                )
                default_name = f"ecmc{hwtype}.substitutions"

            path = filedialog.asksaveasfilename(
                title="Save substitutions",
                defaultextension=".substitutions",
                initialfile=default_name,
                filetypes=(("Substitution files", "*.substitutions"), ("All files", "*.*")),
            )
            if not path:
                return
            self._set_busy(True, "Saving substitutions...")
            try:
                self._sync_generated_texts_from_popup()
                Path(path).write_text(self.generated_substitutions)
                self.status_var.set(f"Saved substitutions: {path}")
            finally:
                self._set_busy(False)

    root = tk.Tk()
    BrowserApp(root)
    root.mainloop()
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    script_dir = Path(__file__).resolve().parent
    default_candidates = [
        Path("../Beckhoff_EtherCAT_XML-4/Beckhoff EL1xxx.xml").expanduser(),
        script_dir.parent.parent / "Beckhoff_EtherCAT_XML-4/Beckhoff EL1xxx.xml",
    ]
    default_file = default_candidates[0]
    for candidate in default_candidates:
        if candidate.exists():
            default_file = candidate
            break
    p = argparse.ArgumentParser(description="Browse PDO mappings from Beckhoff ESI XML.")
    p.add_argument("--file", default=str(default_file), help="ESI XML file path")
    p.add_argument("--name", default="*", help="Wildcard for slave name/type (default: *)")
    p.add_argument("--rev", default="*", help="Wildcard for revision in hex (default: *)")
    p.add_argument("--no-gui", action="store_true", help="Run in terminal mode")
    p.add_argument(
        "--generate-snippet",
        action="store_true",
        help="In --no-gui mode: generate one hardware snippet",
    )
    p.add_argument(
        "--generate-substitutions",
        action="store_true",
        help="In --no-gui mode: generate one substitutions file",
    )
    p.add_argument(
        "--slave-index",
        type=int,
        help="1-based slave index from listing (used with generation options)",
    )
    p.add_argument(
        "--mapping-index",
        type=int,
        default=1,
        help="1-based mapping index on selected slave (default: 1)",
    )
    p.add_argument(
        "--snippet-out",
        help="Output .cmd file for generated snippet (default: print to stdout)",
    )
    p.add_argument(
        "--substitutions-out",
        help="Output .substitutions file (default: print to stdout)",
    )
    p.add_argument(
        "--optional-pdos",
        help="Comma-separated PDO indexes to include as optional, e.g. 0x1600,0x1a08",
    )
    p.add_argument(
        "--exclude-dc",
        action="store_true",
        help="Exclude DC clock config lines from generated HW snippet",
    )
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    file_path = Path(args.file).expanduser()

    if args.no_gui:
        try:
            slaves = parse_esi_file(file_path, args.name, args.rev)
        except Exception as exc:
            print(f"Failed to parse '{file_path}': {exc}", file=sys.stderr)
            return 1

        generation_count = int(bool(args.generate_snippet)) + int(bool(args.generate_substitutions))
        if generation_count == 0:
            print_mappings(slaves)
            return 0
        if generation_count > 1:
            print("Choose only one generation mode: --generate-snippet or --generate-substitutions", file=sys.stderr)
            return 2
        if args.generate_snippet and args.substitutions_out:
            print("--substitutions-out cannot be used with --generate-snippet", file=sys.stderr)
            return 2
        if args.generate_substitutions and args.snippet_out:
            print("--snippet-out cannot be used with --generate-substitutions", file=sys.stderr)
            return 2

        if args.slave_index is None:
            print("Generation requires --slave-index", file=sys.stderr)
            return 2
        if args.slave_index < 1 or args.slave_index > len(slaves):
            print(f"Invalid --slave-index {args.slave_index}, valid range: 1..{len(slaves)}", file=sys.stderr)
            return 2

        slave = slaves[args.slave_index - 1]
        if not slave.mappings:
            print("Selected slave has no PDO mappings.", file=sys.stderr)
            return 2

        if args.mapping_index < 1 or args.mapping_index > len(slave.mappings):
            print(
                f"Invalid --mapping-index {args.mapping_index}, valid range: 1..{len(slave.mappings)}",
                file=sys.stderr,
            )
            return 2

        mapping = slave.mappings[args.mapping_index - 1]
        optional_pdo_indexes: list[str] = []
        if args.optional_pdos:
            for item in args.optional_pdos.split(","):
                pdo_index = _norm_hex(item.strip())
                if pdo_index:
                    optional_pdo_indexes.append(pdo_index)
        if args.generate_snippet:
            output = generate_hw_snippet(
                slave=slave,
                mapping=mapping,
                mapping_index=args.mapping_index,
                mapping_count=len(slave.mappings),
                optional_pdo_indexes=optional_pdo_indexes,
                include_dc=not args.exclude_dc,
                esi_file=str(file_path),
            )
            if args.snippet_out:
                output_file = Path(args.snippet_out).expanduser()
                output_file.write_text(output)
                print(f"Wrote snippet: {output_file}")
                return 0
        else:
            output = generate_substitutions(
                slave=slave,
                mapping=mapping,
                mapping_index=args.mapping_index,
                mapping_count=len(slave.mappings),
                optional_pdo_indexes=optional_pdo_indexes,
                include_dc=not args.exclude_dc,
                esi_file=str(file_path),
            )
            if args.substitutions_out:
                output_file = Path(args.substitutions_out).expanduser()
                output_file.write_text(output)
                print(f"Wrote substitutions: {output_file}")
                return 0

        print(output, end="")
        return 0

    return run_gui(file_path, args.name, args.rev)


if __name__ == "__main__":
    raise SystemExit(main())
