import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.startup_validator.cli import run
from scripts.startup_validator.validator import validate


class StartupValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "cfg").mkdir()
        (self.root / "cfg" / "axis.yaml").write_text("axis:\n  id: 1\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, text: str) -> Path:
        path = self.root / "startup.cmd"
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_current_style_startup(self):
        path = self.write(
            '${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=2,HW_DESC=EL7047"\n'
            '${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=cfg/axis.yaml,DEV=${IOC},DRV_SID=2"\n'
            'ecmcConfigOrDie "Cfg.SetTraceMaskBit(15,0)"\n'
        )
        result = validate(path)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.script_calls, 2)
        self.assertEqual(result.references, ("cfg/axis.yaml",))

    def test_missing_file_is_reported_with_location(self):
        path = self.write('${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=cfg/missing.yaml"\n')
        result = validate(path)
        self.assertEqual(result.errors, 1)
        self.assertEqual(result.diagnostics[0].code, "E301")
        self.assertEqual(result.diagnostics[0].line, 1)

    def test_duplicate_and_malformed_macros_are_rejected(self):
        path = self.write('${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=1,BROKEN,SLAVE_ID=2"\n')
        codes = {item.code for item in validate(path).diagnostics}
        self.assertEqual(codes, {"E201", "E203"})

    def test_unbalanced_macro_and_quote_are_rejected(self):
        path = self.write('${SCRIPTEXEC} "${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=${ID"\n')
        codes = {item.code for item in validate(path).diagnostics}
        self.assertIn("E101", codes)
        self.assertIn("E102", codes)

    def test_legacy_configure_slave_is_a_warning(self):
        path = self.write('${SCRIPTEXEC} ${ecmccfg_DIR}configureSlave.cmd "HW_DESC=EL7037"\n')
        result = validate(path)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.warnings, 1)
        self.assertEqual(result.diagnostics[0].code, "W301")

    def test_installed_template_name_is_not_treated_as_local_file(self):
        path = self.write('${SCRIPTEXEC} ${ecmccfg_DIR}applySubstitutions.cmd "SUBST_FILE=ecmcEL7047.substitutions"\n')
        self.assertEqual(validate(path).errors, 0)

    def test_cli_exit_status(self):
        good = self.write('ecmcConfigOrDie "Cfg.SetTraceMaskBit(15,0)"\n')
        with redirect_stdout(StringIO()):
            good_status = run([str(good)])
        self.assertEqual(good_status, 0)
        bad = self.write('${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=missing.yaml"\n')
        with redirect_stdout(StringIO()):
            bad_status = run([str(bad), "--format", "json"])
        self.assertEqual(bad_status, 1)


if __name__ == "__main__":
    unittest.main()
