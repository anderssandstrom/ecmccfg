"""Regression tests for Jinja-native family/variant hardware profiles."""
import json
import pathlib
import unittest

import jinja2

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "hardwareProfiles"


def render(axis, env):
    loader = jinja2.FileSystemLoader([str(ROOT / "templates"), str(ROOT)])
    template = jinja2.Environment(loader=loader).get_template(
        "hardwareProfiles/renderDefaults.jinja2")
    result = json.loads(template.render(axis_config=axis, hardware_env=env))
    if "__hardware_profile_error__" in result:
        raise ValueError(result["__hardware_profile_error__"])
    return result


class HardwareProfileTests(unittest.TestCase):
    def test_legacy_unchanged(self):
        axis = {"drive": {"setpoint": "ec0.s2.velocitySetpoint01"},
                "input": {"limit": {"forward": "plcOverride", "backward": "plcOverride"}}}
        self.assertEqual(render(axis, {}), axis)

    def test_el7041_csv_and_override(self):
        axis = {"axis": {"mode": "CSV"},
                "drive": {"slave": 7, "numerator": 10.0, "denominator": 99},
                "encoder": {"slave": 7, "numerator": 1.0}}
        got = render(axis, {"ECMC_HW_M0_S7": "EL7041", "ECMC_HW_SCRIPT_M0_S7": "EL7041"})
        self.assertEqual(got["drive"]["setpoint"], "ec0.s7.velocitySetpoint01")
        self.assertEqual(got["drive"]["denominator"], 99)
        self.assertEqual(got["encoder"]["denominator"], 12800)
        self.assertEqual(got["encoder"]["position"], "ec0.s7.positionActual01")

    def test_el7047_csp(self):
        got = render({"axis": {"mode": "CSP"},
                      "drive": {"slave": 7, "numerator": 1.0}},
                     {"ECMC_HW_M0_S7": "EL7047",
                      "ECMC_HW_SCRIPT_M0_S7": "EL7047_CSP"})
        self.assertEqual(got["drive"]["setpoint"], "ec0.s7.positionSetpoint01")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            render({"axis": {"mode": "CSV"}, "drive": {"slave": 7}},
                   {"ECMC_HW_M0_S7": "EL7047",
                    "ECMC_HW_SCRIPT_M0_S7": "EL7047_CSP"})

    def test_el7062_feedback_and_swapped_inputs(self):
        axis = {"axis": {"mode": "CSV"},
                "drive": {"slave": "$(SLAVE=7)", "channel": "$(CH=2)"},
                "encoder": {"slave": 7, "channel": 2, "feedback": "incremental"},
                "input": {"limit": {"swap": "$(SWAP=true)"}}}
        got = render(axis, {"ECMC_HW_M0_S7": "EL7062",
                            "ECMC_HW_SCRIPT_M0_S7": "EL7062",
                            "CH": "2"})
        self.assertEqual(got["drive"]["setpoint"], "ec0.s7.velocitySetpoint02")
        self.assertEqual(got["encoder"]["position"], "ec0.s7.positionActual02_2")
        self.assertEqual(got["input"]["limit"]["forward"], "ec0.s7.binaryInputs02.0")
        self.assertEqual(got["input"]["limit"]["backward"], "ec0.s7.binaryInputs02.1")
        self.assertNotIn("swap", got["input"]["limit"])

    def test_encoder_terminals(self):
        for model, bits in [("EL5042", 64), ("EL5102", 32)]:
            with self.subTest(model=model):
                got = render({"encoder": {"slave": 5, "channel": 2, "numerator": 360.0}},
                             {"ECMC_HW_M0_S5": model})
                self.assertEqual(got["encoder"]["position"], "ec0.s5.positionActual02")
                self.assertEqual(got["encoder"]["bits"], bits)
                self.assertEqual(got["encoder"]["numerator"], 360.0)

    def test_servo_variants(self):
        for model in ("EL7201_RES", "EL7211_OCT", "EL7221_OCT"):
            with self.subTest(model=model):
                got = render({"axis": {"mode": "CSV"}, "drive": {"slave": 7}},
                             {"ECMC_HW_M0_S7": model,
                              "ECMC_HW_SCRIPT_M0_S7": "EL7211-9014_STD"})
                self.assertEqual(got["drive"]["setpoint"], "ec0.s7.velocitySetpoint01")

    def test_opt_requires_explicit_mapping(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            render({"axis": {"mode": "CSV"}, "drive": {"slave": 7}},
                   {"ECMC_HW_M0_S7": "EL7211_OCT",
                    "ECMC_HW_SCRIPT_M0_S7": "EL7211-9014_OPT"})


if __name__ == "__main__":
    unittest.main()
