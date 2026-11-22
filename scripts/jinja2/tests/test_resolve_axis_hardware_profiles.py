"""Unit tests: python -m unittest discover -s scripts/jinja2/tests -p test_resolve_axis_hardware_profiles.py"""
import pathlib
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from resolveAxisHardwareProfiles import deep_merge, preprocess, resolve


class TestProfiles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / "EL7041").mkdir()
        (self.root / "EL7041" / "drive.yaml").write_text(
            "drive:\n  type: 0\n  numerator: 10\n  denominator: 32768\n")
        (self.root / "EL5101").mkdir()
        (self.root / "EL5101" / "encoder.yaml").write_text(
            "encoder:\n  type: 0\n  filter:\n    velocity:\n      enable: true\n      size: 100\n")

    def test_override_and_deep_merge(self):
        data = {"hardwareProfiles": {"drive": "EL7041", "encoder": "EL5101"},
                "drive": {"numerator": 20},
                "encoder": {"filter": {"velocity": {"enable": False}}}}
        result = resolve(data, self.root)
        self.assertEqual(result["drive"], {"type": 0, "numerator": 20, "denominator": 32768})
        self.assertEqual(result["encoder"]["filter"]["velocity"], {"enable": False, "size": 100})
        self.assertNotIn("hardwareProfiles", result)

    def test_without_profiles_copy_unchanged(self):
        src, dest = self.root / "source.yaml", self.root / "target.yaml"
        original = "# application comment\ndrive:\n  numerator: 1\n"
        src.write_text(original)
        preprocess(src, dest, self.root)
        self.assertEqual(dest.read_text(), original)

    def test_missing_profile_fails(self):
        with self.assertRaises(FileNotFoundError):
            resolve({"hardwareProfiles": {"drive": "UNKNOWN"}}, self.root)

    def test_bad_profile_name_fails(self):
        with self.assertRaises(ValueError):
            resolve({"hardwareProfiles": {"drive": "../../etc"}}, self.root)

    def test_false_and_null_override(self):
        self.assertEqual(deep_merge({"a": True, "b": 2}, {"a": False, "b": None}),
                         {"a": False, "b": None})

    def test_unknown_section_fails(self):
        with self.assertRaises(ValueError):
            resolve({"hardwareProfiles": {"controller": "EL7041"}}, self.root)


if __name__ == "__main__":
    unittest.main()
