"""Tests for hardware defaults selected from an EtherCAT slave ID."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from resolveAxisHardwareProfiles import deep_merge, preprocess, resolve, select_profiles


class TestProfiles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        for model in ("EL7041", "EL5101"):
            (self.root / model).mkdir()
        (self.root / "EL7041" / "drive.yaml").write_text(
            "drive:\n  type: 0\n  numerator: 10\n  denominator: 32768\n"
            "  control: ec$(MASTER).s$(SLAVE).driveControl01\n")
        (self.root / "EL5101" / "encoder.yaml").write_text(
            "encoder:\n  type: 0\n  filter:\n    velocity:\n      enable: true\n      size: 100\n")
        self.env = {"ECMC_HW_M0_S7": "EL7041-0052",
                    "ECMC_HW_M0_S8": "EL5101", "ECMC_EC_MASTER_ID": "0"}

    def test_slave_lookup_variant_fallback_and_override(self):
        axis = {"drive": {"slave": 7, "numerator": 20},
                "encoder": {"slave": 8, "filter": {"velocity": {"enable": False}}}}
        data = resolve(axis, self.root, self.env)
        self.assertEqual(data["drive"], {
            "type": 0, "numerator": 20, "denominator": 32768,
            "control": "ec0.s7.driveControl01"})
        self.assertEqual(data["encoder"]["filter"]["velocity"], {"enable": False, "size": 100})
        self.assertNotIn("slave", data["drive"])
        self.assertNotIn("slave", data["encoder"])

    def test_ioc_slave_macros(self):
        axis = {"drive": {"slave": "$(DRV_SLAVE)"},
                "encoder": {"slave": "$(ENC_SLAVE)"}}
        env = dict(self.env, DRV_SLAVE="7", ENC_SLAVE="8")
        resolved = resolve(axis, self.root, env)
        self.assertEqual(resolved["drive"]["control"], "ec0.s7.driveControl01")
        self.assertEqual(resolved["encoder"]["type"], 0)

    def test_macro_default_and_nested_macros(self):
        axis = {"drive": {"slave": "$(DRV_SLAVE=7)"}}
        resolved = resolve(axis, self.root, self.env)
        self.assertEqual(resolved["drive"]["type"], 0)
        env = dict(self.env, DRV_SLAVE="$(AXIS_SLAVE)", AXIS_SLAVE="7")
        self.assertEqual(resolve({"drive": {"slave": "$(DRV_SLAVE)"}},
                                 self.root, env)["drive"]["type"], 0)

    def test_macro_master(self):
        env = {"MASTER_ID": "1", "DRV_SLAVE": "7",
               "ECMC_HW_M1_S7": "EL7041"}
        axis = {"drive": {"master": "$(MASTER_ID)", "slave": "$(DRV_SLAVE)"}}
        resolved = resolve(axis, self.root, env)
        self.assertEqual(resolved["drive"]["control"], "ec1.s7.driveControl01")
        self.assertNotIn("master", resolved["drive"])

    def test_missing_and_recursive_macros_rejected(self):
        for value, env in (
            ("$(UNKNOWN)", self.env),
            ("$(DRV_SLAVE)", dict(self.env, DRV_SLAVE="$(DRV_SLAVE)")),
            ("$(DRV_SLAVE)", dict(self.env, DRV_SLAVE="xyz")),
        ):
            with self.subTest(value=value, env=env), self.assertRaises(ValueError):
                resolve({"drive": {"slave": value}}, self.root, env)

    def test_cli_preprocessing_expands_macros(self):
        source, target = self.root / "macro-axis.yaml", self.root / "resolved.yaml"
        source.write_text("drive:\n  slave: $(DRV_SLAVE)\n  numerator: 20\n")
        preprocess(source, target, self.root, dict(self.env, DRV_SLAVE="7"))
        self.assertEqual(__import__("yaml").safe_load(target.read_text())["drive"]["numerator"], 20)
        self.assertNotIn("slave", __import__("yaml").safe_load(target.read_text())["drive"])

    def test_el7062_two_channels_and_macro(self):
        model = self.root / "EL7062"
        model.mkdir()
        (model / "drive.yaml").write_text(
            "channels: 2\ndrive:\n  type: 1\n"
            "  setpoint: ec$(MASTER).s$(SLAVE).velocitySetpoint$(CHANNEL)\n"
            "  status: ec$(MASTER).s$(SLAVE).driveStatus$(CHANNEL)\n")
        (model / "encoder.yaml").write_text(
            "channels: 2\nencoder:\n"
            "  position: ec$(MASTER).s$(SLAVE).positionActual$(CHANNEL)\n")
        env = dict(self.env, ECMC_HW_M0_S9="EL7062", DRV_CHANNEL="2")
        axis = {
            "drive": {"slave": 9, "channel": "$(DRV_CHANNEL)"},
            "encoder": {"slave": 9, "channel": "$(DRV_CHANNEL)"},
        }
        out = resolve(axis, self.root, env)
        self.assertEqual(out["drive"]["type"], 1)
        self.assertEqual(out["drive"]["setpoint"], "ec0.s9.velocitySetpoint02")
        self.assertEqual(out["drive"]["status"], "ec0.s9.driveStatus02")
        self.assertEqual(out["encoder"]["position"], "ec0.s9.positionActual02")
        self.assertNotIn("channel", out["drive"])
        self.assertNotIn("channel", out["encoder"])
        axis["drive"]["channel"] = 1
        self.assertEqual(resolve(axis, self.root, env)["drive"]["setpoint"],
                         "ec0.s9.velocitySetpoint01")

    def test_el7062_encoder_feedback_both_channels(self):
        model = self.root / "EL7062"
        model.mkdir()
        (model / "encoder.yaml").write_text(
            "channels: 2\nencoder:\n  type: 0\n  source: 0\n"
            "  denominator: 12800\nfeedbacks:\n"
            "  openloop:\n"
            "    position: ec$(MASTER).s$(SLAVE).positionActual$(CHANNEL)\n"
            "  incremental:\n"
            "    position: ec$(MASTER).s$(SLAVE).positionActual$(CHANNEL)_2\n")
        env = dict(self.env, ECMC_HW_M0_S9="EL7062", ENC_FEEDBACK="incremental")
        for channel in (1, 2):
            for feedback, suffix in (("openloop", ""), ("incremental", "_2")):
                with self.subTest(channel=channel, feedback=feedback):
                    cfg = {"encoder": {"slave": 9, "channel": channel,
                                       "feedback": feedback, "numerator": 2.0}}
                    out = resolve(cfg, self.root, env)["encoder"]
                    self.assertEqual(out["position"],
                                     "ec0.s9.positionActual%02d%s" % (channel, suffix))
                    self.assertEqual(out["numerator"], 2.0)
                    self.assertEqual(out["denominator"], 12800)
                    self.assertNotIn("feedback", out)
                    self.assertNotIn("channel", out)

        selected = resolve({"encoder": {"slave": 9, "feedback": "$(ENC_FEEDBACK)"}},
                           self.root, env)["encoder"]
        self.assertEqual(selected["position"], "ec0.s9.positionActual01_2")
        default = resolve({"encoder": {"slave": 9}}, self.root, env)["encoder"]
        self.assertEqual(default["position"], "ec0.s9.positionActual01")

        for name in ("absolute", "", 1):
            with self.subTest(unsupported=name), self.assertRaises(ValueError):
                resolve({"encoder": {"slave": 9, "feedback": name}}, self.root, env)

    def test_feedback_rejected_for_profile_without_variants(self):
        with self.assertRaisesRegex(ValueError, "does not support feedback"):
            resolve({"encoder": {"slave": 8, "feedback": "incremental"}},
                    self.root, self.env)

    def test_real_el7062_profile_and_jinja_command_snippets(self):
        try:
            import jinja2
        except ImportError:
            self.skipTest("jinja2 is not installed")
        root = pathlib.Path(__file__).resolve().parents[1]
        profiles = root / "hardwareProfiles"
        templates = root / "templates"
        env = {"ECMC_HW_M0_S7": "EL7062"}
        axis = {"drive": {"slave": 7, "channel": 2, "numerator": 10.0},
                "encoder": {"slave": 7, "channel": 2,
                            "feedback": "incremental", "numerator": 1.0}}
        selected = select_profiles(axis, profiles, env)
        self.assertEqual(selected["drive"]["data"]["type"], 1)
        self.assertEqual(selected["drive"]["data"]["setpoint"],
                         "ec0.s7.velocitySetpoint02")
        self.assertEqual(selected["encoder"]["data"]["position"],
                         "ec0.s7.positionActual02_2")
        self.assertTrue(selected["drive"]["snippet"])
        self.assertTrue(selected["encoder"]["snippet"])
        renderer = jinja2.Environment(loader=jinja2.FileSystemLoader(str(root)))
        # The command hook is in templates; its included snippets are in
        # hardwareProfiles. Include using that directory as a second loader.
        renderer.loader = jinja2.FileSystemLoader([str(templates), str(root)])
        output = renderer.get_template("hardwareDefaults.jinja2").render(
            hardware=selected)
        self.assertIn("Cfg.SetAxisDrvScaleDenom(", output)
        self.assertIn("Cfg.SetAxisEncScaleDenom(", output)
        self.assertIn("positionActual02_2", output)
        self.assertIn("velocitySetpoint02", output)
        self.assertLess(output.index("Cfg.SetAxisEncScaleDenom("),
                        output.index("Cfg.LinkEcEntryToObject(ec0.s7.positionActual02_2"))

        axis["drive"]["denominator"] = 200
        axis["encoder"]["denominator"] = 400
        selected = select_profiles(axis, profiles, env)
        output = renderer.get_template("hardwareDefaults.jinja2").render(
            hardware=selected)
        # Hardware defaults are emitted even when the axis overrides them.
        # The normal axis templates apply explicit values afterwards.
        self.assertIn("Cfg.SetAxisDrvScaleDenom(${ECMC_AXIS_NO},2147483648)", output)
        self.assertIn("Cfg.SetAxisEncScaleDenom(${ECMC_AXIS_NO},1048576)", output)
        self.assertIn("positionActual02_2", output)
        self.assertIn("velocitySetpoint02", output)
        resolved = resolve(axis, profiles, env)
        self.assertEqual(resolved["drive"]["denominator"], 200)
        self.assertEqual(resolved["encoder"]["denominator"], 400)

    def test_invalid_channel_rejected(self):
        for channel in (0, 2, -1, True, "$(MISSING)", "abc"):
            with self.subTest(channel=channel), self.assertRaises(ValueError):
                resolve({"drive": {"slave": 7, "channel": channel}},
                        self.root, self.env)

    def test_default_channel_one(self):
        resolved = resolve({"drive": {"slave": 7}}, self.root, self.env)
        self.assertEqual(resolved["drive"]["control"], "ec0.s7.driveControl01")

    def test_original_yaml_unchanged_without_selectors(self):
        source, target = self.root / "axis.yaml", self.root / "result.yaml"
        text = "# comment\naxis:\n  id: 1\ndrive:\n  numerator: 1\n"
        source.write_text(text)
        preprocess(source, target, self.root, {})
        self.assertEqual(target.read_text(), text)

    def test_unknown_slave_fails(self):
        with self.assertRaisesRegex(ValueError, "not registered"):
            resolve({"drive": {"slave": 9}}, self.root, self.env)

    def test_explicit_unknown_profile_fails(self):
        with self.assertRaises(FileNotFoundError):
            resolve({"drive": {"slave": 7}},
                    self.root, {"ECMC_HW_M0_S7": "MISSING"})

    def test_malformed_slave_fails(self):
        for slave in (-1, True, "../../etc"):
            with self.subTest(slave=slave), self.assertRaises(ValueError):
                resolve({"drive": {"slave": slave}}, self.root, self.env)

    def test_false_zero_none_override(self):
        self.assertEqual(deep_merge({"a": True, "b": 1, "c": 12},
                                    {"a": False, "b": 0, "c": None}),
                         {"a": False, "b": 0, "c": None})

    def test_legacy_not_modified(self):
        value = {"drive": {"numerator": 1, "status": "ec0.s7.status"}}
        self.assertEqual(resolve(value, self.root, {}), value)

    def test_reject_old_hardware_selector(self):
        with self.assertRaisesRegex(ValueError, "not supported"):
            resolve({"hardwareProfiles": {"drive": "EL7041"}}, self.root, self.env)


if __name__ == "__main__":
    unittest.main()
