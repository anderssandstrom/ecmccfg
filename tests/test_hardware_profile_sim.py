"""Offline integration of the dedicated SIM hardware-profile IOC matrix.

No IOC is started, no EtherCAT bus accessed, and no motion commands are sent.
The test checks that every fixture can render through the *real* axis Jinja
and schema pipeline, in addition to checking the dedicated SIM startup plan.
"""
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
JINJA = ROOT / "scripts" / "jinja2"
sys.path.insert(0, str(JINJA))
from ecmcAxes import EcmcAxis

SUITE = ROOT / "tests" / "integration" / "hardware_profiles"
IOC = SUITE / "ioc"
MATRIX = json.loads((SUITE / "matrix.json").read_text())
MACRO = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)(?:=([^()]*))?\)")


def expand_macros(value, env):
    """Substitute IOC macro literals for this isolated test fixture only."""
    if isinstance(value, str):
        def replace(match):
            name, default = match.group(1), match.group(2)
            if name not in env and default is None:
                raise ValueError("Missing fixture macro " + name)
            return str(env.get(name, default))
        return MACRO.sub(replace, value)
    if isinstance(value, dict):
        return {k: expand_macros(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_macros(v, env) for v in value]
    return value


def component_type(desc):
    # Mirrors the actual COMP_TYPE set by the selected hardware scripts.
    if desc.startswith("EL7211-9014"):
        return "EL7211_OCT"
    if desc.startswith("EL7221-9014"):
        return "EL7221_OCT"
    if desc == "EL7201":
        return "EL7201_RES"
    if desc == "EL7041-0052":
        return "EL7041"
    return desc


def environment():
    env = {"ECMC_EC_MASTER_ID": "0"}
    for slave in MATRIX["slaves"]:
        sid, desc = slave["id"], slave["desc"]
        env[f"ECMC_HW_M0_S{sid}"] = component_type(desc)
        env[f"ECMC_HW_SCRIPT_M0_S{sid}"] = desc
    return env


def render_case(case, override=None):
    mapping = {
        "AX_ID": case["id"], "AX_NAME": case["name"],
        "DRV_SLAVE": case["drive"], "ENC_SLAVE": case["enc"],
        "ENC_CH": case["chan"], "DRV_CH": case["chan"],
        "ENC_FEEDBACK": case["fb"],
        "SWAP_LIMITS": str(case["swap"]).lower(),
    }
    if override:
        mapping.update(override)
    filename = IOC / ("axis_el7062.yaml" if case["template"] == "el7062"
                      else "axis_csp.yaml" if case["template"] == "csp"
                      else "axis_csv.yaml")
    document = expand_macros(yaml.safe_load(filename.read_text()), mapping)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "axis.yaml"
        path.write_text(yaml.safe_dump(document, sort_keys=False))
        with patch.dict(os.environ, environment(), clear=False):
            axis = EcmcAxis(path, JINJA / "templates")
            axis.create()
            axis.make()
            return axis.axisTemplate.product


class HardwareProfileSimulation(unittest.TestCase):
    def test_ioc_is_simulation_only_and_covers_matrix(self):
        startup = (IOC / "startup.cmd").read_text()
        self.assertIn("SIM=1", startup)
        self.assertNotIn("SIM=0", startup)
        self.assertNotIn("Cfg.SetIoBackend(0,0)", startup)
        self.assertNotIn("Cfg.Move", startup)
        self.assertNotIn("Cfg.SetAxisEnable(", startup)
        self.assertEqual(len(MATRIX["cases"]), 10)
        for slave in MATRIX["slaves"]:
            self.assertIn(f'SLAVE_ID={slave["id"]},HW_DESC={slave["desc"]}', startup)
        for case in MATRIX["cases"]:
            self.assertIn(f"epicsEnvSet(AX_ID,{case['id']})", startup)
            self.assertIn(f"epicsEnvSet(AX_NAME,{case['name']})", startup)

    def test_all_sim_axes_render_through_real_axis_pipeline(self):
        slaves = {s["id"]: s["desc"] for s in MATRIX["slaves"]}
        for case in MATRIX["cases"]:
            with self.subTest(axis=case["name"]):
                rendered = render_case(case)
                self.assertIn("Cfg.CreateAxis(", rendered)
                self.assertIn(f"ec0.s{case['drive']}.driveControl01", rendered)
                setpoint = ("positionSetpoint01" if case["template"] == "csp"
                            else f"velocitySetpoint{case['chan']:02d}" if case["template"] == "el7062"
                            else "velocitySetpoint01")
                self.assertIn(f"ec0.s{case['drive']}.{setpoint}", rendered)
                enc_name = (f"positionActual{case['chan']:02d}_2" if case["fb"] == "incremental"
                            else f"positionActual{case['chan']:02d}"
                            if slaves[case["enc"]] in ("EL5042", "EL5102")
                            else "positionActual01")
                self.assertIn(f"ec0.s{case['enc']}.{enc_name}", rendered)
                self.assertNotIn("__hardware_profile_error__", rendered)
                if case["template"] == "el7062":
                    bit = 0 if case["swap"] else 1
                    self.assertIn(
                        f"ec0.s9.binaryInputs{case['chan']:02d}.{bit}", rendered)

    def test_csv_csp_mismatch_rejected(self):
        case = next(c for c in MATRIX["cases"] if c["template"] == "csp")
        filename = IOC / "axis_csv.yaml"
        raw = yaml.safe_load(filename.read_text())
        raw = expand_macros(raw, {
            "AX_ID": 19, "AX_NAME": "BAD", "DRV_SLAVE": case["drive"],
            "ENC_SLAVE": case["enc"], "ENC_CH": 1,
        })
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "axis.yaml"
            f.write_text(yaml.safe_dump(raw))
            with patch.dict(os.environ, environment()):
                axis = EcmcAxis(f, JINJA / "templates")
                axis.create()
                with self.assertRaisesRegex(ValueError, "variant/mode mismatch"):
                    axis.make()

    def test_swapped_limits_and_feedback_selection(self):
        case = next(c for c in MATRIX["cases"] if c["name"] == "S7062B")
        result = render_case(case)
        self.assertIn("ec0.s9.positionActual02_2", result)
        self.assertIn("ec0.s9.binaryInputs02.0", result)
        self.assertIn("ec0.s9.binaryInputs02.1", result)
        default = render_case(case, {"SWAP_LIMITS": "false",
                                    "ENC_FEEDBACK": "openloop"})
        self.assertIn("ec0.s9.positionActual02", default)
        self.assertNotIn("ec0.s9.positionActual02_2", default)


if __name__ == "__main__":
    unittest.main()
