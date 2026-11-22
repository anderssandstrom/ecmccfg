"""Tests for hardware defaults selected from an EtherCAT slave ID."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from resolveAxisHardwareProfiles import deep_merge, preprocess, resolve


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
        for slave in (-1, True, "$(SLAVE)", "../../etc"):
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
