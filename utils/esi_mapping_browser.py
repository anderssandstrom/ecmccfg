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

from typing import Dict, List, Optional, Set, Tuple

import argparse
import fnmatch
import re
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from compat_dataclasses import dataclass, field
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

LEGACY_PDO_OUT_MAP = {
    "DIG": "BO",
    "ENC": "Enc",
    "MTI": "BI",
    "MTO": "BO",
    "POS": "Pos",
    "STM": "Drv",
    "Latch": "Ltch",
    "Channel": "BO",
}

LEGACY_PDO_IN_MAP = {
    "DIG": "BI",
    "ENC": "Enc",
    "MTI": "BI",
    "MTO": "BO",
    "POS": "Pos",
    "STM": "Drv",
    "Latch": "Ltch",
    "Channel": "BI",
}

DEV_NEEDS_INDEX = {"ENC", "MTI", "MTO", "POS", "STM", "DRV"}
SINGLE_CH_NEEDS_INDEX = {"AI", "AO", "BI", "BO"}
REMOVE_LAST_MAP = {"Outp-Outp": "", "Inp-Inp": ""}


def _text(node: Optional[ET.Element]) -> str:
    return (node.text or "").strip() if node is not None else ""


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_hexish(value: Optional[str]) -> Optional[int]:
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


def _norm_hex(value: Optional[str]) -> str:
    parsed = _parse_hexish(value)
    if parsed is None:
        return ""
    return f"0x{parsed:x}"


def _norm_subindex(value: Optional[str]) -> str:
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


def _normalize_pattern_items(pattern_expr: Optional[str]) -> List[str]:
    if pattern_expr is None:
        return ["*"]

    raw = [part.strip() for part in pattern_expr.split(",")]
    patterns = [part for part in raw if part]
    if not patterns:
        return ["*"]

    normalized: List[str] = []
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


def _match_pattern(value: str, pattern_expr: Optional[str]) -> bool:
    value_l = value.lower()
    for pat in _normalize_pattern_items(pattern_expr):
        if fnmatch.fnmatch(value_l, pat.lower()):
            return True
    return False


@dataclass
class SmPdoGroup:
    sm_no: str
    pdos: List[str] = field(default_factory=list)


@dataclass
class PdoMapping:
    name: str
    is_default: bool
    source: str
    sm_groups: List[SmPdoGroup] = field(default_factory=list)


@dataclass
class SdoField:
    index: str
    subindex: str
    name: str
    data_type: str
    bit_size: Optional[int]
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
    excludes: Set[str] = field(default_factory=set)
    entries: List[PdoEntry] = field(default_factory=list)


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
class CoeInitCmdInfo:
    transition: str
    index: str
    subindex: str
    data_hex: str
    data_bytes: str
    byte_size: int
    complete_access: bool = False
    fixed: bool = False
    overwritten_by_module: bool = False
    data_adapt_automatically: bool = False
    comment: str = ""


@dataclass
class SlaveInfo:
    type_name: str
    display_name: str
    product_code: str
    revision: str
    mappings: List[PdoMapping] = field(default_factory=list)
    pdo_by_index: Dict[str, PdoInfo] = field(default_factory=dict)
    sdo_fields: Dict[Tuple[str, str], SdoField] = field(default_factory=dict)
    dc_modes: List[DcModeInfo] = field(default_factory=list)
    coe_init_cmds: List[CoeInitCmdInfo] = field(default_factory=list)

    @property
    def short_label(self) -> str:
        shown_type = self.type_name or "UnknownType"
        shown_rev = self.revision or "unknown-rev"
        shown_name = self.display_name or "Unnamed slave"
        return f"{shown_type} {shown_rev} - {shown_name}"


def _extract_alternative_mappings(device: ET.Element) -> List[PdoMapping]:
    mappings: List[PdoMapping] = []
    for idx, alt in enumerate(device.findall(".//AlternativeSmMapping"), start=1):
        name = _text(alt.find("Name")) or f"Alternative mapping {idx}"
        is_default = (alt.get("Default") or "").strip() == "1"
        groups: List[SmPdoGroup] = []
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


def _extract_implicit_mapping(device: ET.Element) -> Optional[PdoMapping]:
    sm_map: OrderedDict[str, List[str]] = OrderedDict()

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

    groups: List[SmPdoGroup] = []
    for sm_no, pdos in sm_map.items():
        pdos_sorted = sorted(pdos, key=lambda idx: (_parse_hexish(idx) is None, _parse_hexish(idx) or 0, idx))
        groups.append(SmPdoGroup(sm_no=sm_no, pdos=pdos_sorted))
    return PdoMapping(
        name="Implicit default mapping",
        is_default=True,
        source="RxPdo/TxPdo @Sm",
        sm_groups=groups,
    )


def _extract_sdo_lookup(device: ET.Element) -> Dict[Tuple[str, str], SdoField]:
    data_types: Dict[str, Dict[str, SdoField]] = {}

    for dt in device.findall("./Profile/Dictionary/DataTypes/DataType"):
        dt_name = _text(dt.find("Name"))
        if not dt_name:
            continue

        sub_lookup: Dict[str, SdoField] = {}
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

    lookup: Dict[Tuple[str, str], SdoField] = {}
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


def _resolve_entry_name(entry_name: str, sdo_field: Optional[SdoField]) -> str:
    if sdo_field is not None:
        if sdo_field.name and not _is_generic_subindex_name(sdo_field.name):
            return sdo_field.name
    return entry_name


def _parse_pdo_definitions(
    device: ET.Element,
    sdo_lookup: Dict[Tuple[str, str], SdoField],
) -> Dict[str, PdoInfo]:
    pdo_by_index: Dict[str, PdoInfo] = {}

    for tag, direction in (("TxPdo", "tx"), ("RxPdo", "rx")):
        for pdo in device.findall(tag):
            pdo_index = _norm_hex(_text(pdo.find("Index")))
            if not pdo_index:
                continue

            sm = (pdo.get("Sm") or "").strip()
            pdo_name = _text(pdo.find("Name"))
            excludes = {_norm_hex(_text(ex_node)) for ex_node in pdo.findall("Exclude")}
            excludes = {idx for idx in excludes if idx}
            entries: List[PdoEntry] = []
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
                    excludes=excludes,
                    entries=entries,
                )
            else:
                if excludes:
                    pdo_by_index[pdo_index].excludes.update(excludes)
                if not pdo_by_index[pdo_index].entries and entries:
                    pdo_by_index[pdo_index].entries = entries

    return pdo_by_index


def _extract_dc_modes(device: ET.Element) -> List[DcModeInfo]:
    modes: List[DcModeInfo] = []
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


def _bool_attr(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip() in ("1", "true", "True", "yes", "on")


def _normalize_data_hex(data_text: str) -> str:
    hex_only = "".join(ch for ch in data_text.strip() if ch in "0123456789abcdefABCDEF")
    if not hex_only:
        return ""
    if len(hex_only) % 2 != 0:
        hex_only = "0" + hex_only
    return hex_only.upper()


def _hex_to_spaced_bytes(data_hex: str) -> str:
    if not data_hex:
        return ""
    return " ".join(data_hex[i : i + 2] for i in range(0, len(data_hex), 2))


def _le_hex_to_int(data_hex: str) -> int:
    if not data_hex:
        return 0
    return int.from_bytes(bytes.fromhex(data_hex), byteorder="little", signed=False)


def _extract_coe_initcmds(device: ET.Element) -> List[CoeInitCmdInfo]:
    init_cmds: List[CoeInitCmdInfo] = []
    for init in device.findall("./Mailbox/CoE/InitCmd"):
        transition = _text(init.find("Transition"))
        index = _norm_hex(_text(init.find("Index")))
        if not index:
            continue
        subindex = _norm_subindex(_text(init.find("SubIndex")))
        data_node = init.find("Data")
        data_text = _text(data_node)
        data_hex = _normalize_data_hex(data_text)
        data_bytes = _hex_to_spaced_bytes(data_hex)
        byte_size = len(data_hex) // 2
        comment = _text(init.find("Comment"))
        init_cmds.append(
            CoeInitCmdInfo(
                transition=transition,
                index=index,
                subindex=subindex,
                data_hex=data_hex,
                data_bytes=data_bytes,
                byte_size=byte_size,
                complete_access=_bool_attr(init.get("CompleteAccess")),
                fixed=_bool_attr(init.get("Fixed")),
                overwritten_by_module=_bool_attr(init.get("OverwrittenByModule")),
                data_adapt_automatically=_bool_attr(data_node.get("AdaptAutomatically") if data_node is not None else None),
                comment=comment,
            )
        )
    return init_cmds


def _device_names_for_match(device: ET.Element, type_name: str, display_name: str) -> List[str]:
    names = [type_name, display_name]
    for n in device.findall("Name"):
        n_text = _text(n)
        if n_text:
            names.append(n_text)
    return [n for n in names if n]


def parse_esi_file(
    file_path: Path, name_pattern: str = "*", rev_pattern: str = "*"
) -> List[SlaveInfo]:
    root = ET.parse(file_path).getroot()
    devices = root.findall(".//Descriptions/Devices/Device")

    slaves: List[SlaveInfo] = []
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
        coe_init_cmds = _extract_coe_initcmds(device)

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
                coe_init_cmds=coe_init_cmds,
            )
        )

    slaves.sort(key=lambda d: (d.type_name, _parse_hexish(d.revision) or 0, d.display_name))
    return slaves


_SUPPORTED_HW_CACHE: Dict[str, Tuple[List[str], Dict[str, List[str]], List[str]]] = {}


def _find_ecmccfg_root(anchor: Optional[Path] = None) -> Optional[Path]:
    candidates: List[Path] = []
    if anchor is not None:
        anchor_resolved = anchor.resolve()
        candidates.extend([anchor_resolved, *anchor_resolved.parents])

    script_dir = Path(__file__).resolve().parent
    candidates.extend([script_dir, *script_dir.parents])

    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])

    seen: Set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "hardware").is_dir() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _normalize_hw_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value).upper()


def _extract_hw_desc_from_stem(stem: str) -> str:
    if not stem.lower().startswith("ecmc"):
        return ""
    return stem[4:]


def _scan_supported_hardware(
    ecmccfg_root: Optional[Path] = None,
) -> Tuple[Optional[Path], List[str], Dict[str, List[str]], List[str]]:
    root = ecmccfg_root if ecmccfg_root is not None else _find_ecmccfg_root()
    if root is None:
        return None, [], {}, []

    cache_key = str(root.resolve())
    cached = _SUPPORTED_HW_CACHE.get(cache_key)
    if cached is not None:
        descs, by_desc, rel_files = cached
        return root, list(descs), {k: list(v) for k, v in by_desc.items()}, list(rel_files)

    by_desc: Dict[str, List[str]] = {}
    rel_files: List[str] = []
    hw_dir = root / "hardware"
    for cmd_file in sorted(hw_dir.rglob("*.cmd")):
        rel = cmd_file.relative_to(root).as_posix()
        rel_files.append(rel)
        desc = _extract_hw_desc_from_stem(cmd_file.stem)
        if not desc:
            continue
        by_desc.setdefault(desc, []).append(rel)

    descs = sorted(by_desc.keys(), key=lambda item: (_normalize_hw_token(item), item))
    _SUPPORTED_HW_CACHE[cache_key] = (list(descs), {k: list(v) for k, v in by_desc.items()}, list(rel_files))
    return root, list(descs), {k: list(v) for k, v in by_desc.items()}, list(rel_files)


def _match_supported_hardware(
    slave: SlaveInfo,
    selected_hw_desc: str = "",
    ecmccfg_root: Optional[Path] = None,
    limit: int = 24,
) -> Tuple[Optional[Path], str, List[str], List[str], Dict[str, List[str]], int]:
    root, descs, by_desc, _rel_files = _scan_supported_hardware(ecmccfg_root=ecmccfg_root)
    total_count = len(descs)
    preferred = selected_hw_desc.strip() or (slave.type_name or "").strip()

    if not descs:
        return root, preferred, [], [], by_desc, total_count

    preferred_norm = _normalize_hw_token(preferred)
    ranked: List[Tuple[int, int, str]] = []
    for desc in descs:
        desc_norm = _normalize_hw_token(desc)
        if not preferred_norm:
            continue
        if desc_norm == preferred_norm:
            ranked.append((0, len(desc_norm), desc))
        elif desc_norm.startswith(preferred_norm):
            ranked.append((1, len(desc_norm), desc))
        elif preferred_norm in desc_norm:
            ranked.append((2, len(desc_norm), desc))
    ranked.sort(key=lambda row: (row[0], row[1], row[2]))
    matches = [row[2] for row in ranked[:limit]]

    suggestions: List[str] = []
    if not matches and preferred_norm:
        family_match = re.match(r"([A-Z]+[0-9]{2})", preferred_norm)
        family = family_match.group(1) if family_match else preferred_norm[:4]
        if family:
            for desc in descs:
                if _normalize_hw_token(desc).startswith(family):
                    suggestions.append(desc)
            suggestions = suggestions[:limit]

    return root, preferred, matches, suggestions, by_desc, total_count


def _effective_pdo_indexes(
    mapping: PdoMapping,
    optional_pdo_indexes: Optional[List[str]] = None,
    selected_pdo_indexes: Optional[List[str]] = None,
) -> List[str]:
    if selected_pdo_indexes is not None:
        ordered = OrderedDict()
        for pdo_index in selected_pdo_indexes:
            norm = _norm_hex(pdo_index)
            if norm:
                ordered[norm] = None
        return list(ordered.keys())

    selected = [pdo for group in mapping.sm_groups for pdo in group.pdos]
    if optional_pdo_indexes:
        selected.extend(optional_pdo_indexes)
    ordered = OrderedDict()
    for pdo_index in selected:
        norm = _norm_hex(pdo_index)
        if norm:
            ordered[norm] = None
    return list(ordered.keys())


def _detect_selected_channel_groups(slave: SlaveInfo, selected_indexes: List[str]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for pdo_index in selected_indexes:
        pdo = slave.pdo_by_index.get(pdo_index)
        if pdo is None:
            continue
        first_token = ((pdo.name or "").strip().split(" ") or ["PDO"])[0]
        prefix = re.sub(r"[^A-Za-z]", "", first_token).upper() or "PDO"
        channel = _channel_from_pdo_name(pdo.name) or 1
        label = f"{prefix}{channel:02d}"
        groups.setdefault(prefix, [])
        if label not in groups[prefix]:
            groups[prefix].append(label)
    for labels in groups.values():
        labels.sort(
            key=lambda item: (
                int(re.search(r"(\d+)$", item).group(1)) if re.search(r"(\d+)$", item) else 0,
                item,
            )
        )
    return groups


def generate_engineering_cfg(
    slave: SlaveInfo,
    mapping: PdoMapping,
    mapping_index: int,
    mapping_count: int,
    optional_pdo_indexes: Optional[List[str]] = None,
    selected_pdo_indexes: Optional[List[str]] = None,
    hwtype_override: Optional[str] = None,
    selected_hw_desc: str = "",
    ecmccfg_root: Optional[Path] = None,
    esi_file: Optional[str] = None,
) -> str:
    selected_indexes = _effective_pdo_indexes(
        mapping,
        optional_pdo_indexes=optional_pdo_indexes,
        selected_pdo_indexes=selected_pdo_indexes,
    )
    channel_groups = _detect_selected_channel_groups(slave, selected_indexes)
    hwtype = _resolve_hwtype(slave, mapping_index, mapping_count, hwtype_override)

    root, hw_desc, matches, suggestions, by_desc, total_supported = _match_supported_hardware(
        slave=slave,
        selected_hw_desc=selected_hw_desc,
        ecmccfg_root=ecmccfg_root,
        limit=20,
    )

    chosen_hw_desc = hw_desc or (slave.type_name or "UNKNOWN_HW")
    drv_sid_macro = "${DRV_SID}"
    enc_sid_macro = "${ENC_SID}"

    if channel_groups.get("STM"):
        drv_ch_match = re.search(r"(\d+)$", channel_groups["STM"][0])
        drv_ch = drv_ch_match.group(1) if drv_ch_match else "01"
    elif channel_groups.get("DRV"):
        drv_ch_match = re.search(r"(\d+)$", channel_groups["DRV"][0])
        drv_ch = drv_ch_match.group(1) if drv_ch_match else "01"
    else:
        drv_ch = "01"

    if channel_groups.get("ENC"):
        enc_ch_match = re.search(r"(\d+)$", channel_groups["ENC"][0])
        enc_ch = enc_ch_match.group(1) if enc_ch_match else "01"
    else:
        enc_ch = "01"

    rows: List[str] = []
    rows.append("#- ecmc engineering starter cfg")
    rows.append(
        f"#- selected slave: type={slave.type_name or 'unknown'}, product={slave.product_code or 'unknown'}, revision={slave.revision or 'unknown'}"
    )
    rows.append(f"#- mapping: {mapping.name or 'unnamed'} ({mapping_index}/{mapping_count})")
    if esi_file:
        rows.append(f"#- source ESI file: {esi_file}")
    rows.append("#- For new/unsupported hardware, use this ESI mapping browser to generate HW/DB/UI support first.")
    rows.append("")
    rows.append("### startup.cmd")
    rows.append("require ecmccfg")
    rows.append('epicsEnvSet("IOC"                      "${IOC=IOC_TEST}")')
    rows.append(f'epicsEnvSet("ECMC_EC_HWTYPE"           "{hwtype}")')
    rows.append("")
    rows.append("#- Add slave from currently supported ecmccfg hardware:")
    rows.append(f'${{SCRIPTEXEC}} ${{ecmccfg_DIR}}addSlave.cmd,       "SLAVE_ID=${{SLAVE_ID=0}},HW_DESC={chosen_hw_desc}"')
    rows.append('epicsEnvSet("DRV_SID"                  "${ECMC_EC_SLAVE_NUM}")')
    rows.append('epicsEnvSet("ENC_SID"                  "${DRV_SID}")')
    rows.append("")
    rows.append("#- Optional: apply components")
    rows.append(
        '#-${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS=\'I_MAX_MA=1000\'"'
    )
    rows.append("")
    rows.append("#- Optional: if you generated new support in this tool, execute generated HW snippet")
    rows.append(f"#-${{SCRIPTEXEC}} ./cfg/ecmc{hwtype}.cmd")
    rows.append("")
    rows.append("#- Load axis/plc")
    rows.append(
        f'${{SCRIPTEXEC}} ${{ecmccfg_DIR}}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml, DEV=${{IOC}}, AX_NAME=M1, AXIS_ID=1, DRV_SID={drv_sid_macro}, ENC_SID={enc_sid_macro}, DRV_CH={drv_ch}, ENC_CH={enc_ch}"'
    )
    rows.append(
        f'${{SCRIPTEXEC}} ${{ecmccfg_DIR}}loadPLCFile.cmd,    "FILE=./cfg/main.plc, SAMPLE_RATE_MS=100, PLC_MACROS=\'AX_ID=1,DRV_SID={drv_sid_macro},ENC_SID={enc_sid_macro},DRV_CH={drv_ch},ENC_CH={enc_ch}\'"'
    )
    rows.append("#-${SCRIPTEXEC} ./cfg/load_extra.cmd")
    rows.append("")
    rows.append("### cfg/axis.yaml")
    rows.append("axis:")
    rows.append("  id: ${AXIS_ID=1}")
    rows.append("")
    rows.append("epics:")
    rows.append("  name: ${AX_NAME=M1}")
    rows.append("  precision: 3")
    rows.append("  description: Auto-generated engineering template")
    rows.append("  unit: mm")
    rows.append("")
    rows.append("drive:")
    rows.append("  type: 0")
    rows.append("  numerator: 10")
    rows.append("  denominator: 32768")
    rows.append("  setpoint: ec0.s$(DRV_SID).velocitySetpoint${DRV_CH=01}")
    rows.append("  control: ec0.s$(DRV_SID).driveControl${DRV_CH=01}")
    rows.append("  status: ec0.s$(DRV_SID).driveStatus${DRV_CH=01}")
    rows.append("")
    rows.append("encoder:")
    rows.append("  type: 1")
    rows.append("  bits: 32")
    rows.append("  absBits: 26")
    rows.append("  position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}")
    rows.append("  status: ec0.s$(ENC_SID).encoderStatus${ENC_CH=01}")
    rows.append("")
    rows.append("trajectory:")
    rows.append("  type: 1")
    rows.append("  axis:")
    rows.append("    velocity: 1")
    rows.append("    acceleration: 10")
    rows.append("    deceleration: 10")
    rows.append("    emergencyDeceleration: 20")
    rows.append("    jerk: 200")
    rows.append("")
    rows.append("### cfg/main.plc")
    rows.append("if(${SELF}.firstscan) {")
    rows.append("  var plc:=${SELF_ID};")
    rows.append("  ${DBG=#}println('PLC ',plc,' startup');")
    rows.append("};")
    rows.append("")
    rows.append("# Example:")
    rows.append("substitute \"DRV_CH=${DRV_CH=01}\"")
    rows.append("include \"plc_templates/drive_watchdog.plc_inc\"")
    rows.append("")
    rows.append("### cfg/load_extra.cmd")
    rows.append("#- Add any additional setup commands/includes here")
    rows.append("#-${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  \"COMP=Drive-Generic-Ctrl-Params,CH_ID=1\"")
    rows.append("")
    rows.append("### supported_hardware")
    if root is None:
        rows.append("#- ecmccfg root not found, could not scan ./hardware")
    else:
        rows.append(f"#- scanned: {root / 'hardware'}")
        rows.append(f"#- total supported HW_DESC entries: {total_supported}")
        rows.append(f"#- selected HW_DESC for addSlave: {chosen_hw_desc}")
        if matches:
            rows.append("#- best matches:")
            for desc in matches:
                paths = by_desc.get(desc, [])
                rows.append(f"#-   {desc}" if not paths else f"#-   {desc} -> {paths[0]}")
        elif suggestions:
            rows.append("#- no exact match; closest family candidates:")
            for desc in suggestions:
                paths = by_desc.get(desc, [])
                rows.append(f"#-   {desc}" if not paths else f"#-   {desc} -> {paths[0]}")
        else:
            rows.append("#- no matching HW_DESC found for this slave type")
        rows.append("#- Use ESI mapping browser generation when no supported HW_DESC exists yet.")
    rows.append("")
    rows.append("### detected_pdo_groups")
    if not channel_groups:
        rows.append("#- none")
    else:
        for prefix in sorted(channel_groups.keys()):
            rows.append(f"#- {prefix}: {', '.join(channel_groups[prefix])}")

    return "\n".join(rows) + "\n"


def print_mappings(slaves: List[SlaveInfo]) -> None:
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
                print(f"          optional PDOs listed: {optional_count}")
        if slave.coe_init_cmds:
            print(f"     CoE InitCmd startup SDOs: {len(slave.coe_init_cmds)}")


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
        "REAL": "F32",
        "REAL32": "F32",
        "FLOAT": "F32",
        "SINGLE": "F32",
        "LREAL": "F64",
        "REAL64": "F64",
        "DOUBLE": "F64",
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


def _replace_tokens(text: str, replacements: Dict[str, str]) -> str:
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


def _is_single_channel_slave(slave: Optional[SlaveInfo]) -> bool:
    if slave is None:
        return False
    text = f"{slave.display_name} {slave.type_name}".lower()
    return bool(re.search(r"\b1\s*ch\.?\b", text))


def _pdo_type_and_prefix(
    pdo: PdoInfo, slave: Optional[SlaveInfo] = None, legacy_naming: bool = False
) -> Tuple[str, str]:
    words = pdo.name.split()
    if not words:
        return ("Dev", "Dev")

    raw = words[0]
    if legacy_naming:
        pdo_map = LEGACY_PDO_IN_MAP if pdo.direction == "rx" else LEGACY_PDO_OUT_MAP
    else:
        pdo_map = PDO_IN_MAP if pdo.direction == "rx" else PDO_OUT_MAP
    mapped = _replace_tokens(raw, pdo_map)

    channel_no: Optional[int] = None
    for idx in range(len(words) - 1):
        if words[idx].lower() == "channel" and words[idx + 1].isdigit():
            channel_no = int(words[idx + 1])
            break

    if channel_no is None and raw.upper() in DEV_NEEDS_INDEX:
        channel_no = 1

    # Some single-channel terminals (for example EL3001) have PDO names
    # without explicit "Channel 1" text; force *_01 style prefixes.
    if (
        not legacy_naming
        and channel_no is None
        and mapped in SINGLE_CH_NEEDS_INDEX
        and _is_single_channel_slave(slave)
    ):
        channel_no = 1

    prefix = mapped if channel_no is None else f"{mapped}{channel_no:02d}"
    return (mapped, prefix)


def _entry_record_name(
    pdo: PdoInfo, entry_name: str, slave: Optional[SlaveInfo] = None, legacy_naming: bool = False
) -> str:
    dev, prefix = _pdo_type_and_prefix(pdo, slave=slave, legacy_naming=legacy_naming)
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


def _channel_from_pdo_name(pdo_name: str) -> Optional[int]:
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
    slave: SlaveInfo, mapping_index: int, mapping_count: int, hwtype_override: Optional[str] = None
) -> str:
    if hwtype_override and hwtype_override.strip():
        return _snake(hwtype_override)
    return _build_hwtype(slave, mapping_index, mapping_count)


def _unique_symbol(candidate: str, used: Dict[str, int]) -> str:
    count = used.get(candidate, 0) + 1
    used[candidate] = count
    if count == 1:
        return candidate
    return f"{candidate}_{count:02d}"


def _symbol_with_direction(base_name: str, direction: str, used: Dict[str, int]) -> str:
    del direction
    return _unique_symbol(_snake(base_name), used)


def _entry_symbol(
    pdo: PdoInfo,
    entry: PdoEntry,
    used: Dict[str, int],
    slave: Optional[SlaveInfo] = None,
    legacy_naming: bool = False,
) -> str:
    if legacy_naming:
        base_name = entry.raw_name or entry.resolved_name or f"{entry.index}_{entry.subindex}"
    else:
        base_name = entry.resolved_name or entry.raw_name or f"{entry.index}_{entry.subindex}"
    record_name = _entry_record_name(pdo, base_name, slave=slave, legacy_naming=legacy_naming)
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
    used: Dict[str, int],
    slave: Optional[SlaveInfo] = None,
    legacy_naming: bool = False,
) -> str:
    root = _packed_root_name(pdo)
    _dev, prefix = _pdo_type_and_prefix(pdo, slave=slave, legacy_naming=legacy_naming)
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


def _build_packed_bit_comment(chunk: List[PdoEntry]) -> str:
    # Keep placeholders ("gap") so merged bit layout is explicit and reviewable.
    segments: List[Tuple[int, int, str]] = []
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


def _mapping_pdo_set(mapping: PdoMapping) -> Set[str]:
    selected: Set[str] = set()
    for group in mapping.sm_groups:
        for pdo_index in group.pdos:
            selected.add(pdo_index)
    return selected


def optional_pdos_for_mapping(slave: SlaveInfo, mapping: PdoMapping) -> List[PdoInfo]:
    selected = _mapping_pdo_set(mapping)
    optional = [pdo for idx, pdo in slave.pdo_by_index.items() if idx not in selected]
    optional.sort(key=lambda p: (_parse_hexish(p.index) is None, _parse_hexish(p.index) or 0, p.direction, p.name))
    return optional


def _pdo_choice_sort_key(choice: PdoChoice) -> Tuple[int, int, str, str]:
    idx_num = _parse_hexish(choice.pdo.index)
    return (
        1 if idx_num is None else 0,
        idx_num if idx_num is not None else 0,
        0 if choice.is_default else 1,
        choice.pdo.name,
    )


def _is_non_decreasing_pdo_order(indexes: List[str]) -> bool:
    parsed: List[int] = []
    for idx in indexes:
        idx_num = _parse_hexish(idx)
        if idx_num is None:
            return False
        parsed.append(idx_num)
    return all(parsed[i] <= parsed[i + 1] for i in range(len(parsed) - 1))


def pdo_choices_for_mapping(slave: SlaveInfo, mapping: PdoMapping) -> List[PdoChoice]:
    default_choices: List[PdoChoice] = []
    seen: Set[str] = set()

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

    optional_choices: List[PdoChoice] = []
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


def _pdo_conflict_reason(slave: SlaveInfo, candidate_index: str, selected_indexes: Set[str]) -> str:
    candidate = slave.pdo_by_index.get(candidate_index)
    if candidate is None:
        return "missing in ESI PDO list"

    for selected_index in selected_indexes:
        if selected_index == candidate_index:
            continue
        selected = slave.pdo_by_index.get(selected_index)
        if selected is None:
            continue

        if selected.direction != candidate.direction:
            continue

        if candidate_index in selected.excludes:
            return f"excluded by {selected.index} ({selected.name or 'unnamed'})"
        if selected_index in candidate.excludes:
            return f"excludes {selected.index} ({selected.name or 'unnamed'})"

    return ""


def _build_pdo_conflict_context(
    slave: SlaveInfo, selected_indexes: Set[str]
) -> Tuple[Dict[str, Set[str]], Dict[str, Dict[str, str]]]:
    selected_by_direction: Dict[str, Set[str]] = {}
    excluded_by_direction: Dict[str, Dict[str, str]] = {}
    for selected_index in selected_indexes:
        selected = slave.pdo_by_index.get(selected_index)
        if selected is None:
            continue
        direction = selected.direction
        selected_by_direction.setdefault(direction, set()).add(selected_index)
        ex_map = excluded_by_direction.setdefault(direction, {})
        for excluded_idx in selected.excludes:
            if excluded_idx and excluded_idx not in ex_map:
                ex_map[excluded_idx] = selected_index
    return selected_by_direction, excluded_by_direction


def _pdo_conflict_reason_with_context(
    slave: SlaveInfo,
    candidate_index: str,
    selected_indexes: Set[str],
    selected_by_direction: Dict[str, Set[str]],
    excluded_by_direction: Dict[str, Dict[str, str]],
) -> str:
    candidate = slave.pdo_by_index.get(candidate_index)
    if candidate is None:
        return "missing in ESI PDO list"

    selected_dir = selected_by_direction.get(candidate.direction, set())
    excluded_by = excluded_by_direction.get(candidate.direction, {}).get(candidate_index)
    if excluded_by and excluded_by in selected_indexes:
        selected = slave.pdo_by_index.get(excluded_by)
        if selected is not None:
            return f"excluded by {selected.index} ({selected.name or 'unnamed'})"
        return f"excluded by {excluded_by}"

    for excluded_idx in candidate.excludes:
        if excluded_idx not in selected_dir:
            continue
        selected = slave.pdo_by_index.get(excluded_idx)
        if selected is not None:
            return f"excludes {selected.index} ({selected.name or 'unnamed'})"
        return f"excludes {excluded_idx}"

    return ""


def pdo_selectable_for_mapping(
    slave: SlaveInfo,
    mapping: PdoMapping,
    candidate_index: str,
    checked_selected_indexes: Optional[Set[str]] = None,
    conflict_context: Optional[Tuple[Dict[str, Set[str]], Dict[str, Dict[str, str]]]] = None,
) -> Tuple[bool, str]:
    if checked_selected_indexes is None:
        selected = _mapping_pdo_set(mapping)
    else:
        selected = set(checked_selected_indexes)
    selected.discard(candidate_index)
    if conflict_context is None:
        conflict_context = _build_pdo_conflict_context(slave, selected)
    reason = _pdo_conflict_reason_with_context(
        slave,
        candidate_index,
        selected,
        conflict_context[0],
        conflict_context[1],
    )
    if reason:
        return False, reason
    return True, ""


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


def _select_dc_mode(slave: SlaveInfo) -> Optional[DcModeInfo]:
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
    optional_pdo_indexes: Optional[List[str]] = None,
    selected_pdo_indexes: Optional[List[str]] = None,
    hwtype_override: Optional[str] = None,
    generated_entries: Optional[List[GeneratedEntry]] = None,
    include_dc: bool = True,
    include_coe_initcmd: bool = False,
    legacy_naming: bool = True,
    esi_file: Optional[str] = None,
) -> str:
    rows: List[str] = []
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

    if include_coe_initcmd and slave.coe_init_cmds:
        rows.append("#- CoE InitCmd startup SDOs from ESI (Mailbox/CoE/InitCmd)")
        rows.append("#- NOTE: ESI Transition qualifiers are informational only and kept as comments.")
        rows.append("#- NOTE: ecmc startup SDO commands are always applied in transition PREOP -> OP.")
        for idx, init_cmd in enumerate(slave.coe_init_cmds, start=1):
            meta = [f"Transition={init_cmd.transition or '?'}"]
            if init_cmd.fixed:
                meta.append("Fixed=1")
            if init_cmd.complete_access:
                meta.append("CompleteAccess=1")
            if init_cmd.overwritten_by_module:
                meta.append("OverwrittenByModule=1")
            if init_cmd.data_adapt_automatically:
                meta.append("AdaptAutomatically=1")
            rows.append(f"#- InitCmd[{idx:02d}] " + ", ".join(meta))
            if init_cmd.comment:
                rows.append(f"#-   Comment: {init_cmd.comment}")

            if not init_cmd.data_hex:
                rows.append(
                    f"#- WARNING: skipped InitCmd[{idx:02d}] {init_cmd.index}:{init_cmd.subindex} (empty/non-hex data)"
                )
                continue
            if init_cmd.byte_size > 4:
                rows.append(
                    f"#- WARNING: skipped InitCmd[{idx:02d}] {init_cmd.index}:{init_cmd.subindex} "
                    f"(byteSize={init_cmd.byte_size} > 4, EcAddSdo supports up to 4 bytes)"
                )
                continue

            value_int = _le_hex_to_int(init_cmd.data_hex)
            rows.append(
                "ecmcConfigOrDie \"Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},"
                f"{init_cmd.index},{init_cmd.subindex},{value_int},{init_cmd.byte_size})\""
            )
        rows.append("")

    mapping_pdos = _mapping_pdo_set(mapping)
    mapping_sm_by_pdo: Dict[str, str] = {}
    for group in mapping.sm_groups:
        for pdo_index in group.pdos:
            if pdo_index not in mapping_sm_by_pdo:
                mapping_sm_by_pdo[pdo_index] = group.sm_no

    used_symbols: Dict[str, int] = {}
    already_added: Set[str] = set()

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
                run_entries: List[PdoEntry] = []
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
                        chunk: List[PdoEntry] = []
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
                                symbol = _entry_symbol(pdo, single, used_symbols, slave=slave, legacy_naming=legacy_naming)
                                dt = _entry_to_ecmc_dt(single)
                                desc = single.resolved_name or single.raw_name or single.index
                                _emit_entry_line(single.index, single.subindex, dt, symbol, desc, packed=False)
                            continue

                        packed_group_idx += 1
                        packed_dt = "U8" if bits <= 8 else "U16"
                        packed_entry = chunk_non_padding[0]
                        packed_symbol = _packed_symbol_name(
                            pdo,
                            packed_group_idx,
                            used_symbols,
                            slave=slave,
                            legacy_naming=legacy_naming,
                        )
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
                        if bit_comment:
                            for bit_line in _bit_comment_lines(bit_comment):
                                rows.append(f"#- {packed_symbol} {bit_line}")

                    entry_i = run_j
                    continue

            symbol = _entry_symbol(pdo, entry, used_symbols, slave=slave, legacy_naming=legacy_naming)
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
        ordered_selected: List[str] = []
        seen_selected: Set[str] = set()
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


def _bit_comment_lines(bit_comment: str) -> List[str]:
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


def _entry_to_asyn_dtyp(entry: GeneratedEntry) -> str:
    if entry.dt in {"F32", "F64"}:
        return "asynFloat64"
    return "asynInt32"


def generate_substitutions(
    slave: SlaveInfo,
    mapping: PdoMapping,
    mapping_index: int,
    mapping_count: int,
    optional_pdo_indexes: Optional[List[str]] = None,
    selected_pdo_indexes: Optional[List[str]] = None,
    hwtype_override: Optional[str] = None,
    include_dc: bool = True,
    include_coe_initcmd: bool = False,
    legacy_naming: bool = True,
    esi_file: Optional[str] = None,
) -> str:
    collected: List[GeneratedEntry] = []
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
        include_coe_initcmd=include_coe_initcmd,
        legacy_naming=legacy_naming,
        esi_file=esi_file,
    )

    groups: Dict[str, List[GeneratedEntry]] = {"ai": [], "ao": [], "bi": [], "bo": [], "mbbi": [], "mbbo": []}
    for entry in collected:
        groups[_entry_to_subst_group(entry)].append(entry)

    rows: List[str] = []
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

    def _add_file_block_ai_ao(template: str, entries: List[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append(f'file "{template}" {{')
        rows.append("    pattern { REC_NAME, DESC , SRC_NAME, DTYP}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            rows.append(
                f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "{entry.source_name}", "{_entry_to_asyn_dtyp(entry)}"}}'
            )
        rows.append("}")
        rows.append("")

    def _add_file_block_bi_bo(template: str, entries: List[GeneratedEntry]) -> None:
        if not entries:
            return
        rows.append(f'file "{template}" {{')
        rows.append("    pattern { REC_NAME, DESC , SRC_NAME}")
        for entry in entries:
            rec_name = entry.source_name.replace("_", "-")
            rows.append(f'        {{"{_esc_subst(rec_name)}", "{_esc_subst(entry.desc)}", "{entry.source_name}"}}')
        rows.append("}")
        rows.append("")

    def _add_file_block_mbbi(entries: List[GeneratedEntry]) -> None:
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

    def _add_file_block_mbbo(entries: List[GeneratedEntry]) -> None:
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


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _panel_row_label(entry: GeneratedEntry, row_no: int) -> str:
    rec_name = entry.source_name.replace("_", "-")
    head = rec_name.split("-")[0] if rec_name else ""
    head_match = re.match(r"([A-Za-z]+)([0-9]{0,2})", head)
    head_type = head_match.group(1).upper() if head_match else ""
    type_map = {"DRV": "STM", "FB": "ENC"}
    mapped_type = type_map.get(head_type, head_type)

    base = (entry.desc or "").strip()
    if not base:
        parts = [part for part in rec_name.split("-") if part]
        if len(parts) >= 2:
            base = f"{parts[-2]}-{parts[-1]}"
        elif parts:
            base = parts[-1]
    if mapped_type and base and not base.upper().startswith(mapped_type):
        base = f"{mapped_type} {base}"
    base = re.sub(r"\s+", " ", base).strip(" -:_")
    if not base:
        base = f"PV {row_no:02d}"
    return base[:16]


def _panel_group_id(entry: GeneratedEntry) -> str:
    rec_name = entry.source_name.replace("_", "-")
    head = rec_name.split("-")[0] if rec_name else ""
    match = re.match(r"([A-Za-z]+)([0-9]{0,2})", head)
    if match:
        channel_id = match.group(2) or ""
        if channel_id:
            channel_num = _parse_int(channel_id)
            if channel_num is not None:
                return f"CH{channel_num:02d}"
            return f"CH{channel_id}"
    if head:
        return "DEV"
    return "DEV"


def _panel_group_title(group_id: str) -> str:
    return group_id


def _panel_group_sort_key(group_id: str, original_order: int) -> Tuple[int, int, int, str]:
    match = re.match(r"CH([0-9]{1,2})$", group_id)
    if not match:
        return (1, 999, original_order, group_id)

    group_num = _parse_int(match.group(1))
    if group_num is None:
        return (1, 999, original_order, group_id)
    return (0, group_num, original_order, group_id)


def _panel_entry_uses_byte(entry: GeneratedEntry) -> bool:
    if entry.packed:
        return True
    return entry.dt.startswith("B")


def _panel_byte_range(entry: GeneratedEntry) -> Tuple[int, int]:
    if entry.packed:
        if entry.dt == "U16":
            return (0, 15)
        return (0, 7)
    if entry.dt.startswith("B"):
        bit_count = _parse_int(entry.dt[1:]) or 1
        if bit_count < 1:
            bit_count = 1
        if bit_count > 16:
            bit_count = 16
        return (0, bit_count - 1)
    return (0, 7)


def generate_caqtdm_panel(
    slave: SlaveInfo,
    mapping: PdoMapping,
    mapping_index: int,
    mapping_count: int,
    optional_pdo_indexes: Optional[List[str]] = None,
    selected_pdo_indexes: Optional[List[str]] = None,
    hwtype_override: Optional[str] = None,
    legacy_naming: bool = True,
    esi_file: Optional[str] = None,
) -> str:
    collected: List[GeneratedEntry] = []
    _ = generate_hw_snippet(
        slave=slave,
        mapping=mapping,
        mapping_index=mapping_index,
        mapping_count=mapping_count,
        optional_pdo_indexes=optional_pdo_indexes,
        selected_pdo_indexes=selected_pdo_indexes,
        hwtype_override=hwtype_override,
        generated_entries=collected,
        include_dc=False,
        include_coe_initcmd=False,
        legacy_naming=legacy_naming,
        esi_file=esi_file,
    )

    grouped: OrderedDict[str, List[GeneratedEntry]] = OrderedDict()
    for entry in collected:
        group_id = _panel_group_id(entry)
        grouped.setdefault(group_id, []).append(entry)
    if not grouped:
        grouped["GEN"] = []
    original_pos = {group_id: idx for idx, group_id in enumerate(grouped.keys(), start=1)}
    ordered_group_items = sorted(
        grouped.items(),
        key=lambda kv: _panel_group_sort_key(kv[0], original_pos.get(kv[0], 9999)),
    )

    panel_w = 100
    panel_h = 400
    tab_x = 1
    tab_y = 118
    tab_w = 98
    tab_h = 281
    row_y0 = 6
    row_step = 28
    max_rows_per_tab = max(1, (tab_h - 38) // row_step)

    hwtype = _resolve_hwtype(slave, mapping_index, mapping_count, hwtype_override)
    title = _xml_escape(slave.type_name or "ecmcSlave")
    source_file = _xml_escape(esi_file or "")
    has_byte_widget = any(
        _panel_entry_uses_byte(entry)
        for _gid, entries in ordered_group_items
        for entry in entries[:max_rows_per_tab]
    )

    rows: List[str] = []
    rows.append('<?xml version="1.0" encoding="UTF-8"?>')
    rows.append("<ui version=\"4.0\">")
    rows.append(" <class>Form</class>")
    rows.append(" <widget class=\"QWidget\" name=\"Form\">")
    rows.append("  <property name=\"geometry\">")
    rows.append("   <rect>")
    rows.append("    <x>0</x>")
    rows.append("    <y>0</y>")
    rows.append(f"    <width>{panel_w}</width>")
    rows.append(f"    <height>{panel_h}</height>")
    rows.append("   </rect>")
    rows.append("  </property>")
    rows.append("  <property name=\"windowTitle\">")
    rows.append(f"   <string>{title}</string>")
    rows.append("  </property>")
    rows.append("  <property name=\"minimumSize\">")
    rows.append("   <size>")
    rows.append(f"    <width>{panel_w}</width>")
    rows.append(f"    <height>{panel_h}</height>")
    rows.append("   </size>")
    rows.append("  </property>")
    rows.append("  <property name=\"maximumSize\">")
    rows.append("   <size>")
    rows.append(f"    <width>{panel_w}</width>")
    rows.append(f"    <height>{panel_h}</height>")
    rows.append("   </size>")
    rows.append("  </property>")
    rows.append("  <widget class=\"caInclude\" name=\"cainclude\">")
    rows.append("   <property name=\"geometry\">")
    rows.append("    <rect>")
    rows.append("     <x>0</x>")
    rows.append("     <y>0</y>")
    rows.append(f"     <width>{panel_w}</width>")
    rows.append(f"     <height>{panel_h}</height>")
    rows.append("    </rect>")
    rows.append("   </property>")
    rows.append("   <property name=\"macro\">")
    rows.append("    <string>IOC=$(IOC),MasterID=$(MasterID),SlaveID=$(SlaveID)</string>")
    rows.append("   </property>")
    rows.append("   <property name=\"filename\" stdset=\"0\">")
    rows.append("    <string notr=\"true\">ecmcE_slave_frame_S.ui</string>")
    rows.append("   </property>")
    rows.append("  </widget>")

    rows.append(
        f"  <!-- auto-generated for {title}, mapping M{mapping_index:02d}/{mapping_count}, hwtype={_xml_escape(hwtype)} -->"
    )
    if source_file:
        rows.append(f"  <!-- source ESI file: {source_file} -->")

    rows.append("  <widget class=\"QTabWidget\" name=\"tabwidget_auto\">")
    rows.append("   <property name=\"geometry\">")
    rows.append("    <rect>")
    rows.append(f"     <x>{tab_x}</x>")
    rows.append(f"     <y>{tab_y}</y>")
    rows.append(f"     <width>{tab_w}</width>")
    rows.append(f"     <height>{tab_h}</height>")
    rows.append("    </rect>")
    rows.append("   </property>")
    rows.append("   <property name=\"currentIndex\">")
    rows.append("    <number>0</number>")
    rows.append("   </property>")

    for tab_idx, (group_id, entries) in enumerate(ordered_group_items, start=1):
        tab_title = _xml_escape(_panel_group_title(group_id))
        shown = entries[:max_rows_per_tab]
        hidden_count = max(0, len(entries) - len(shown))

        rows.append(f"   <widget class=\"QWidget\" name=\"tabPage_auto_{tab_idx:02d}\">")
        rows.append("    <attribute name=\"title\">")
        rows.append(f"     <string>{tab_title}</string>")
        rows.append("    </attribute>")

        for row_no, entry in enumerate(shown, start=1):
            rec_name = entry.source_name.replace("_", "-")
            channel = _xml_escape(f"$(IOC):m$(MasterID)s$(SlaveID)-{rec_name}")
            label_text = _xml_escape(_panel_row_label(entry, row_no))
            tooltip_text = _xml_escape((entry.desc or rec_name).strip())
            y = row_y0 + (row_no - 1) * row_step

            is_byte = _panel_entry_uses_byte(entry)
            label_w = 66 if is_byte else 54
            value_x = 70 if is_byte else 58
            value_w = 24 if is_byte else 36
            value_h = 26 if is_byte else 16

            rows.append(f"    <widget class=\"caLabel\" name=\"calabel_auto_{tab_idx:02d}_{row_no:02d}\">")
            rows.append("     <property name=\"geometry\">")
            rows.append("      <rect>")
            rows.append("       <x>2</x>")
            rows.append(f"       <y>{y}</y>")
            rows.append(f"       <width>{label_w}</width>")
            rows.append("       <height>16</height>")
            rows.append("      </rect>")
            rows.append("     </property>")
            rows.append("     <property name=\"text\">")
            rows.append(f"      <string>{label_text}</string>")
            rows.append("     </property>")
            rows.append("     <property name=\"toolTip\">")
            rows.append(f"      <string>{tooltip_text}</string>")
            rows.append("     </property>")
            rows.append("    </widget>")

            if is_byte:
                start_bit, end_bit = _panel_byte_range(entry)
                rows.append(f"    <widget class=\"caByte\" name=\"cabyte_auto_{tab_idx:02d}_{row_no:02d}\">")
                rows.append("     <property name=\"geometry\">")
                rows.append("      <rect>")
                rows.append(f"       <x>{value_x}</x>")
                rows.append(f"       <y>{y - 4}</y>")
                rows.append(f"       <width>{value_w}</width>")
                rows.append(f"       <height>{value_h}</height>")
                rows.append("      </rect>")
                rows.append("     </property>")
                rows.append("     <property name=\"toolTip\">")
                rows.append(f"      <string>{tooltip_text}</string>")
                rows.append("     </property>")
                rows.append("     <property name=\"channel\" stdset=\"0\">")
                rows.append(f"      <string notr=\"true\">{channel}</string>")
                rows.append("     </property>")
                rows.append("     <property name=\"direction\">")
                rows.append("      <enum>caByte::Up</enum>")
                rows.append("     </property>")
                rows.append("     <property name=\"startBit\">")
                rows.append(f"      <number>{start_bit}</number>")
                rows.append("     </property>")
                rows.append("     <property name=\"endBit\">")
                rows.append(f"      <number>{end_bit}</number>")
                rows.append("     </property>")
                rows.append("     <property name=\"colorMode\">")
                rows.append("      <enum>caByte::Static</enum>")
                rows.append("     </property>")
                rows.append("     <property name=\"foreground\" stdset=\"0\">")
                rows.append("      <color>")
                rows.append("       <red>0</red>")
                rows.append("       <green>85</green>")
                rows.append("       <blue>0</blue>")
                rows.append("      </color>")
                rows.append("     </property>")
                rows.append("    </widget>")
            else:
                rows.append(f"    <widget class=\"caLineEdit\" name=\"calineedit_auto_{tab_idx:02d}_{row_no:02d}\">")
                rows.append("     <property name=\"geometry\">")
                rows.append("      <rect>")
                rows.append(f"       <x>{value_x}</x>")
                rows.append(f"       <y>{y}</y>")
                rows.append(f"       <width>{value_w}</width>")
                rows.append("       <height>16</height>")
                rows.append("      </rect>")
                rows.append("     </property>")
                rows.append("     <property name=\"toolTip\">")
                rows.append(f"      <string>{tooltip_text}</string>")
                rows.append("     </property>")
                rows.append("     <property name=\"alignment\">")
                rows.append("      <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>")
                rows.append("     </property>")
                rows.append("     <property name=\"channel\" stdset=\"0\">")
                rows.append(f"      <string notr=\"true\">{channel}</string>")
                rows.append("     </property>")
                rows.append("    </widget>")

        if hidden_count > 0:
            hidden_y = row_y0 + len(shown) * row_step
            rows.append(f"    <widget class=\"caLabel\" name=\"calabel_auto_more_{tab_idx:02d}\">")
            rows.append("     <property name=\"geometry\">")
            rows.append("      <rect>")
            rows.append("       <x>2</x>")
            rows.append(f"       <y>{hidden_y}</y>")
            rows.append("       <width>92</width>")
            rows.append("       <height>16</height>")
            rows.append("      </rect>")
            rows.append("     </property>")
            rows.append("     <property name=\"text\">")
            rows.append(f"      <string>+{hidden_count} more PVs</string>")
            rows.append("     </property>")
            rows.append("    </widget>")

        rows.append("   </widget>")

    rows.append("  </widget>")

    rows.append(" </widget>")
    rows.append(" <customwidgets>")
    rows.append("  <customwidget>")
    rows.append("   <class>caLabel</class>")
    rows.append("   <extends>QLabel</extends>")
    rows.append("   <header>caLabel</header>")
    rows.append("  </customwidget>")
    rows.append("  <customwidget>")
    rows.append("   <class>caInclude</class>")
    rows.append("   <extends>QWidget</extends>")
    rows.append("   <header>caInclude</header>")
    rows.append("  </customwidget>")
    rows.append("  <customwidget>")
    rows.append("   <class>caLineEdit</class>")
    rows.append("   <extends>QLineEdit</extends>")
    rows.append("   <header>caLineEdit</header>")
    rows.append("  </customwidget>")
    if has_byte_widget:
        rows.append("  <customwidget>")
        rows.append("   <class>caByte</class>")
        rows.append("   <extends>QWidget</extends>")
        rows.append("   <header>caByte</header>")
        rows.append("  </customwidget>")
    rows.append(" </customwidgets>")
    rows.append(" <resources/>")
    rows.append(" <connections/>")
    rows.append("</ui>")

    return "\n".join(rows).rstrip() + "\n"


def _ui_widget_rect(widget: ET.Element) -> Optional[Tuple[int, int, int, int]]:
    rect = widget.find("./property[@name='geometry']/rect")
    if rect is None:
        return None
    x = _parse_int(_text(rect.find("x")))
    y = _parse_int(_text(rect.find("y")))
    w = _parse_int(_text(rect.find("width")))
    h = _parse_int(_text(rect.find("height")))
    if x is None or y is None or w is None or h is None:
        return None
    return (x, y, w, h)


def _ui_widget_string_property(widget: ET.Element, prop_name: str) -> str:
    prop = widget.find(f"./property[@name='{prop_name}']")
    if prop is None:
        return ""
    return _text(prop.find("string"))


def parse_generated_panel_preview_items(
    panel_ui: str,
) -> Tuple[
    int,
    int,
    Optional[Tuple[int, int, int, int]],
    List[Tuple[str, List[Tuple[str, Tuple[int, int, int, int], str]]]],
]:
    root = ET.fromstring(panel_ui)
    form_widget = root.find("./widget[@name='Form']")
    panel_w = 100
    panel_h = 400
    if form_widget is not None:
        form_rect = _ui_widget_rect(form_widget)
        if form_rect is not None:
            _x, _y, panel_w, panel_h = form_rect

    def _collect_items(
        widget_iter,
        x_off: int = 0,
        y_off: int = 0,
    ) -> List[Tuple[str, Tuple[int, int, int, int], str]]:
        out: List[Tuple[str, Tuple[int, int, int, int], str]] = []
        for widget in widget_iter:
            cls = widget.get("class", "")
            name = widget.get("name", "")
            if not (
                name.startswith("calabel_auto")
                or name.startswith("calineedit_auto")
                or name.startswith("cabyte_auto")
            ):
                continue
            rect = _ui_widget_rect(widget)
            if rect is None:
                continue
            x, y, w, h = rect
            abs_rect = (x + x_off, y + y_off, w, h)
            if cls == "caLabel":
                text = _ui_widget_string_property(widget, "text")
                out.append(("label", abs_rect, text))
            elif cls == "caLineEdit":
                channel = _ui_widget_string_property(widget, "channel")
                out.append(("lineedit", abs_rect, channel))
            elif cls == "caByte":
                start_bit = _parse_int(_text(widget.find("./property[@name='startBit']/number")))
                end_bit = _parse_int(_text(widget.find("./property[@name='endBit']/number")))
                bit_text = ""
                if start_bit is not None and end_bit is not None:
                    bit_text = f"B{start_bit}..B{end_bit}"
                out.append(("byte", abs_rect, bit_text))
        return out

    tabs: List[Tuple[str, List[Tuple[str, Tuple[int, int, int, int], str]]]] = []
    tab_rect_out: Optional[Tuple[int, int, int, int]] = None
    tab_widget = root.find(".//widget[@name='tabwidget_auto']")
    if tab_widget is not None:
        tab_rect = _ui_widget_rect(tab_widget)
        if tab_rect is not None:
            tab_rect_out = tab_rect
            tx, ty, tw, th = tab_rect
            tab_pages = [node for node in tab_widget.findall("./widget") if node.get("class", "") == "QWidget"]
            if tab_pages:
                for page in tab_pages:
                    tab_title = _text(page.find("./attribute[@name='title']/string")) or "Tab"
                    page_items = _collect_items(page.findall(".//widget"), x_off=tx + 2, y_off=ty + 24)
                    tabs.append((tab_title, page_items))
            else:
                tabs.append(("Panel", _collect_items(root.findall(".//widget"))))
        else:
            tabs.append(("Panel", _collect_items(root.findall(".//widget"))))
    else:
        tabs.append(("Panel", _collect_items(root.findall(".//widget"))))

    return panel_w, panel_h, tab_rect_out, tabs


def mapping_details_text(slave: SlaveInfo, mapping: PdoMapping) -> str:
    lines: List[str] = []
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
        lines.append("")

    optional = optional_pdos_for_mapping(slave, mapping)
    optional_count = len(optional)
    non_selectable_count = 0
    mapping_selected = _mapping_pdo_set(mapping)
    mapping_conflict_context = _build_pdo_conflict_context(slave, mapping_selected)
    for pdo in optional:
        selectable, _reason = pdo_selectable_for_mapping(
            slave,
            mapping,
            pdo.index,
            checked_selected_indexes=mapping_selected,
            conflict_context=mapping_conflict_context,
        )
        if not selectable:
            non_selectable_count += 1
    lines.append(f"Optional PDOs listed: {optional_count}")
    if non_selectable_count:
        lines.append(f"Optional PDOs blocked by ESI excludes: {non_selectable_count}")
    lines.append("")

    lines.append(f"CoE InitCmd startup SDOs: {len(slave.coe_init_cmds)}")
    if slave.coe_init_cmds:
        lines.append("  (select entries in the CoE InitCmd list for details)")
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


def pdo_choice_details_text(choice: PdoChoice) -> str:
    pdo = choice.pdo
    lines: List[str] = []
    lines.append(f"PDO: {pdo.index}")
    lines.append(f"Name: {pdo.name or '(unnamed)'}")
    lines.append(f"Type: {'default' if choice.is_default else 'optional'}")
    lines.append(f"Direction: {pdo.direction.upper()}")
    lines.append(f"SM: {choice.sm_no}")
    if pdo.excludes:
        excludes = ", ".join(sorted(pdo.excludes, key=lambda idx: (_parse_hexish(idx) is None, _parse_hexish(idx) or 0, idx)))
        lines.append(f"Exclude (ESI): {excludes}")
    else:
        lines.append("Exclude (ESI): none")
    return "\n".join(lines).rstrip() + "\n"


def coe_initcmd_summary_text(init_cmd: CoeInitCmdInfo) -> str:
    transition = init_cmd.transition or "?"
    if init_cmd.byte_size <= 0:
        data = "data=?"
    else:
        data = f"data={init_cmd.data_hex or '??'}"
    return f"{transition} {init_cmd.index}:{init_cmd.subindex} {data} ({init_cmd.byte_size}B)"


def coe_initcmd_details_text(init_cmd: CoeInitCmdInfo) -> str:
    lines: List[str] = []
    lines.append("CoE InitCmd")
    lines.append(f"Transition: {init_cmd.transition or '(none)'}")
    lines.append(f"Index/Sub: {init_cmd.index}:{init_cmd.subindex}")
    lines.append(f"Byte size: {init_cmd.byte_size}")
    lines.append(f"Data hex: {init_cmd.data_hex or '(none)'}")
    lines.append(f"Data bytes: {init_cmd.data_bytes or '(none)'}")
    lines.append(f"Fixed: {'yes' if init_cmd.fixed else 'no'}")
    lines.append(f"CompleteAccess: {'yes' if init_cmd.complete_access else 'no'}")
    lines.append(f"OverwrittenByModule: {'yes' if init_cmd.overwritten_by_module else 'no'}")
    lines.append(f"AdaptAutomatically: {'yes' if init_cmd.data_adapt_automatically else 'no'}")
    lines.append("Note: ecmc startup SDO commands are always applied in transition PREOP -> OP.")
    if init_cmd.comment:
        lines.append(f"Comment: {init_cmd.comment}")
    if init_cmd.byte_size <= 4 and init_cmd.data_hex:
        value_int = _le_hex_to_int(init_cmd.data_hex)
        lines.append(
            "ecmc line: "
            f"Cfg.EcAddSdo(${{ECMC_EC_SLAVE_NUM}},{init_cmd.index},{init_cmd.subindex},{value_int},{init_cmd.byte_size})"
        )
    else:
        lines.append("ecmc line: skipped (EcAddSdo supports up to 4 bytes)")
    return "\n".join(lines).rstrip() + "\n"


def coe_initcmd_is_representable(init_cmd: CoeInitCmdInfo) -> bool:
    return bool(init_cmd.data_hex) and 0 < init_cmd.byte_size <= 4


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
            self._setup_tree_style()

            self.slaves: List[SlaveInfo] = []
            self.current_mappings: List[PdoMapping] = []
            self.current_pdo_choices: List[PdoChoice] = []
            self.optional_pdo_vars: List[tk.BooleanVar] = []
            self.pdo_row_items: List[Dict[str, object]] = []
            self.pdo_item_to_row: Dict[str, int] = {}
            self.current_coe_item_indexes: List[int] = []
            self.generated_snippet = ""
            self.generated_substitutions = ""
            self.generated_panel = ""
            self.generated_popup: Optional[tk.Toplevel] = None
            self.generated_hw_text: Optional[tk.Text] = None
            self.generated_db_text: Optional[tk.Text] = None
            self.generated_panel_text: Optional[tk.Text] = None
            self.generated_panel_preview_canvas: Optional[tk.Canvas] = None
            self.generated_edit_var: Optional[tk.BooleanVar] = None
            self._is_busy = False
            self._activity_active = False
            self._activity_status_before = ""
            self._pending_pdo_select_after_id: Optional[str] = None
            self.compact_status_labels = True
            self.custom_hwtype_override = ""
            self.exclude_dc_clock = False
            self.include_coe_initcmd = False
            self.legacy_naming = True
            self._mapping_overview_text = ""
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

            coe_header = ttk.Frame(right_frame)
            coe_header.pack(fill=tk.X, pady=(8, 4))
            ttk.Label(coe_header, text="CoE InitCmd startup SDOs").pack(side=tk.LEFT)
            self.coe_only_representable_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                coe_header,
                text="Only <=4B",
                variable=self.coe_only_representable_var,
                command=self._on_coe_filter_toggle,
            ).pack(side=tk.RIGHT)
            coe_frame = ttk.Frame(right_frame)
            coe_frame.pack(fill=tk.X)
            self.coe_list = tk.Listbox(coe_frame, exportselection=False, height=5)
            self.coe_list.pack(side=tk.LEFT, fill=tk.X, expand=True)
            coe_scroll = ttk.Scrollbar(coe_frame, orient=tk.VERTICAL, command=self.coe_list.yview)
            coe_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.coe_list.config(yscrollcommand=coe_scroll.set)
            self.coe_list.bind("<<ListboxSelect>>", self._on_coe_select)

            ttk.Label(
                right_frame,
                text="PDO tree (expand PDO rows to inspect entries, toggle selection in Sel column)",
            ).pack(anchor=tk.W, pady=(8, 4))
            optional_frame = ttk.Frame(right_frame)
            optional_frame.pack(fill=tk.BOTH, expand=False)
            self.pdo_tree = ttk.Treeview(
                optional_frame,
                columns=("sel", "type", "index", "dir", "sm"),
                show="tree headings",
                height=12,
                style="Pdo.Treeview",
            )
            self.pdo_tree.heading("#0", text="PDO / Entry", anchor=tk.W)
            self.pdo_tree.heading("sel", text="Sel", anchor=tk.W)
            self.pdo_tree.heading("type", text="Type", anchor=tk.W)
            self.pdo_tree.heading("index", text="Index", anchor=tk.W)
            self.pdo_tree.heading("dir", text="Dir/DT", anchor=tk.W)
            self.pdo_tree.heading("sm", text="SM/Bits", anchor=tk.W)
            self.pdo_tree.column("#0", width=360, stretch=True, anchor=tk.W)
            self.pdo_tree.column("sel", width=46, stretch=False, anchor=tk.W)
            self.pdo_tree.column("type", width=86, stretch=False, anchor=tk.W)
            self.pdo_tree.column("index", width=130, stretch=False, anchor=tk.W)
            self.pdo_tree.column("dir", width=78, stretch=False, anchor=tk.W)
            self.pdo_tree.column("sm", width=78, stretch=False, anchor=tk.W)
            self.pdo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            optional_scroll = ttk.Scrollbar(optional_frame, orient=tk.VERTICAL, command=self.pdo_tree.yview)
            optional_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.pdo_tree.configure(yscrollcommand=optional_scroll.set)
            self.pdo_tree.tag_configure("blocked", foreground="gray55")
            self.pdo_tree.tag_configure("normal", foreground="black")
            self.pdo_tree.bind("<<TreeviewSelect>>", self._on_pdo_tree_select)
            self.pdo_tree.bind("<Button-1>", self._on_pdo_tree_click)
            self.pdo_tree.bind("<space>", self._on_pdo_tree_space)

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

            self.status_var = tk.StringVar(value="Idle")
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

        def _setup_tree_style(self) -> None:
            style = ttk.Style(self.root)
            base_bg = style.lookup("Treeview", "background") or "#ffffff"
            base_fg = style.lookup("Treeview", "foreground") or "#000000"
            sel_bg = style.lookup("Treeview", "selectbackground") or "#c7def7"
            sel_fg = style.lookup("Treeview", "selectforeground") or "#000000"

            style.configure("Pdo.Treeview", background=base_bg, foreground=base_fg)
            # Keep selected rows readable even when tree focus changes.
            style.map(
                "Pdo.Treeview",
                background=[
                    ("selected", sel_bg),
                    ("selected", "!focus", sel_bg),
                ],
                foreground=[
                    ("selected", sel_fg),
                    ("selected", "!focus", sel_fg),
                ],
            )

        def _set_busy(self, busy: bool, message: Optional[str] = None) -> None:
            if busy and self._activity_active:
                self._end_activity(restore_status=False)
            self._is_busy = bool(busy)
            if message is not None:
                if self.compact_status_labels and busy:
                    self.status_var.set("Working")
                elif self.compact_status_labels and not busy:
                    self.status_var.set("Idle")
                else:
                    self.status_var.set(message)
            if busy:
                if self.compact_status_labels:
                    self.status_var.set("Working")
                self.busy_var.set("Working...")
                self.progress.configure(mode="indeterminate")
                self.progress.start(12)
                self.root.config(cursor="watch")
            else:
                self.progress.stop()
                self.progress.configure(mode="determinate", value=0)
                self.busy_var.set("Idle")
                if self.compact_status_labels:
                    self.status_var.set("Idle")
                self.root.config(cursor="")
            try:
                self.root.update_idletasks()
                # Process pending UI events so button-state changes are immediate on all platforms.
                self.root.update()
            except Exception:
                pass

        def _begin_activity(self, message: str, maximum: int) -> None:
            if self._is_busy:
                return
            if not self._activity_active:
                self._activity_status_before = self.status_var.get()
            self._activity_active = True
            self.busy_var.set("Updating...")
            self.status_var.set("Updating" if self.compact_status_labels else message)
            self.progress.stop()
            self.progress.configure(mode="determinate", maximum=max(1, maximum), value=0)
            try:
                self.root.update_idletasks()
            except Exception:
                pass

        def _step_activity(self, value: int, message: Optional[str] = None, force: bool = False) -> None:
            if self._is_busy or not self._activity_active:
                return
            if message is not None:
                self.status_var.set("Updating" if self.compact_status_labels else message)
            elif self.compact_status_labels:
                self.status_var.set("Updating")
            max_value = int(float(self.progress.cget("maximum") or 1))
            capped = max(0, min(int(value), max_value))
            self.progress.configure(value=capped)
            try:
                self.root.update_idletasks()
                if force:
                    self.root.update()
            except Exception:
                pass

        def _end_activity(self, restore_status: bool = True) -> None:
            if not self._activity_active:
                return
            self._activity_active = False
            self.progress.stop()
            self.progress.configure(mode="determinate", value=0)
            self.busy_var.set("Idle")
            if self.compact_status_labels:
                self.status_var.set("Idle")
            elif restore_status and self._activity_status_before:
                self.status_var.set(self._activity_status_before)
            self._activity_status_before = ""
            try:
                self.root.update_idletasks()
            except Exception:
                pass

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
            sdo_state = "on" if self.include_coe_initcmd else "off"
            naming_state = "legacy" if self.legacy_naming else "modern"
            if self.custom_hwtype_override.strip():
                self.hwtype_label_var.set(
                    f"HWTYPE: custom={_snake(self.custom_hwtype_override)} | DC:{dc_state} | CoE-SDO:{sdo_state} | Naming:{naming_state}"
                )
                return
            auto_hwtype = self._auto_hwtype_for_current_selection()
            if auto_hwtype:
                self.hwtype_label_var.set(
                    f"HWTYPE: auto={auto_hwtype} | DC:{dc_state} | CoE-SDO:{sdo_state} | Naming:{naming_state}"
                )
            else:
                self.hwtype_label_var.set(f"HWTYPE: auto | DC:{dc_state} | CoE-SDO:{sdo_state} | Naming:{naming_state}")

        def _open_options_popup(self) -> None:
            auto_hwtype = self._auto_hwtype_for_current_selection()
            dialog = tk.Toplevel(self.root)
            dialog.title("Generator options")
            dialog.transient(self.root)
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
            include_coe_var = tk.BooleanVar(value=self.include_coe_initcmd)
            ttk.Checkbutton(
                frame,
                text="Include CoE InitCmd SDOs in HW snippet",
                variable=include_coe_var,
            ).grid(row=3, column=0, sticky=tk.W)
            legacy_naming_var = tk.BooleanVar(value=self.legacy_naming)
            ttk.Checkbutton(
                frame,
                text="Use legacy record naming (esi_parser style)",
                variable=legacy_naming_var,
            ).grid(row=4, column=0, sticky=tk.W)

            btns = ttk.Frame(frame)
            btns.grid(row=5, column=0, sticky=tk.E, pady=(10, 0))

            def _apply_options() -> None:
                value = hwtype_var.get().strip()
                self.custom_hwtype_override = value
                self.exclude_dc_clock = bool(exclude_dc_var.get())
                self.include_coe_initcmd = bool(include_coe_var.get())
                self.legacy_naming = bool(legacy_naming_var.get())
                if value:
                    self.status_var.set(
                        f"Options saved: HWTYPE={_snake(value)}, DC={'off' if self.exclude_dc_clock else 'on'}, "
                        f"CoE-SDO={'on' if self.include_coe_initcmd else 'off'}, Naming={'legacy' if self.legacy_naming else 'modern'}"
                    )
                else:
                    self.status_var.set(
                        f"Options saved: HWTYPE=auto, DC={'off' if self.exclude_dc_clock else 'on'}, "
                        f"CoE-SDO={'on' if self.include_coe_initcmd else 'off'}, Naming={'legacy' if self.legacy_naming else 'modern'}"
                    )
                self._update_hwtype_indicator()
                dialog.destroy()
                if self.pdo_tree.winfo_exists():
                    self.pdo_tree.focus_set()

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

        def _refresh_coe_list(self, slave: SlaveInfo) -> None:
            self.coe_list.delete(0, tk.END)
            self.current_coe_item_indexes = []
            only_repr = bool(self.coe_only_representable_var.get())
            for idx, init_cmd in enumerate(slave.coe_init_cmds):
                if only_repr and not coe_initcmd_is_representable(init_cmd):
                    continue
                self.current_coe_item_indexes.append(idx)
                self.coe_list.insert(tk.END, coe_initcmd_summary_text(init_cmd))
            if self.coe_list.size() == 0:
                placeholder = "(no CoE InitCmd entries)"
                if only_repr:
                    placeholder = "(no representable CoE InitCmd entries <=4B)"
                self.coe_list.insert(tk.END, placeholder)

        def _on_coe_filter_toggle(self) -> None:
            slave = self._selected_slave()
            self.details.delete("1.0", tk.END)
            if slave is None:
                self.coe_list.delete(0, tk.END)
                self.current_coe_item_indexes = []
                return
            self._refresh_coe_list(slave)
            filter_state = "ON" if self.coe_only_representable_var.get() else "OFF"
            self.status_var.set(f"CoE filter 'Only <=4B' {filter_state}")

        def _on_coe_select(self, _event) -> None:
            slave = self._selected_slave()
            if slave is None:
                return
            sel = self.coe_list.curselection()
            if not sel:
                return
            list_idx = sel[0]
            if not (0 <= list_idx < len(self.current_coe_item_indexes)):
                return
            idx = self.current_coe_item_indexes[list_idx]
            self.details.delete("1.0", tk.END)
            self.details.insert(tk.END, coe_initcmd_details_text(slave.coe_init_cmds[idx]))

        def _selected_checked_pdo_indexes(self) -> List[str]:
            indexes: List[str] = []
            for row_item in self.pdo_row_items:
                if row_item.get("checked", False):
                    choice = row_item["choice"]
                    indexes.append(choice.pdo.index)
            return indexes

        def _current_checked_pdo_indexes(self, exclude_pdo_index: Optional[str] = None) -> Set[str]:
            checked: Set[str] = set()
            for row_item in self.pdo_row_items:
                if not row_item.get("checked", False):
                    continue
                choice = row_item["choice"]
                if exclude_pdo_index is not None and choice.pdo.index == exclude_pdo_index:
                    continue
                checked.add(choice.pdo.index)
            return checked

        def _selected_pdo_row_index(self) -> int:
            selected = self.pdo_tree.selection()
            if not selected:
                return -1
            item_id = selected[0]
            if item_id in self.pdo_item_to_row:
                return self.pdo_item_to_row[item_id]
            parent = self.pdo_tree.parent(item_id)
            if parent and parent in self.pdo_item_to_row:
                return self.pdo_item_to_row[parent]
            return -1

        def _cancel_pending_pdo_details_update(self) -> None:
            if self._pending_pdo_select_after_id is None:
                return
            try:
                self.root.after_cancel(self._pending_pdo_select_after_id)
            except Exception:
                pass
            self._pending_pdo_select_after_id = None

        def _run_pending_pdo_details_update(self) -> None:
            self._pending_pdo_select_after_id = None
            row_idx = self._selected_pdo_row_index()
            if row_idx >= 0:
                self._show_pdo_row_details(row_idx)

        def _schedule_pdo_details_update(self, delay_ms: int = 40) -> None:
            self._cancel_pending_pdo_details_update()
            self._pending_pdo_select_after_id = self.root.after(delay_ms, self._run_pending_pdo_details_update)

        def _show_pdo_row_details(self, row_idx: int) -> None:
            if not (0 <= row_idx < len(self.pdo_row_items)):
                return
            row_item = self.pdo_row_items[row_idx]
            choice = row_item["choice"]
            reason = row_item.get("reason", "")
            self.details.delete("1.0", tk.END)
            self.details.insert(tk.END, pdo_choice_details_text(choice))
            if reason:
                self.details.insert(tk.END, f"\nNot selectable for current mapping: {reason}\n")
            slave = self._selected_slave()
            mapping, _mapping_idx0 = self._selected_mapping()
            if slave is not None and mapping is not None:
                self.details.insert(tk.END, "\n---\n\nMapping overview (incl. DC info)\n\n")
                overview = self._mapping_overview_text or mapping_details_text(slave, mapping)
                self.details.insert(tk.END, overview)

        def _clear_optional_pdos(self) -> None:
            self._cancel_pending_pdo_details_update()
            self.current_pdo_choices = []
            self.optional_pdo_vars = []
            self.pdo_row_items = []
            self.pdo_item_to_row = {}
            for item_id in self.pdo_tree.get_children(""):
                self.pdo_tree.delete(item_id)

        def _update_pdo_row_states(self, slave: SlaveInfo, mapping: PdoMapping) -> None:
            total_rows = len(self.pdo_row_items)
            if total_rows <= 0:
                return
            self._begin_activity("Refreshing PDO availability...", total_rows)
            checked_selected = self._current_checked_pdo_indexes()
            conflict_context = _build_pdo_conflict_context(slave, checked_selected)
            try:
                for row_idx, row_item in enumerate(self.pdo_row_items):
                    choice = row_item["choice"]
                    item_id = row_item["item_id"]
                    entry_item_ids = row_item.get("entry_items", [])
                    checked = bool(row_item.get("checked", False))
                    if choice.is_default:
                        selectable = True
                        reason = ""
                    elif checked:
                        selectable = True
                        reason = ""
                    else:
                        selectable, reason = pdo_selectable_for_mapping(
                            slave,
                            mapping,
                            choice.pdo.index,
                            checked_selected_indexes=checked_selected,
                            conflict_context=conflict_context,
                        )

                    row_type = "DEFAULT" if choice.is_default else "OPTIONAL"
                    sel_mark = "[x]" if checked else "[ ]"
                    is_blocked = (not selectable) and (not checked)
                    row_text = choice.pdo.name or "(unnamed)"
                    if is_blocked and reason:
                        row_text = f"{row_text} [blocked: {reason}]"
                    row_values = (sel_mark, row_type, choice.pdo.index, choice.pdo.direction.upper(), choice.sm_no)
                    row_tag = ("blocked",) if is_blocked else ("normal",)

                    if row_item.get("ui_text") != row_text or row_item.get("ui_values") != row_values:
                        self.pdo_tree.item(item_id, text=row_text, values=row_values)
                        row_item["ui_text"] = row_text
                        row_item["ui_values"] = row_values

                    if row_item.get("ui_tag") != row_tag:
                        self.pdo_tree.item(item_id, tags=row_tag)
                        for entry_item_id in entry_item_ids:
                            self.pdo_tree.item(entry_item_id, tags=row_tag)
                        row_item["ui_tag"] = row_tag

                    row_item["reason"] = reason if is_blocked else ""
                    if is_blocked:
                        self.pdo_tree.item(item_id, open=False)
                    self.pdo_row_items[row_idx] = row_item

                    done_rows = row_idx + 1
                    if done_rows == total_rows or (done_rows % 24) == 0:
                        self._step_activity(
                            done_rows,
                            message=f"Refreshing PDO availability... {done_rows}/{total_rows}",
                            force=(done_rows == total_rows),
                        )
            finally:
                self._end_activity(restore_status=True)

        def _toggle_pdo_row(self, row_idx: int) -> None:
            if not (0 <= row_idx < len(self.current_pdo_choices)):
                return
            slave = self._selected_slave()
            mapping, _mapping_idx0 = self._selected_mapping()
            if slave is None or mapping is None:
                return

            row_item = self.pdo_row_items[row_idx]
            choice = row_item["choice"]
            checked_value = not bool(row_item.get("checked", False))

            if checked_value and not choice.is_default:
                selectable, reason = pdo_selectable_for_mapping(
                    slave,
                    mapping,
                    choice.pdo.index,
                    checked_selected_indexes=self._current_checked_pdo_indexes(exclude_pdo_index=choice.pdo.index),
                )
                if not selectable:
                    self.status_var.set(f"PDO {choice.pdo.index} is not selectable: {reason}")
                    checked_value = False

            row_item["checked"] = checked_value
            self.pdo_row_items[row_idx] = row_item
            self._cancel_pending_pdo_details_update()
            self._update_pdo_row_states(slave, mapping)
            self._show_pdo_row_details(row_idx)

        def _on_pdo_tree_select(self, _event) -> None:
            self._schedule_pdo_details_update(delay_ms=40)

        def _on_pdo_tree_click(self, event) -> Optional[str]:
            item_id = self.pdo_tree.identify_row(event.y)
            if not item_id:
                return None
            column_id = self.pdo_tree.identify_column(event.x)
            pdo_item_id = item_id
            if pdo_item_id not in self.pdo_item_to_row:
                parent = self.pdo_tree.parent(pdo_item_id)
                if parent:
                    pdo_item_id = parent
            if pdo_item_id not in self.pdo_item_to_row:
                return None
            row_idx = self.pdo_item_to_row[pdo_item_id]
            if column_id == "#1":
                self.pdo_tree.selection_set(pdo_item_id)
                self.pdo_tree.focus(pdo_item_id)
                self._toggle_pdo_row(row_idx)
                return "break"
            return None

        def _on_pdo_tree_space(self, _event) -> Optional[str]:
            row_idx = self._selected_pdo_row_index()
            if row_idx >= 0:
                self._toggle_pdo_row(row_idx)
                return "break"
            return None

        def _refresh_optional_pdos(self, slave: SlaveInfo, mapping: PdoMapping) -> None:
            self._clear_optional_pdos()
            self.current_pdo_choices = pdo_choices_for_mapping(slave, mapping)
            total_choices = len(self.current_pdo_choices)
            if total_choices > 0:
                self._begin_activity("Building PDO tree...", total_choices)
            try:
                for row_idx, choice in enumerate(self.current_pdo_choices):
                    pdo = choice.pdo
                    item_id = self.pdo_tree.insert(
                        "",
                        tk.END,
                        text=pdo.name or "(unnamed)",
                        values=("", "", pdo.index, pdo.direction.upper(), choice.sm_no),
                        open=False,
                    )
                    self.pdo_item_to_row[item_id] = row_idx

                    entry_item_ids: List[str] = []
                    for entry in pdo.entries:
                        entry_label = entry.resolved_name or entry.raw_name or "(unnamed)"
                        entry_item = self.pdo_tree.insert(
                            item_id,
                            tk.END,
                            text=entry_label,
                            values=("", "ENTRY", f"{entry.index}:{entry.subindex}", entry.data_type, f"{entry.bitlen}b"),
                        )
                        entry_item_ids.append(entry_item)

                    self.pdo_row_items.append(
                        {
                            "choice": choice,
                            "item_id": item_id,
                            "entry_items": entry_item_ids,
                            "checked": bool(choice.is_default),
                            "reason": "",
                        }
                    )

                    done_rows = row_idx + 1
                    if done_rows == total_choices or (done_rows % 24) == 0:
                        self._step_activity(
                            done_rows,
                            message=f"Building PDO tree... {done_rows}/{total_choices}",
                            force=(done_rows == total_choices),
                        )
            finally:
                if total_choices > 0:
                    self._end_activity(restore_status=True)

            if not self.current_pdo_choices:
                item_id = self.pdo_tree.insert("", tk.END, text="(No PDOs available for this mapping)")
                self.pdo_tree.item(item_id, tags=("blocked",))

            self._update_pdo_row_states(slave, mapping)

        def _load(self) -> None:
            if self._is_busy:
                self.status_var.set("Working" if self.compact_status_labels else "Working... please wait.")
                return
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
                self.coe_list.delete(0, tk.END)
                self.current_coe_item_indexes = []
                self._clear_optional_pdos()
                self.details.delete("1.0", tk.END)
                self.current_mappings = []
                self.generated_snippet = ""
                self.generated_substitutions = ""
                self.generated_panel = ""
                self._mapping_overview_text = ""

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
            self._cancel_pending_pdo_details_update()
            self.current_mappings = slave.mappings
            self.generated_snippet = ""
            self.generated_substitutions = ""
            self.generated_panel = ""
            self._mapping_overview_text = ""

            self.mapping_list.delete(0, tk.END)
            self._refresh_coe_list(slave)
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
                self._mapping_overview_text = ""
                self._update_hwtype_indicator()

        def _on_mapping_select(self, _event) -> None:
            slave = self._selected_slave()
            mapping, _ = self._selected_mapping()
            if slave is None or mapping is None:
                return
            self._cancel_pending_pdo_details_update()
            self.generated_snippet = ""
            self.generated_substitutions = ""
            self.generated_panel = ""
            self._refresh_optional_pdos(slave, mapping)
            self._mapping_overview_text = mapping_details_text(slave, mapping)
            self.details.delete("1.0", tk.END)
            self.details.insert(tk.END, self._mapping_overview_text)
            self._update_hwtype_indicator()

        def _show_generated_files_popup(self) -> None:
            if self.generated_popup is not None and self.generated_popup.winfo_exists():
                self.generated_popup.destroy()
            self.generated_popup = None
            self.generated_hw_text = None
            self.generated_db_text = None
            self.generated_panel_text = None
            self.generated_panel_preview_canvas = None
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
            self.generated_panel_text = _add_tab("Panel .ui", self.generated_panel)
            preview_tab = ttk.Frame(notebook)
            notebook.add(preview_tab, text="Panel preview")
            preview_outer = ttk.Frame(preview_tab)
            preview_outer.pack(fill=tk.BOTH, expand=True)
            self.generated_panel_preview_canvas = tk.Canvas(preview_outer, bg="#f5f5f5", highlightthickness=0)
            self.generated_panel_preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            preview_yscroll = ttk.Scrollbar(
                preview_outer, orient=tk.VERTICAL, command=self.generated_panel_preview_canvas.yview
            )
            preview_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
            preview_xscroll = ttk.Scrollbar(
                preview_outer, orient=tk.HORIZONTAL, command=self.generated_panel_preview_canvas.xview
            )
            preview_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
            self.generated_panel_preview_canvas.config(
                yscrollcommand=preview_yscroll.set,
                xscrollcommand=preview_xscroll.set,
            )

            btns = ttk.Frame(outer)
            btns.pack(fill=tk.X, pady=(8, 0))
            self.generated_edit_var = tk.BooleanVar(value=False)

            def _set_editable_state() -> None:
                editable = bool(self.generated_edit_var and self.generated_edit_var.get())
                state = tk.NORMAL if editable else tk.DISABLED
                for widget in (
                    self.generated_hw_text,
                    self.generated_db_text,
                    self.generated_panel_text,
                ):
                    if widget is not None and widget.winfo_exists():
                        widget.config(state=state)

            def _close_popup() -> None:
                self.generated_popup = None
                self.generated_hw_text = None
                self.generated_db_text = None
                self.generated_panel_text = None
                self.generated_panel_preview_canvas = None
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
            ttk.Button(btns, text="Save panel .ui...", command=self._save_panel).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(btns, text="Save all...", command=self._save_all_generated).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(btns, text="Refresh preview", command=self._refresh_panel_preview).pack(
                side=tk.LEFT, padx=(6, 0)
            )
            ttk.Button(btns, text="Close", command=_close_popup).pack(side=tk.RIGHT)
            dialog.protocol("WM_DELETE_WINDOW", _close_popup)
            self._refresh_panel_preview()

        def _sync_generated_texts_from_popup(self) -> None:
            if self.generated_hw_text is not None and self.generated_hw_text.winfo_exists():
                self.generated_snippet = self.generated_hw_text.get("1.0", "end-1c")
            if self.generated_db_text is not None and self.generated_db_text.winfo_exists():
                self.generated_substitutions = self.generated_db_text.get("1.0", "end-1c")
            if self.generated_panel_text is not None and self.generated_panel_text.winfo_exists():
                self.generated_panel = self.generated_panel_text.get("1.0", "end-1c")

        def _generate_files_popup(self) -> None:
            if self._is_busy:
                self.status_var.set("Working" if self.compact_status_labels else "Working... please wait.")
                return
            slave = self._selected_slave()
            mapping, mapping_idx0 = self._selected_mapping()
            if slave is None or mapping is None:
                messagebox.showwarning("Selection missing", "Select a slave and PDO mapping first.")
                return

            self._set_busy(True, "Generating hardware snippet, DB file, and panel...")
            try:
                self.generated_snippet = generate_hw_snippet(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    include_dc=not self.exclude_dc_clock,
                    include_coe_initcmd=self.include_coe_initcmd,
                    legacy_naming=self.legacy_naming,
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
                    include_coe_initcmd=self.include_coe_initcmd,
                    legacy_naming=self.legacy_naming,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.generated_panel = generate_caqtdm_panel(
                    slave=slave,
                    mapping=mapping,
                    mapping_index=mapping_idx0 + 1,
                    mapping_count=max(1, len(slave.mappings)),
                    selected_pdo_indexes=self._selected_checked_pdo_indexes(),
                    hwtype_override=self.custom_hwtype_override or None,
                    legacy_naming=self.legacy_naming,
                    esi_file=str(Path(self.file_var.get()).expanduser()),
                )
                self.status_var.set(
                    f"Generated HW + DB + panel for {slave.type_name}, mapping {mapping_idx0 + 1}/{len(slave.mappings)}"
                )
            finally:
                self._set_busy(False)

            self._show_generated_files_popup()

        def _refresh_panel_preview(self) -> None:
            if self.generated_panel_preview_canvas is None or not self.generated_panel_preview_canvas.winfo_exists():
                return
            self._sync_generated_texts_from_popup()
            canvas = self.generated_panel_preview_canvas
            canvas.delete("all")

            if not self.generated_panel.strip():
                canvas.create_text(12, 12, anchor=tk.NW, text="No panel generated.", fill="#444")
                return

            try:
                panel_w, panel_h, tab_rect, tab_sets = parse_generated_panel_preview_items(self.generated_panel)
            except Exception as exc:
                canvas.create_text(12, 12, anchor=tk.NW, text=f"Preview parse error:\n{exc}", fill="#a00")
                return

            shown_tabs = tab_sets if tab_sets else [("Panel", [])]

            scale = 1.55
            ox = 14
            oy = 26
            gap_x = 24
            gap_y = 26
            panel_px_w = int(panel_w * scale)
            panel_px_h = int(panel_h * scale)
            cols = 2 if len(shown_tabs) > 1 else 1
            rows_n = (len(shown_tabs) + cols - 1) // cols
            canvas_w = (ox * 2) + (panel_px_w * cols) + (gap_x * max(0, cols - 1))
            canvas_h = (oy * 2) + (panel_px_h * rows_n) + (gap_y * max(0, rows_n - 1))
            canvas.config(scrollregion=(0, 0, canvas_w, canvas_h))

            canvas.create_text(
                ox,
                4,
                anchor=tk.NW,
                fill="#555",
                text="Rough preview (not exact caQtDM rendering, all tabs)",
            )

            for tab_idx, (tab_title, items) in enumerate(shown_tabs, start=1):
                col = (tab_idx - 1) % cols
                row = (tab_idx - 1) // cols
                px = ox + col * (panel_px_w + gap_x)
                py = oy + row * (panel_px_h + gap_y)
                canvas.create_text(
                    px,
                    py - 8,
                    anchor=tk.NW,
                    text=f"Tab {tab_idx}: {tab_title}",
                    fill="#333",
                    font=("TkDefaultFont", 8),
                )
                canvas.create_rectangle(
                    px - 2,
                    py - 2,
                    px + panel_px_w + 2,
                    py + panel_px_h + 2,
                    outline="#777",
                    width=1,
                    fill="#efefef",
                )

                if tab_rect is not None:
                    tx, ty, tw, th = tab_rect
                    tx1 = px + tx * scale
                    ty1 = py + ty * scale
                    tx2 = px + (tx + tw) * scale
                    ty2 = py + (ty + th) * scale
                    canvas.create_rectangle(tx1, ty1, tx2, ty2, outline="#6d6d6d", width=1, fill="#f2f2f2")
                    title_w = min(42, tw - 4)
                    t1x = px + (tx + 2) * scale
                    t1y = py + (ty + 2) * scale
                    t2x = px + (tx + 2 + title_w) * scale
                    t2y = py + (ty + 20) * scale
                    canvas.create_rectangle(t1x, t1y, t2x, t2y, outline="#666", width=1, fill="#e5e5e5")
                    canvas.create_text(
                        t1x + 3,
                        t1y + ((t2y - t1y) / 2),
                        anchor=tk.W,
                        text=tab_title[:10],
                        fill="#333",
                        font=("TkDefaultFont", 8),
                    )

                for item_type, rect, text in items:
                    x, y, w, h = rect
                    x1 = px + x * scale
                    y1 = py + y * scale
                    x2 = px + (x + w) * scale
                    y2 = py + (y + h) * scale

                    if item_type == "label":
                        canvas.create_text(
                            x1 + 2,
                            y1 + (h * scale) / 2,
                            anchor=tk.W,
                            text=text,
                            fill="#222",
                            font=("TkDefaultFont", 8),
                        )
                    elif item_type == "byte":
                        canvas.create_rectangle(x1, y1, x2, y2, outline="#4d784d", width=1, fill="#e9f5e9")
                        bit_label = text or "bits"
                        bit_count = 0
                        match = re.match(r"B(\d+)\.\.B(\d+)", bit_label)
                        if match:
                            start_b = int(match.group(1))
                            end_b = int(match.group(2))
                            if end_b >= start_b:
                                bit_count = (end_b - start_b) + 1
                        if bit_count > 0:
                            gap = 1
                            max_cell_h = 6
                            total_gaps = (bit_count - 1) * gap
                            usable_h = max(6, (y2 - y1) - 4)
                            cell_h = min(max_cell_h, max(1, int((usable_h - total_gaps) / bit_count)))
                            col_h = bit_count * cell_h + total_gaps
                            start_y = y2 - 2 - col_h
                            cell_w = max(4, int((x2 - x1) - 4))
                            cell_x = x1 + ((x2 - x1) - cell_w) / 2
                            for i in range(bit_count):
                                by1 = start_y + i * (cell_h + gap)
                                by2 = by1 + cell_h
                                canvas.create_rectangle(
                                    cell_x,
                                    by1,
                                    cell_x + cell_w,
                                    by2,
                                    outline="#3f6f3f",
                                    width=1,
                                    fill="#d3e9d3",
                                )
                    else:
                        canvas.create_rectangle(x1, y1, x2, y2, outline="#666", width=1, fill="#fff")
                        tail = text.split("-")[-1] if text else ""
                        canvas.create_text(
                            x2 - 2,
                            y1 + (h * scale) / 2,
                            anchor=tk.E,
                            text=tail[:10],
                            fill="#666",
                            font=("TkDefaultFont", 7),
                        )

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
                    include_coe_initcmd=self.include_coe_initcmd,
                    legacy_naming=self.legacy_naming,
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
                    include_coe_initcmd=self.include_coe_initcmd,
                    legacy_naming=self.legacy_naming,
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

        def _save_panel(self) -> None:
            self._sync_generated_texts_from_popup()
            if not self.generated_panel:
                self._generate_files_popup()
                if not self.generated_panel:
                    return

            slave = self._selected_slave()
            _, mapping_idx0 = self._selected_mapping()
            default_name = "ecmcPanel.ui"
            if slave is not None and mapping_idx0 >= 0:
                hwtype = _resolve_hwtype(
                    slave,
                    mapping_idx0 + 1,
                    max(1, len(slave.mappings)),
                    self.custom_hwtype_override or None,
                )
                default_name = f"ecmc{hwtype}.ui"

            path = filedialog.asksaveasfilename(
                title="Save caQtDM panel",
                defaultextension=".ui",
                initialfile=default_name,
                filetypes=(("Qt ui files", "*.ui"), ("All files", "*.*")),
            )
            if not path:
                return
            self._set_busy(True, "Saving panel...")
            try:
                self._sync_generated_texts_from_popup()
                Path(path).write_text(self.generated_panel)
                self.status_var.set(f"Saved panel: {path}")
            finally:
                self._set_busy(False)

        def _save_all_generated(self) -> None:
            self._sync_generated_texts_from_popup()
            if not (self.generated_snippet and self.generated_substitutions and self.generated_panel):
                self._generate_files_popup()
                if not (self.generated_snippet and self.generated_substitutions and self.generated_panel):
                    return

            slave = self._selected_slave()
            _, mapping_idx0 = self._selected_mapping()
            base_name = "ecmcGenerated"
            if slave is not None and mapping_idx0 >= 0:
                hwtype = _resolve_hwtype(
                    slave,
                    mapping_idx0 + 1,
                    max(1, len(slave.mappings)),
                    self.custom_hwtype_override or None,
                )
                base_name = f"ecmc{hwtype}"

            picked = filedialog.asksaveasfilename(
                title="Save all generated files (choose base name)",
                defaultextension=".cmd",
                initialfile=f"{base_name}.cmd",
                filetypes=(("Command files", "*.cmd"), ("All files", "*.*")),
            )
            if not picked:
                return

            picked_path = Path(picked)
            stem = picked_path.stem if picked_path.stem else base_name
            out_cmd = picked_path.with_name(f"{stem}.cmd")
            out_subs = picked_path.with_name(f"{stem}.substitutions")
            out_ui = picked_path.with_name(f"{stem}.ui")

            self._set_busy(True, "Saving all generated files...")
            try:
                self._sync_generated_texts_from_popup()
                out_cmd.write_text(self.generated_snippet)
                out_subs.write_text(self.generated_substitutions)
                out_ui.write_text(self.generated_panel)
                self.status_var.set(
                    f"Saved all: {out_cmd.name}, {out_subs.name}, {out_ui.name}"
                )
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
        "--generate-panel",
        action="store_true",
        help="In --no-gui mode: generate one caQtDM panel (.ui)",
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
        "--panel-out",
        help="Output .ui file for generated panel (default: print to stdout)",
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
    p.add_argument(
        "--include-coe-initcmd",
        action="store_true",
        help="Include Mailbox/CoE/InitCmd startup SDOs in generated HW snippet",
    )
    p.add_argument(
        "--modern-naming",
        action="store_true",
        help="Use modern naming instead of legacy esi_parser-style record names",
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

        generation_count = int(bool(args.generate_snippet)) + int(bool(args.generate_substitutions)) + int(
            bool(args.generate_panel)
        )
        if generation_count == 0:
            print_mappings(slaves)
            return 0
        if generation_count > 1:
            print(
                "Choose only one generation mode: --generate-snippet, --generate-substitutions, or --generate-panel",
                file=sys.stderr,
            )
            return 2
        if args.generate_snippet and (args.substitutions_out or args.panel_out):
            print("--substitutions-out/--panel-out cannot be used with --generate-snippet", file=sys.stderr)
            return 2
        if args.generate_substitutions and (args.snippet_out or args.panel_out):
            print("--snippet-out/--panel-out cannot be used with --generate-substitutions", file=sys.stderr)
            return 2
        if args.generate_panel and (args.snippet_out or args.substitutions_out):
            print("--snippet-out/--substitutions-out cannot be used with --generate-panel", file=sys.stderr)
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
        optional_pdo_indexes: List[str] = []
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
                include_coe_initcmd=args.include_coe_initcmd,
                legacy_naming=not args.modern_naming,
                esi_file=str(file_path),
            )
            if args.snippet_out:
                output_file = Path(args.snippet_out).expanduser()
                output_file.write_text(output)
                print(f"Wrote snippet: {output_file}")
                return 0
        elif args.generate_substitutions:
            output = generate_substitutions(
                slave=slave,
                mapping=mapping,
                mapping_index=args.mapping_index,
                mapping_count=len(slave.mappings),
                optional_pdo_indexes=optional_pdo_indexes,
                include_dc=not args.exclude_dc,
                include_coe_initcmd=args.include_coe_initcmd,
                legacy_naming=not args.modern_naming,
                esi_file=str(file_path),
            )
            if args.substitutions_out:
                output_file = Path(args.substitutions_out).expanduser()
                output_file.write_text(output)
                print(f"Wrote substitutions: {output_file}")
                return 0
        else:
            output = generate_caqtdm_panel(
                slave=slave,
                mapping=mapping,
                mapping_index=args.mapping_index,
                mapping_count=len(slave.mappings),
                optional_pdo_indexes=optional_pdo_indexes,
                legacy_naming=not args.modern_naming,
                esi_file=str(file_path),
            )
            if args.panel_out:
                output_file = Path(args.panel_out).expanduser()
                output_file.write_text(output)
                print(f"Wrote panel: {output_file}")
                return 0

        print(output, end="")
        return 0

    return run_gui(file_path, args.name, args.rev)


if __name__ == "__main__":
    raise SystemExit(main())
