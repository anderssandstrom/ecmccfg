"""Regression tests for Jinja-native family/variant hardware profiles."""
import json
import pathlib
import unittest

import jinja2

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT  # Installed scripts are flattened into the module root.


def render(axis, env):
    loader = jinja2.FileSystemLoader([str(ROOT / "templates"), str(ROOT)])
    template = jinja2.Environment(loader=loader).get_template(
        "hwProfileResolve.jinja2")
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

    def test_el70xx_openloop_default_denominator(self):
        for model in ("EL7031", "EL7037", "EL7041", "EL7047"):
            with self.subTest(model=model):
                env = {"ECMC_HW_M0_S7": model, "ECMC_HW_SCRIPT_M0_S7": model}
                got = render({"encoder": {"slave": 7, "numerator": 1.0}}, env)
                self.assertEqual(got["encoder"]["denominator"], 12800)
                override = render({"encoder": {"slave": 7, "numerator": 1.0,
                                               "denominator": 12345}}, env)
                self.assertEqual(override["encoder"]["denominator"], 12345)


    def test_index_homing_latch_profiles(self):
        for model, channel in (("EL5101", 1), ("EL5102", 1), ("EL5102", 2), ("EL7062", 1), ("EL7062", 2)):
            for home_type in (11, 12):
                with self.subTest(model=model, channel=channel, home_type=home_type):
                    enc = {"slave": 7, "channel": channel, "numerator": 1,
                           "denominator": 4096, "homing": {"type": home_type, "position": 0}}
                    if model == "EL7062":
                        enc["feedback"] = "incremental"
                    result = render({"encoder": enc},
                                    {"ECMC_HW_M0_S7": model, "ECMC_HW_SCRIPT_M0_S7": model})["encoder"]
                    suffix = f"{channel:02d}"
                    latch = result["latch"]
                    if model == "EL7062":
                        self.assertEqual(result["position"], f"ec0.s7.positionActual{suffix}_2")
                        self.assertEqual(result["control"], f"ec0.s7.touchProbeControl{suffix}")
                        self.assertEqual(result["status"], f"ec0.s7.touchProbeStatus{suffix}")
                        self.assertEqual(latch["position"], f"ec0.s7.touchProbePositionPos{suffix}_1")
                        self.assertEqual((latch["control"], latch["status"], latch["armCmd"], latch["armBits"]), (0, 1, 17, 5))
                    else:
                        self.assertEqual(result["control"], f"ec0.s7.encoderControl{suffix}")
                        self.assertEqual(result["status"], f"ec0.s7.encoderStatus{suffix}")
                        self.assertEqual(latch["position"], f"ec0.s7.encoderLatchPosition{suffix}")
                        self.assertEqual((latch["control"], latch["status"], latch["armCmd"], latch["armBits"]), (0, 0, 1, 1))

    def test_index_homing_override_and_validation(self):
        env = {"ECMC_HW_M0_S7": "EL5102"}
        enc = {"slave": 7, "numerator": 1, "denominator": 4096,
               "homing": {"type": 11}, "latch": {"armCmd": 3}}
        got = render({"encoder": enc}, env)["encoder"]
        self.assertEqual(got["latch"]["armCmd"], 3)
        self.assertEqual(got["latch"]["armBits"], 1)
        got = render({"encoder": {"slave": 7, "numerator": 1,
                                    "denominator": 4096}}, env)["encoder"]
        self.assertNotIn("latch", got)
        with self.assertRaisesRegex(ValueError, "oversampling"):
            render({"encoder": {"slave": 7, "homing": {"type": 11}}},
                   {"ECMC_HW_M0_S7": "EL5101", "ECMC_HW_SCRIPT_M0_S7": "EL5101-0011"})
        with self.assertRaisesRegex(ValueError, "requires encoder.feedback"):
            render({"encoder": {"slave": 7, "homing": {"type": 12}}},
                   {"ECMC_HW_M0_S7": "EL7062"})

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

    def test_el5021_sincos_encoder(self):
        got = render({"encoder": {"slave": 11, "numerator": 360.0,
                                  "denominator": 65536}},
                     {"ECMC_HW_M0_S11": "EL5021",
                      "ECMC_HW_SCRIPT_M0_S11": "EL5021"})
        self.assertEqual(got["encoder"]["position"], "ec0.s11.positionActual01")
        self.assertEqual(got["encoder"]["bits"], 32)
        self.assertEqual(got["encoder"]["type"], 0)
        self.assertEqual(got["encoder"]["denominator"], 65536)
        self.assertEqual(got["encoder"]["numerator"], 360.0)
        with self.assertRaisesRegex(ValueError, "Unsupported channel"):
            render({"encoder": {"slave": 11, "channel": 2}},
                   {"ECMC_HW_M0_S11": "EL5021"})

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
