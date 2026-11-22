"""Ensure hardware profiles survive the flat IOC script installation layout."""
from pathlib import Path
import re
import unittest

import jinja2

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "jinja2"
FAMILIES = ("EL70xx", "EL7062", "EL72xx", "EL5021",
            "EL5042", "EL5101", "EL5102")


class InstalledJinjaProfiles(unittest.TestCase):
    def test_gnumakefile_installs_flat_templates(self):
        makefile = (ROOT / "GNUmakefile").read_text()
        self.assertIn("SCRIPTS+=$(wildcard ./scripts/jinja2/*)", makefile)
        for name in ("hwProfileResolve.jinja2", *(
                f"hwProfile{family}.jinja2" for family in FAMILIES)):
            with self.subTest(template=name):
                self.assertTrue((SCRIPTS / name).is_file(), name)

    def test_no_nested_profile_include_needed(self):
        names = ("hwProfileResolve.jinja2", *(
                 f"hwProfile{family}.jinja2" for family in FAMILIES))
        for name in names:
            text = (SCRIPTS / name).read_text()
            self.assertNotIn("hardwareProfiles/", text)

    def test_flat_install_jinja_loader_renders_all_families(self):
        # Exactly the installed IOC searchpath: no source-tree subdirectories.
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(SCRIPTS)))
        template = env.get_template("hwProfileResolve.jinja2")
        for family, component, desc in [
            ("EL70xx", "EL7041", "EL7041-0052"),
            ("EL7062", "EL7062", "EL7062"),
            ("EL72xx", "EL7211_OCT", "EL7211-9014_STD"),
            ("EL5021", "EL5021", "EL5021"),
            ("EL5042", "EL5042", "EL5042"),
            ("EL5101", "EL5101", "EL5101"),
            ("EL5102", "EL5102", "EL5102"),
        ]:
            with self.subTest(family=family):
                section = "drive" if family in ("EL70xx", "EL7062", "EL72xx") else "encoder"
                document = {section: {"slave": 7}}
                if section == "drive":
                    document["axis"] = {"mode": "CSV"}
                content = template.render(axis_config=document, hardware_env={
                    "ECMC_EC_MASTER_ID": "0",
                    "ECMC_HW_M0_S7": component,
                    "ECMC_HW_SCRIPT_M0_S7": desc})
                self.assertIn("ec0.s7.", content)
                self.assertNotIn("__hardware_profile_error__", content)


if __name__ == "__main__":
    unittest.main()
