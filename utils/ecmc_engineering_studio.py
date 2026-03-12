#!/usr/bin/env python3
"""
ecmc Engineering Studio

Base engineering application with:
- Ordered object tree (Slave/Axis/PLC)
- Per-object parameter tree
- Right-side file editor for axis/plc files
- Popup-driven slave selection from supported ecmccfg hardware
- Launcher for esi_mapping_browser (for generating new support)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from esi_mapping_browser import _find_ecmccfg_root, _scan_supported_hardware


@dataclass
class SlaveObj:
    slave_id: int
    hw_desc: str
    macros: str = ""
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class AxisObj:
    file: str
    axis_id: int
    axis_name: str
    drv_sid: str = "${DRV_SID}"
    enc_sid: str = "${ENC_SID}"
    drv_ch: str = "01"
    enc_ch: str = "01"
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class PlcObj:
    file: str
    sample_rate_ms: str = "100"
    macros: str = "DBG="
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectObj:
    kind: str  # slave | axis | plc
    data: object


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "axis"


def _as_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except Exception:
        return default


class EngineeringStudio:
    def __init__(self, root, outdir: Path, default_esi_file: str = "") -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.root.title("ecmc Engineering Studio")
        self.root.geometry("1520x920")

        self.output_dir_var = tk.StringVar(value=str(outdir))
        self.default_esi_file = default_esi_file.strip()
        self.status_var = tk.StringVar(value="Ready")

        self.supported_hw_root: Path | None = None
        self.supported_hw_descs: list[str] = []
        self.supported_hw_by_desc: dict[str, list[str]] = {}
        self.add_slave_param_defs: list[dict[str, str]] = self._discover_add_slave_param_defs()
        self.axis_cmd_param_defs: list[dict[str, str]] = self._discover_axis_cmd_param_defs()
        self.plc_cmd_param_defs: list[dict[str, str]] = self._discover_plc_cmd_param_defs()

        self.objects: list[ProjectObj] = [
            ProjectObj("axis", AxisObj(file="cfg/axis_01_m1.yaml", axis_id=1, axis_name="M1")),
            ProjectObj("plc", PlcObj(file="cfg/main.plc")),
        ]
        self.file_buffers: dict[str, str] = {}
        self.current_edit_file: str | None = None
        self.current_edit_obj_idx: int = -1

        self._build_ui()
        self._refresh_supported_hw()
        self._refresh_object_tree()
        self._refresh_param_tree(None)
        self._refresh_generated_list()

    def _build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        top = ttk.Frame(self.root, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Output dir").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(top, textvariable=self.output_dir_var, width=88).grid(row=0, column=1, sticky=tk.EW, padx=6)
        ttk.Button(top, text="Browse...", command=self._pick_output_dir).grid(row=0, column=2, padx=(0, 10))
        top.columnconfigure(1, weight=1)

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Panedwindow(body, orient=tk.VERTICAL)
        right = ttk.Frame(body)
        body.add(left, weight=2)
        body.add(right, weight=5)

        obj_frame = ttk.Frame(left)
        param_frame = ttk.Frame(left)
        left.add(obj_frame, weight=3)
        left.add(param_frame, weight=2)

        ttk.Label(obj_frame, text="Objects (ordered)").pack(anchor=tk.W, pady=(0, 4))
        self.obj_tree = ttk.Treeview(obj_frame, columns=("type", "summary"), show="tree headings")
        self.obj_tree.heading("#0", text="#", anchor=tk.W)
        self.obj_tree.heading("type", text="Type", anchor=tk.W)
        self.obj_tree.heading("summary", text="Summary", anchor=tk.W)
        self.obj_tree.column("#0", width=44, stretch=False, anchor=tk.W)
        self.obj_tree.column("type", width=84, stretch=False, anchor=tk.W)
        self.obj_tree.column("summary", width=360, stretch=True, anchor=tk.W)
        self.obj_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        obj_scroll = ttk.Scrollbar(obj_frame, orient=tk.VERTICAL, command=self.obj_tree.yview)
        obj_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.obj_tree.configure(yscrollcommand=obj_scroll.set)
        self.obj_tree.bind("<<TreeviewSelect>>", self._on_object_select)
        self.obj_tree.bind("<Button-3>", self._on_object_right_click)
        self.obj_tree.bind("<Control-Button-1>", self._on_object_right_click)

        self.obj_menu = tk.Menu(self.root, tearoff=0)
        self.obj_menu.add_command(label="Add Slave...", command=lambda: self._add_slave(after_selected=True))
        self.obj_menu.add_command(label="Add Axis...", command=lambda: self._add_axis(after_selected=True))
        self.obj_menu.add_command(label="Add PLC...", command=lambda: self._add_plc(after_selected=True))
        self.obj_menu.add_separator()
        self.obj_menu.add_command(label="Edit Object...", command=self._edit_selected_object)
        self.obj_menu.add_separator()
        self.obj_menu.add_command(label="Move Up", command=lambda: self._move_selected_object(-1))
        self.obj_menu.add_command(label="Move Down", command=lambda: self._move_selected_object(1))
        self.obj_menu.add_separator()
        self.obj_menu.add_command(label="Remove", command=self._remove_selected_object)

        ttk.Label(param_frame, text="Object Parameters").pack(anchor=tk.W, pady=(0, 4))
        self.param_tree = ttk.Treeview(param_frame, columns=("value",), show="tree headings")
        self.param_tree.heading("#0", text="Parameter", anchor=tk.W)
        self.param_tree.heading("value", text="Value", anchor=tk.W)
        self.param_tree.column("#0", width=180, anchor=tk.W, stretch=False)
        self.param_tree.column("value", width=260, anchor=tk.W, stretch=True)
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scroll = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=self.param_tree.yview)
        param_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.param_tree.configure(yscrollcommand=param_scroll.set)

        ttk.Label(right, text="File Editor").pack(anchor=tk.W)
        header = ttk.Frame(right)
        header.pack(fill=tk.X, pady=(4, 4))
        self.editor_file_var = tk.StringVar(value="(select axis/plc object)")
        ttk.Label(header, textvariable=self.editor_file_var).pack(side=tk.LEFT)
        ttk.Button(header, text="Apply Editor Changes", command=self._apply_editor_changes).pack(side=tk.RIGHT)

        self.editor_text = tk.Text(right, wrap=tk.NONE)
        self.editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ey = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.editor_text.yview)
        ey.pack(side=tk.RIGHT, fill=tk.Y)
        ex = ttk.Scrollbar(right, orient=tk.HORIZONTAL, command=self.editor_text.xview)
        ex.pack(side=tk.BOTTOM, fill=tk.X)
        self.editor_text.configure(yscrollcommand=ey.set, xscrollcommand=ex.set)

        bottom = ttk.Frame(self.root, padding=(8, 4))
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(bottom, text="Add Slave", command=lambda: self._add_slave(after_selected=False)).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Add Axis", command=lambda: self._add_axis(after_selected=False)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Add PLC", command=lambda: self._add_plc(after_selected=False)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Generate Preview", command=self._refresh_generated_list).pack(side=tk.LEFT, padx=(18, 0))
        ttk.Button(bottom, text="Save All", command=self._save_all).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Quit", command=self.root.destroy).pack(side=tk.RIGHT)
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.LEFT, padx=(14, 0))

    def _pick_output_dir(self) -> None:
        from tkinter import filedialog

        picked = filedialog.askdirectory(title="Select output directory", initialdir=self.output_dir_var.get().strip() or ".")
        if picked:
            self.output_dir_var.set(picked)

    def _refresh_supported_hw(self) -> None:
        self.supported_hw_root, self.supported_hw_descs, self.supported_hw_by_desc, _ = _scan_supported_hardware()

    def _discover_cmd_param_defs(
        self,
        script_rel_path: str,
        preferred: list[str],
        skip: set[str],
    ) -> list[dict[str, str]]:
        root = _find_ecmccfg_root()
        if root is None:
            return []
        cmd_file = root / script_rel_path
        if not cmd_file.exists():
            return []

        try:
            text = cmd_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        defaults: dict[str, str] = {}
        for match in re.finditer(r"\$\{([A-Z0-9_]+)=([^}]*)\}", text):
            name = match.group(1).strip()
            if name and name not in defaults:
                defaults[name] = match.group(2).strip()

        descriptions: dict[str, str] = {}
        for line in text.splitlines():
            m = re.search(r"\\param\\s+([A-Z0-9_]+)(.*)$", line)
            if not m:
                continue
            pname = m.group(1).strip()
            pdesc = m.group(2).strip(" :")
            if pname and pname not in descriptions:
                descriptions[pname] = pdesc

        ordered: list[str] = []
        for name in preferred:
            if name in descriptions or name in defaults:
                ordered.append(name)
        for name in descriptions.keys():
            if name not in ordered:
                ordered.append(name)
        for name in defaults.keys():
            if name not in ordered:
                ordered.append(name)

        defs: list[dict[str, str]] = []
        for name in ordered:
            if name in skip:
                continue
            defs.append(
                {
                    "name": name,
                    "default": defaults.get(name, ""),
                    "desc": descriptions.get(name, ""),
                }
            )
        return defs

    def _discover_add_slave_param_defs(self) -> list[dict[str, str]]:
        return self._discover_cmd_param_defs(
            script_rel_path="scripts/addSlave.cmd",
            preferred=["SUBST_FILE", "P_SCRIPT", "NELM", "DEFAULT_SUBS", "DEFAULT_SLAVE_PVS"],
            skip={"HW_DESC", "SLAVE_ID", "MACROS", "CONFIG", "CALLED_FROM_CFG_SLAVE"},
        )

    def _discover_axis_cmd_param_defs(self) -> list[dict[str, str]]:
        return self._discover_cmd_param_defs(
            script_rel_path="scripts/jinja2/loadYamlAxis.cmd",
            preferred=["DEV", "PREFIX"],
            skip={"FILE"},
        )

    def _discover_plc_cmd_param_defs(self) -> list[dict[str, str]]:
        return self._discover_cmd_param_defs(
            script_rel_path="scripts/loadPLCFile.cmd",
            preferred=["PLC_ID", "TMP_PATH", "PRINT_PLC_FILE", "SUBST_FILE", "INC", "DESC"],
            skip={"FILE", "SAMPLE_RATE_MS", "PLC_MACROS"},
        )

    def _selected_obj_index(self) -> int:
        sel = self.obj_tree.selection()
        if not sel:
            return -1
        m = re.match(r"obj_(\\d+)$", sel[0])
        if not m:
            return -1
        return _as_int(m.group(1), default=-1)

    def _select_obj_index(self, idx: int) -> None:
        item_id = f"obj_{idx}"
        if self.obj_tree.exists(item_id):
            self.obj_tree.selection_set(item_id)
            self.obj_tree.focus(item_id)
            self.obj_tree.see(item_id)

    def _insert_index(self, after_selected: bool) -> int:
        if not after_selected:
            return len(self.objects)
        idx = self._selected_obj_index()
        if idx < 0:
            return len(self.objects)
        return min(len(self.objects), idx + 1)

    def _refresh_object_tree(self) -> None:
        self.obj_tree.delete(*self.obj_tree.get_children(""))
        for idx, obj in enumerate(self.objects):
            summary = self._object_summary(obj)
            self.obj_tree.insert("", "end", iid=f"obj_{idx}", text=f"{idx + 1:02d}", values=(obj.kind.upper(), summary))

    def _object_summary(self, obj: ProjectObj) -> str:
        if obj.kind == "slave":
            s: SlaveObj = obj.data
            if s.macros.strip():
                return f"SLAVE_ID={s.slave_id}, HW_DESC={s.hw_desc}, MACROS={s.macros}"
            return f"SLAVE_ID={s.slave_id}, HW_DESC={s.hw_desc}"
        if obj.kind == "axis":
            a: AxisObj = obj.data
            return f"FILE={a.file}, AXIS_ID={a.axis_id}, AX_NAME={a.axis_name}"
        if obj.kind == "plc":
            p: PlcObj = obj.data
            return f"FILE={p.file}, SAMPLE_RATE_MS={p.sample_rate_ms}"
        return ""

    def _extend_rows_with_param_defs(
        self,
        rows: list[tuple[str, str]],
        current_params: dict[str, str],
        param_defs: list[dict[str, str]],
    ) -> None:
        def_names = {p["name"] for p in param_defs}
        for pdef in param_defs:
            name = pdef["name"]
            current = (current_params.get(name, "") or "").strip()
            if current:
                rows.append((name, current))
            else:
                default_val = (pdef.get("default", "") or "").strip()
                rows.append((name, f"<default: {default_val}>" if default_val else ""))
        for key in sorted(k for k in current_params.keys() if k not in def_names):
            rows.append((key, current_params.get(key, "")))

    def _ordered_param_items(
        self,
        current_params: dict[str, str],
        param_defs: list[dict[str, str]],
    ) -> list[tuple[str, str]]:
        ordered_names = [p["name"] for p in param_defs if p["name"] in current_params]
        ordered_names.extend(sorted(k for k in current_params.keys() if k not in set(ordered_names)))
        return [(name, current_params[name]) for name in ordered_names]

    def _format_cmd_assignments(
        self,
        items: list[tuple[str, str]],
        quote_keys: set[str] | None = None,
    ) -> str:
        quote_keys = quote_keys or set()
        rendered: list[str] = []
        for key, raw in items:
            value = (str(raw) if raw is not None else "").strip()
            if not value:
                continue
            already_quoted = (value.startswith("'") and value.endswith("'")) or (
                value.startswith('"') and value.endswith('"')
            )
            needs_quote = key in quote_keys or ("," in value) or (" " in value)
            if needs_quote and not already_quoted:
                value = "'" + value.replace("'", "\\'") + "'"
            rendered.append(f"{key}={value}")
        return ", ".join(rendered)

    def _object_params(self, obj: ProjectObj) -> list[tuple[str, str]]:
        if obj.kind == "slave":
            s: SlaveObj = obj.data
            rows: list[tuple[str, str]] = [
                ("SLAVE_ID", str(s.slave_id)),
                ("HW_DESC", s.hw_desc),
                ("MACROS", s.macros),
            ]
            self._extend_rows_with_param_defs(rows, s.params, self.add_slave_param_defs)
            return rows
        if obj.kind == "axis":
            a: AxisObj = obj.data
            rows = [
                ("FILE", a.file),
                ("AX_NAME", a.axis_name),
                ("AXIS_ID", str(a.axis_id)),
                ("DRV_SID", a.drv_sid),
                ("ENC_SID", a.enc_sid),
                ("DRV_CH", a.drv_ch),
                ("ENC_CH", a.enc_ch),
            ]
            self._extend_rows_with_param_defs(rows, a.params, self.axis_cmd_param_defs)
            return rows
        if obj.kind == "plc":
            p: PlcObj = obj.data
            rows = [("FILE", p.file), ("SAMPLE_RATE_MS", p.sample_rate_ms), ("PLC_MACROS", p.macros)]
            self._extend_rows_with_param_defs(rows, p.params, self.plc_cmd_param_defs)
            return rows
        return []

    def _refresh_param_tree(self, obj: ProjectObj | None) -> None:
        self.param_tree.delete(*self.param_tree.get_children(""))
        if obj is None:
            return
        for name, value in self._object_params(obj):
            self.param_tree.insert("", "end", text=name, values=(value,))

    def _on_object_select(self, _event=None) -> None:
        self._stash_editor_to_buffer()
        idx = self._selected_obj_index()
        if not (0 <= idx < len(self.objects)):
            self.current_edit_obj_idx = -1
            self.current_edit_file = None
            self.editor_file_var.set("(select axis/plc object)")
            self.editor_text.delete("1.0", self.tk.END)
            self._refresh_param_tree(None)
            return
        self.current_edit_obj_idx = idx
        obj = self.objects[idx]
        self._refresh_param_tree(obj)
        self._open_editor_for_object(obj)

    def _on_object_right_click(self, event) -> str | None:
        row_id = self.obj_tree.identify_row(event.y)
        if row_id:
            self.obj_tree.selection_set(row_id)
            self.obj_tree.focus(row_id)
        try:
            self.obj_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.obj_menu.grab_release()
        return "break"

    def _open_editor_for_object(self, obj: ProjectObj) -> None:
        if obj.kind == "axis":
            a: AxisObj = obj.data
            rel = self._normalize_rel_path(a.file, default=f"cfg/axis_{a.axis_id:02d}_{_slug(a.axis_name)}.yaml")
            a.file = rel
            self.current_edit_file = rel
            if rel not in self.file_buffers:
                self.file_buffers[rel] = self._default_axis_yaml(a)
            self.editor_file_var.set(rel)
            self.editor_text.delete("1.0", self.tk.END)
            self.editor_text.insert(self.tk.END, self.file_buffers[rel])
            return
        if obj.kind == "plc":
            p: PlcObj = obj.data
            rel = self._normalize_rel_path(p.file, default="cfg/main.plc")
            p.file = rel
            self.current_edit_file = rel
            if rel not in self.file_buffers:
                self.file_buffers[rel] = self._default_plc()
            self.editor_file_var.set(rel)
            self.editor_text.delete("1.0", self.tk.END)
            self.editor_text.insert(self.tk.END, self.file_buffers[rel])
            return
        self.current_edit_file = None
        self.editor_file_var.set("(no editable file for this object)")
        self.editor_text.delete("1.0", self.tk.END)

    def _apply_editor_changes(self) -> None:
        self._stash_editor_to_buffer()
        if self.current_edit_file:
            self.status_var.set(f"Applied editor changes to buffer: {self.current_edit_file}")

    def _stash_editor_to_buffer(self) -> None:
        if self.current_edit_file is None:
            return
        self.file_buffers[self.current_edit_file] = self.editor_text.get("1.0", "end-1c")

    def _normalize_rel_path(self, value: str, default: str) -> str:
        rel = value.strip().replace("\\\\", "/")
        if not rel:
            rel = default
        if rel.startswith("./"):
            rel = rel[2:]
        return rel

    def _slave_selector_popup(self, current: SlaveObj | None = None) -> SlaveObj | None:
        import tkinter as tk
        from tkinter import filedialog, ttk

        self._refresh_supported_hw()

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Slave")
        dialog.transient(self.root)
        dialog.geometry("820x560")
        dialog.grab_set()

        result: SlaveObj | None = None
        filter_var = tk.StringVar(value="")
        sid_var = tk.StringVar(value=str(current.slave_id if current is not None else self._next_slave_id()))
        manual_var = tk.StringVar(value=current.hw_desc if current is not None else "")
        macros_var = tk.StringVar(value=current.macros if current is not None else "")
        esi_file_var = tk.StringVar(value=self.default_esi_file)
        esi_name_var = tk.StringVar(value="*")
        esi_rev_var = tk.StringVar(value="*")
        param_vars: dict[str, tk.StringVar] = {}
        for pdef in self.add_slave_param_defs:
            pname = pdef["name"]
            default_value = ""
            if current is not None:
                default_value = current.params.get(pname, "")
            param_vars[pname] = tk.StringVar(value=default_value)

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Filter").pack(side=tk.LEFT)
        filt_entry = ttk.Entry(row, textvariable=filter_var, width=36)
        filt_entry.pack(side=tk.LEFT, padx=(6, 8))
        ttk.Label(row, text="SLAVE_ID").pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=sid_var, width=8).pack(side=tk.LEFT, padx=(6, 0))

        body = ttk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        listbox = tk.Listbox(body, exportselection=False)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scroll.set)

        details = tk.Text(frame, wrap=tk.WORD, height=8)
        details.pack(fill=tk.X, pady=(8, 0))
        details.configure(state=tk.DISABLED)

        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row2, text="Manual HW_DESC").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=manual_var, width=48).pack(side=tk.LEFT, padx=(6, 0))

        row2b = ttk.Frame(frame)
        row2b.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(row2b, text="MACROS").pack(side=tk.LEFT)
        ttk.Entry(row2b, textvariable=macros_var, width=60).pack(side=tk.LEFT, padx=(6, 0))

        if self.add_slave_param_defs:
            extra = ttk.LabelFrame(frame, text="addSlave.cmd extra parameters", padding=6)
            extra.pack(fill=tk.X, pady=(8, 0))
            max_cols = 2
            for idx, pdef in enumerate(self.add_slave_param_defs):
                pname = pdef["name"]
                row_no = idx // max_cols
                col_base = (idx % max_cols) * 2
                ttk.Label(extra, text=pname).grid(row=row_no, column=col_base, sticky=tk.W, padx=(0, 6), pady=(0, 4))
                ttk.Entry(extra, textvariable=param_vars[pname], width=20).grid(
                    row=row_no, column=col_base + 1, sticky=tk.W, padx=(0, 12), pady=(0, 4)
                )

        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(row3, text="ESI file").pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=esi_file_var, width=46).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(
            row3,
            text="Browse...",
            command=lambda: _pick_popup_esi_file(),
        ).pack(side=tk.LEFT, padx=(6, 0))

        row4 = ttk.Frame(frame)
        row4.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(row4, text="Name").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=esi_name_var, width=14).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row4, text="Rev").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=esi_rev_var, width=14).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Button(
            row4,
            text="Add HW Support via ESI Browser...",
            command=lambda: _open_esi_from_popup(),
        ).pack(side=tk.LEFT)

        def set_details(text: str) -> None:
            details.configure(state=tk.NORMAL)
            details.delete("1.0", tk.END)
            details.insert(tk.END, text)
            details.configure(state=tk.DISABLED)

        def _pick_popup_esi_file() -> None:
            picked = filedialog.askopenfilename(
                title="Select ESI XML file",
                filetypes=(("XML files", "*.xml"), ("All files", "*.*")),
            )
            if picked:
                esi_file_var.set(picked)

        def _open_esi_from_popup() -> None:
            self._open_esi_mapping_browser(
                esi_file=esi_file_var.get().strip(),
                name_pattern=esi_name_var.get().strip() or "*",
                rev_pattern=esi_rev_var.get().strip() or "*",
            )
            self.default_esi_file = esi_file_var.get().strip()
            self._refresh_supported_hw()
            refresh_list()

        def refresh_list(_event=None) -> None:
            filt = filter_var.get().strip().lower()
            listbox.delete(0, tk.END)
            for desc in self.supported_hw_descs:
                if filt and filt not in desc.lower():
                    continue
                listbox.insert(tk.END, desc)
            set_details("Select supported HW_DESC or type manual value.")

        def on_select(_event=None) -> None:
            sel = listbox.curselection()
            if not sel:
                return
            desc = listbox.get(sel[0])
            manual_var.set(desc)
            paths = self.supported_hw_by_desc.get(desc, [])
            rows = [f"HW_DESC: {desc}", ""]
            if paths:
                rows.append("Command files:")
                for path in paths:
                    rows.append(f"  - {path}")
            else:
                rows.append("(No command file path found)")
            set_details("\\n".join(rows))

        def apply_and_close() -> None:
            nonlocal result
            sid = _as_int(sid_var.get(), default=-1)
            hw = manual_var.get().strip()
            if sid < 0 or not hw:
                return
            params: dict[str, str] = {}
            for pdef in self.add_slave_param_defs:
                pname = pdef["name"]
                value = (param_vars[pname].get() or "").strip()
                if value:
                    params[pname] = value
            result = SlaveObj(
                slave_id=sid,
                hw_desc=hw,
                macros=(macros_var.get() or "").strip(),
                params=params,
            )
            dialog.destroy()

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Add", command=apply_and_close).pack(side=tk.RIGHT, padx=(0, 6))

        filt_entry.bind("<KeyRelease>", refresh_list)
        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Double-1>", lambda _e: apply_and_close())
        refresh_list()
        filt_entry.focus_set()

        dialog.wait_window()
        return result

    def _axis_popup(self, current: AxisObj | None = None) -> AxisObj | None:
        fields = {
            "file": current.file if current else f"cfg/axis_{self._next_axis_id():02d}_m{self._next_axis_id()}.yaml",
            "axis_id": str(current.axis_id if current else self._next_axis_id()),
            "axis_name": current.axis_name if current else f"M{self._next_axis_id()}",
            "drv_sid": current.drv_sid if current else "${DRV_SID}",
            "enc_sid": current.enc_sid if current else "${ENC_SID}",
            "drv_ch": current.drv_ch if current else "01",
            "enc_ch": current.enc_ch if current else "01",
        }
        field_defs: list[tuple[str, str, int]] = [
            ("file", "FILE", 42),
            ("axis_name", "AX_NAME", 16),
            ("axis_id", "AXIS_ID", 8),
            ("drv_sid", "DRV_SID", 16),
            ("enc_sid", "ENC_SID", 16),
            ("drv_ch", "DRV_CH", 8),
            ("enc_ch", "ENC_CH", 8),
        ]
        known_extra_names = {p["name"] for p in self.axis_cmd_param_defs}
        if current is not None:
            for name, value in current.params.items():
                if name not in known_extra_names:
                    self.axis_cmd_param_defs.append({"name": name, "default": "", "desc": ""})
                    known_extra_names.add(name)
        for pdef in self.axis_cmd_param_defs:
            pname = pdef["name"]
            field_defs.append((pname, pname, 18))
            fields[pname] = current.params.get(pname, "") if current is not None else ""
        res = self._generic_fields_popup(
            title="Axis Object",
            fields=field_defs,
            defaults=fields,
        )
        if not res:
            return None
        params: dict[str, str] = {}
        for pdef in self.axis_cmd_param_defs:
            pname = pdef["name"]
            value = (res.get(pname, "") or "").strip()
            if value:
                params[pname] = value
        return AxisObj(
            file=self._normalize_rel_path(res["file"], default=fields["file"]),
            axis_id=_as_int(res["axis_id"], default=_as_int(fields["axis_id"], default=1)),
            axis_name=(res["axis_name"].strip() or fields["axis_name"]),
            drv_sid=(res["drv_sid"].strip() or "${DRV_SID}"),
            enc_sid=(res["enc_sid"].strip() or "${ENC_SID}"),
            drv_ch=(res["drv_ch"].strip() or "01"),
            enc_ch=(res["enc_ch"].strip() or "01"),
            params=params,
        )

    def _plc_popup(self, current: PlcObj | None = None) -> PlcObj | None:
        defaults = {
            "file": current.file if current else self._suggest_plc_file(),
            "sample_rate_ms": current.sample_rate_ms if current else "100",
            "macros": current.macros if current else "DBG=",
        }
        field_defs: list[tuple[str, str, int]] = [
            ("file", "FILE", 42),
            ("sample_rate_ms", "SAMPLE_RATE_MS", 12),
            ("macros", "PLC_MACROS", 42),
        ]
        known_extra_names = {p["name"] for p in self.plc_cmd_param_defs}
        if current is not None:
            for name in current.params.keys():
                if name not in known_extra_names:
                    self.plc_cmd_param_defs.append({"name": name, "default": "", "desc": ""})
                    known_extra_names.add(name)
        for pdef in self.plc_cmd_param_defs:
            pname = pdef["name"]
            field_defs.append((pname, pname, 22))
            defaults[pname] = current.params.get(pname, "") if current is not None else ""
        res = self._generic_fields_popup(
            title="PLC Object",
            fields=field_defs,
            defaults=defaults,
        )
        if not res:
            return None
        params: dict[str, str] = {}
        for pdef in self.plc_cmd_param_defs:
            pname = pdef["name"]
            value = (res.get(pname, "") or "").strip()
            if value:
                params[pname] = value
        return PlcObj(
            file=self._normalize_rel_path(res["file"], default=defaults["file"]),
            sample_rate_ms=(res["sample_rate_ms"].strip() or "100"),
            macros=res["macros"].strip(),
            params=params,
        )

    def _generic_fields_popup(
        self,
        title: str,
        fields: list[tuple[str, str, int]],
        defaults: dict[str, str],
    ) -> dict[str, str] | None:
        import tkinter as tk
        from tkinter import ttk

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        vars_map = {key: tk.StringVar(value=defaults.get(key, "")) for key, _label, _w in fields}
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        for row, (key, label, width) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=(0, 6))
            ttk.Entry(frame, textvariable=vars_map[key], width=width).grid(row=row, column=1, sticky=tk.W, padx=(8, 0), pady=(0, 6))

        result: dict[str, str] | None = None

        def apply_and_close() -> None:
            nonlocal result
            result = {k: v.get() for k, v in vars_map.items()}
            dialog.destroy()

        btns = ttk.Frame(frame)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky=tk.E, pady=(8, 0))
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="OK", command=apply_and_close).pack(side=tk.RIGHT, padx=(0, 6))

        first_key = fields[0][0] if fields else None
        if first_key:
            dialog.after(10, lambda: frame.focus_set())
        dialog.wait_window()
        return result

    def _next_slave_id(self) -> int:
        ids = [obj.data.slave_id for obj in self.objects if obj.kind == "slave"]
        return 0 if not ids else max(ids) + 1

    def _next_axis_id(self) -> int:
        ids = [obj.data.axis_id for obj in self.objects if obj.kind == "axis"]
        return 1 if not ids else max(ids) + 1

    def _suggest_plc_file(self) -> str:
        used = {obj.data.file for obj in self.objects if obj.kind == "plc"}
        if "cfg/main.plc" not in used:
            return "cfg/main.plc"
        idx = 2
        while True:
            cand = f"cfg/main_{idx}.plc"
            if cand not in used:
                return cand
            idx += 1

    def _add_slave(self, after_selected: bool) -> None:
        picked = self._slave_selector_popup()
        if not picked:
            return
        sid = picked.slave_id
        existing = {obj.data.slave_id for obj in self.objects if obj.kind == "slave"}
        if sid in existing:
            self.status_var.set(f"SLAVE_ID {sid} already exists.")
            return
        idx = self._insert_index(after_selected)
        self.objects.insert(idx, ProjectObj("slave", picked))
        self._refresh_object_tree()
        self._select_obj_index(idx)
        self.status_var.set(f"Added slave at position {idx + 1}")

    def _add_axis(self, after_selected: bool) -> None:
        axis = self._axis_popup()
        if axis is None:
            return
        idx = self._insert_index(after_selected)
        self.objects.insert(idx, ProjectObj("axis", axis))
        self._refresh_object_tree()
        self._select_obj_index(idx)
        self.status_var.set(f"Added axis at position {idx + 1}")

    def _add_plc(self, after_selected: bool) -> None:
        plc = self._plc_popup()
        if plc is None:
            return
        idx = self._insert_index(after_selected)
        self.objects.insert(idx, ProjectObj("plc", plc))
        self._refresh_object_tree()
        self._select_obj_index(idx)
        self.status_var.set(f"Added plc at position {idx + 1}")

    def _edit_selected_object(self) -> None:
        idx = self._selected_obj_index()
        if not (0 <= idx < len(self.objects)):
            return
        obj = self.objects[idx]
        if obj.kind == "slave":
            s: SlaveObj = obj.data
            picked = self._slave_selector_popup(current=s)
            if not picked:
                return
            sid = picked.slave_id
            existing = {i: o.data.slave_id for i, o in enumerate(self.objects) if o.kind == "slave" and i != idx}
            if sid in existing.values():
                self.status_var.set(f"SLAVE_ID {sid} already exists.")
                return
            self.objects[idx] = ProjectObj("slave", picked)
        elif obj.kind == "axis":
            a: AxisObj = obj.data
            updated = self._axis_popup(current=a)
            if updated is None:
                return
            self.objects[idx] = ProjectObj("axis", updated)
        elif obj.kind == "plc":
            p: PlcObj = obj.data
            updated = self._plc_popup(current=p)
            if updated is None:
                return
            self.objects[idx] = ProjectObj("plc", updated)
        self._refresh_object_tree()
        self._select_obj_index(idx)

    def _move_selected_object(self, delta: int) -> None:
        idx = self._selected_obj_index()
        if not (0 <= idx < len(self.objects)):
            return
        new_idx = idx + delta
        if not (0 <= new_idx < len(self.objects)):
            return
        obj = self.objects.pop(idx)
        self.objects.insert(new_idx, obj)
        self._refresh_object_tree()
        self._select_obj_index(new_idx)
        self.status_var.set(f"Moved object to position {new_idx + 1}")

    def _remove_selected_object(self) -> None:
        idx = self._selected_obj_index()
        if not (0 <= idx < len(self.objects)):
            return
        self._stash_editor_to_buffer()
        removed = self.objects.pop(idx)
        self._refresh_object_tree()
        if idx < len(self.objects):
            self._select_obj_index(idx)
        elif self.objects:
            self._select_obj_index(len(self.objects) - 1)
        else:
            self._refresh_param_tree(None)
            self.editor_file_var.set("(select axis/plc object)")
            self.editor_text.delete("1.0", self.tk.END)
            self.current_edit_file = None
            self.current_edit_obj_idx = -1
        self.status_var.set(f"Removed {removed.kind} object")

    def _default_axis_yaml(self, axis: AxisObj) -> str:
        return "\n".join(
            [
                "axis:",
                f"  id: {axis.axis_id}",
                "",
                "epics:",
                f"  name: {axis.axis_name}",
                "  precision: 3",
                "  description: Auto-generated engineering template",
                "  unit: mm",
                "",
                "drive:",
                "  type: 0",
                "  numerator: 10",
                "  denominator: 32768",
                "  setpoint: ec0.s$(DRV_SID).velocitySetpoint${DRV_CH=01}",
                "  control: ec0.s$(DRV_SID).driveControl${DRV_CH=01}",
                "  status: ec0.s$(DRV_SID).driveStatus${DRV_CH=01}",
                "",
                "encoder:",
                "  type: 1",
                "  bits: 32",
                "  absBits: 26",
                "  position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}",
                "  status: ec0.s$(ENC_SID).encoderStatus${ENC_CH=01}",
                "",
            ]
        ) + "\n"

    def _default_plc(self) -> str:
        return "\n".join(
            [
                "if(${SELF}.firstscan) {",
                "  var plc:=${SELF_ID};",
                "  ${DBG=#}println('PLC ',plc,' startup');",
                "};",
                "",
                "# Example:",
                "substitute \"DRV_CH=01\"",
                "include \"plc_templates/drive_watchdog.plc_inc\"",
                "",
            ]
        ) + "\n"

    def _build_startup(self) -> str:
        lines: list[str] = []
        lines.append("# startup.cmd")
        lines.append("#- Auto-generated by ecmc_engineering_studio.py")
        lines.append("require ecmccfg")
        lines.append('epicsEnvSet("IOC"                      "${IOC=IOC_TEST}")')
        lines.append("")
        lines.append("#- Ordered project objects")
        lines.append("")
        for idx, obj in enumerate(self.objects):
            if obj.kind == "slave":
                s: SlaveObj = obj.data
                args: list[tuple[str, str]] = [("SLAVE_ID", str(s.slave_id)), ("HW_DESC", s.hw_desc)]
                if s.macros.strip():
                    args.append(("MACROS", s.macros))
                args.extend(self._ordered_param_items(s.params, self.add_slave_param_defs))
                lines.append(f"#- [{idx + 1}] SLAVE")
                lines.append(
                    '${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       '
                    f"\"{self._format_cmd_assignments(args, quote_keys={'MACROS'})}\""
                )
            elif obj.kind == "axis":
                a: AxisObj = obj.data
                args = [
                    ("FILE", f"./{a.file}"),
                    ("DEV", "${IOC}"),
                    ("AX_NAME", a.axis_name),
                    ("AXIS_ID", str(a.axis_id)),
                    ("DRV_SID", a.drv_sid),
                    ("ENC_SID", a.enc_sid),
                    ("DRV_CH", a.drv_ch),
                    ("ENC_CH", a.enc_ch),
                ]
                args.extend(self._ordered_param_items(a.params, self.axis_cmd_param_defs))
                lines.append(f"#- [{idx + 1}] AXIS")
                lines.append(
                    '${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   '
                    f"\"{self._format_cmd_assignments(args)}\""
                )
            elif obj.kind == "plc":
                p: PlcObj = obj.data
                args = [
                    ("FILE", f"./{p.file}"),
                    ("SAMPLE_RATE_MS", p.sample_rate_ms),
                    ("PLC_MACROS", p.macros or "DBG="),
                ]
                args.extend(self._ordered_param_items(p.params, self.plc_cmd_param_defs))
                lines.append(f"#- [{idx + 1}] PLC")
                lines.append(
                    '${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd,    '
                    f"\"{self._format_cmd_assignments(args, quote_keys={'PLC_MACROS'})}\""
                )
            lines.append("")
        return "\n".join(lines)

    def _refresh_generated_list(self) -> None:
        self._stash_editor_to_buffer()
        generated = {"startup.cmd": self._build_startup()}
        for obj in self.objects:
            if obj.kind == "axis":
                a: AxisObj = obj.data
                rel = self._normalize_rel_path(a.file, default=f"cfg/axis_{a.axis_id:02d}_{_slug(a.axis_name)}.yaml")
                if rel not in self.file_buffers:
                    self.file_buffers[rel] = self._default_axis_yaml(a)
                generated[rel] = self.file_buffers[rel]
            elif obj.kind == "plc":
                p: PlcObj = obj.data
                rel = self._normalize_rel_path(p.file, default="cfg/main.plc")
                if rel not in self.file_buffers:
                    self.file_buffers[rel] = self._default_plc()
                generated[rel] = self.file_buffers[rel]
        self.generated_files = generated
        self.status_var.set(f"Prepared {len(self.generated_files)} files for save.")

    def _save_all(self) -> None:
        self._refresh_generated_list()
        outdir = Path(self.output_dir_var.get().strip() or ".").expanduser()
        outdir.mkdir(parents=True, exist_ok=True)
        for rel, content in self.generated_files.items():
            path = outdir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.status_var.set(f"Saved {len(self.generated_files)} files to {outdir}")

    def _open_esi_mapping_browser(
        self,
        esi_file: str = "",
        name_pattern: str = "*",
        rev_pattern: str = "*",
    ) -> None:
        from tkinter import messagebox

        browser_script = Path(__file__).resolve().with_name("esi_mapping_browser.py")
        if not browser_script.exists():
            messagebox.showerror("Missing tool", f"Could not find:\n{browser_script}")
            return

        cmd = [sys.executable, str(browser_script)]
        if esi_file:
            cmd.extend(["--file", esi_file])
        cmd.extend(["--name", name_pattern or "*", "--rev", rev_pattern or "*"])
        try:
            subprocess.Popen(cmd, cwd=str(browser_script.parent))
        except Exception as exc:
            messagebox.showerror("Launch failed", f"Could not launch ESI Mapping Browser:\n{exc}")
            return
        self.status_var.set("Opened ESI Mapping Browser.")


def build_arg_parser() -> argparse.ArgumentParser:
    root = _find_ecmccfg_root() or Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="ecmc Engineering Studio GUI")
    parser.add_argument("--outdir", default=str(root / "examples" / "engineering_output"), help="Default output directory")
    parser.add_argument("--esi-file", default="", help="Default ESI file path")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    try:
        import tkinter as tk
    except Exception as exc:
        print(f"GUI unavailable: {exc}", file=sys.stderr)
        return 2

    root = tk.Tk()
    EngineeringStudio(root, outdir=Path(args.outdir).expanduser(), default_esi_file=args.esi_file)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
