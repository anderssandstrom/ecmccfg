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

    def test_add_slave_registers_component_type_with_hw_desc_fallback(self):
        # Component identification belongs in addSlave.cmd; the renderer
        # consumes its registered per-master/per-slave environment variable.
        script = (pathlib.Path(__file__).resolve().parents[2] /
                  "addSlave.cmd").read_text()
        clear = script.index("epicsEnvUnset(ECMC_EC_COMP_TYPE)")
        load = script.index("ecmc${HW_DESC}.cmd")
        register = script.index('epicsEnvSet("ECMC_HW_M')
        self.assertLess(clear, load)
        self.assertLess(load, register)
        self.assertIn('"${ECMC_EC_COMP_TYPE=${HW_DESC}}"', script)

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

    def test_el7062_limit_swapping_and_explicit_override(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        env = {"ECMC_HW_M0_S7": "EL7062"}

        base = {"drive": {"slave": 7, "channel": 2},
                "input": {"limit": {"swap": True}}}
        resolved = resolve(base, profiles, env)
        self.assertEqual(resolved["input"]["limit"]["forward"],
                         "ec0.s7.binaryInputs02.0")
        self.assertEqual(resolved["input"]["limit"]["backward"],
                         "ec0.s7.binaryInputs02.1")
        self.assertNotIn("swap", resolved["input"]["limit"])

        # YAML links override the swapped defaults individually.
        base["input"]["limit"]["forward"] = "ec0.s10.myExternalLimit.3"
        resolved = resolve(base, profiles, env)
        self.assertEqual(resolved["input"]["limit"]["forward"],
                         "ec0.s10.myExternalLimit.3")
        self.assertEqual(resolved["input"]["limit"]["backward"],
                         "ec0.s7.binaryInputs02.1")

        base["input"]["limit"]["swap"] = False
        resolved = resolve(base, profiles, env)
        self.assertEqual(resolved["input"]["limit"]["backward"],
                         "ec0.s7.binaryInputs02.0")

    def test_el7062_limit_swap_macro_and_validation(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        env = {"ECMC_HW_M0_S7": "EL7062", "SWAP_LIMITS": "true"}
        selected = select_profiles(
            {"drive": {"slave": 7},
             "input": {"limit": {"swap": "$(SWAP_LIMITS)"}}},
            profiles, env)
        self.assertEqual(selected["input"]["data"]["limit"]["forward"],
                         "ec0.s7.binaryInputs01.0")
        for value in ("invalid", 2, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_profiles({"drive": {"slave": 7},
                                 "input": {"limit": {"swap": value}}},
                                profiles, env)

    def test_el7041_no_guessed_limit_profile(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        selected = select_profiles(
            {"drive": {"slave": 7},
             "input": {"limit": {"forward": "ec0.s8.fwd.0",
                                 "backward": "ec0.s8.bwd.0"}}},
            profiles, {"ECMC_HW_M0_S7": "EL7041"})
        self.assertNotIn("input", selected)

    def test_new_encoder_channel_profiles(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        for model, enc_type, bits in (("EL5042", 1, 64), ("EL5102", 0, 32)):
            env = {"ECMC_HW_M0_S14": model}
            for channel in (1, 2):
                with self.subTest(model=model, channel=channel):
                    resolved = resolve(
                        {"encoder": {"slave": 14, "channel": channel,
                                     "numerator": 360.0}},
                        profiles, env)["encoder"]
                    self.assertEqual(resolved["position"],
                                     "ec0.s14.positionActual%02d" % channel)
                    self.assertEqual(resolved["type"], enc_type)
                    self.assertEqual(resolved["bits"], bits)
                    self.assertEqual(resolved["numerator"], 360.0)
                    self.assertNotIn("absBits", resolved)
            with self.assertRaisesRegex(ValueError, "exceeds"):
                resolve({"encoder": {"slave": 14, "channel": 3}},
                        profiles, env)

    def test_new_stepper_family_profiles(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        for model in ("EL7031", "EL7037", "EL7047"):
            with self.subTest(model=model):
                env = {"ECMC_HW_M1_S8": model}
                axis = {"drive": {"slave": 8, "master": 1, "denominator": 65432},
                        "encoder": {"slave": 8, "master": 1}}
                result = resolve(axis, profiles, env)
                self.assertEqual(result["drive"]["type"], 0)
                self.assertEqual(result["drive"]["setpoint"],
                                 "ec1.s8.velocitySetpoint01")
                self.assertEqual(result["drive"]["denominator"], 65432)
                self.assertEqual(result["encoder"]["position"],
                                 "ec1.s8.positionActual01")
                self.assertEqual(result["encoder"]["bits"], 16)

    def test_el72xx_component_profiles_and_csv_only(self):
        profiles = pathlib.Path(__file__).resolve().parents[1] / "hardwareProfiles"
        for model in ("EL7201_RES", "EL7201_OCT", "EL7211_RES",
                      "EL7211_OCT", "EL7221_OCT"):
            with self.subTest(model=model):
                env = {"ECMC_HW_M0_S5": model}
                axis = {"axis": {"mode": "CSV"},
                        "drive": {"slave": 5, "numerator": 250.0,
                                  "denominator": 2147483648},
                        "encoder": {"slave": 5, "numerator": 360.0}}
                result = resolve(axis, profiles, env)
                self.assertEqual(result["drive"]["type"], 1)
                self.assertEqual(result["drive"]["setpoint"],
                                 "ec0.s5.velocitySetpoint01")
                self.assertEqual(result["drive"]["denominator"], 2147483648)
                self.assertEqual(result["encoder"]["position"],
                                 "ec0.s5.positionActual01")
                self.assertNotIn("denominator", result["encoder"])
                axis["axis"]["mode"] = "CSP"
                with self.assertRaisesRegex(ValueError, "CSV only"):
                    resolve(axis, profiles, env)

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
