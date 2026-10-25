"""Cross-record checks on expanded OPT databases, without hardware access."""
import re
import unittest

import test_ex72xx_opt as harness


class DatabaseIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        harness.OptTests.setUpClass()
        helper = harness.OptTests()
        cls.databases = []
        for model in harness.MODELS + ['EL7411']:
            for mode in ['CSV', 'CSP', 'CST', 'CSTCA']:
                startup = harness.Startup(model, dict(MODE=mode, DIAG='1'))
                cls.databases.append((f'{model}/{mode}', helper.database(startup)))
        for model in ['EL7062', 'ED7062', 'MO7062-0100']:
            cls.databases.append((model, helper.database(harness.Startup(model))))

    def test_no_unexpanded_macros(self):
        for label, database in self.databases:
            with self.subTest(configuration=label):
                self.assertNotRegex(database, r'\$[({]')

    def test_calculations_fit_epics_fields(self):
        for label, database in self.databases:
            for field, value in re.findall(r'field\(\s*(CALC|OCAL)\s*,\s*"([^"]*)"\)', database):
                with self.subTest(configuration=label, field=field, expression=value):
                    self.assertLessEqual(len(value.encode('utf-8')), 79)

    def test_local_record_links_resolve(self):
        # Slave auto-tune sequences also link to the shared master's EcTool.
        core = (harness.ROOT / 'db/core/ecmcEc.db').read_text()
        master_names = {
            harness.expand(name, dict(P='TEST:', ECMC_EC_MP='m', MASTER_ID='0'))
            for name in re.findall(r'record\(\w+,\s*"([^"]+)"', core)
            if '-EcTool' in name
        }
        for label, database in self.databases:
            names = set(re.findall(r'record\(\w+,\s*"([^"]+)"', database)) | master_names
            links = re.findall(r'field\(\s*(INP[A-L]?|OUT[A-L]?|FLNK|DOL|LNK[0-9A-F])\s*,\s*"([^"]*)"\)', database)
            for field, link in links:
                # Numeric constants and @asyn device links are not local PVs.
                if not link.startswith('TEST:'):
                    continue
                target = link.split()[0].split('.', 1)[0]
                with self.subTest(configuration=label, field=field, target=target):
                    self.assertIn(target, names)


if __name__ == '__main__':
    unittest.main()
