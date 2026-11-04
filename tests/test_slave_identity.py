"""Check identity startup gating and static EPICS records without hardware."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from test_ex72xx_opt import Startup, ROOT


class SlaveIdentityTests(unittest.TestCase):
    def startup(self, env=None, scope=None):
        source = (ROOT / 'scripts/addSlave.cmd').read_text()
        first = source.index('#- Static identity PVs')
        last_line = 'epicsEnvUnset(ECMC_TEMP_SLAVE_IDENTITY_CMD)'
        last = source.index(last_line, first) + len(last_line)
        startup = Startup.__new__(Startup)
        startup.env = dict(SCRIPTEXEC='iocshLoad', ECMC_CONFIG_ROOT='',
                           ECMC_P='TEST:', ECMC_EC_SLAVE_NUM='13')
        startup.env.update(env or {})
        startup.commands, startup.templates = [], []
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'identity.cmd'
            path.write_text(source[first:last])
            startup.run(path, scope or {})
        return startup

    def test_gating_and_status(self):
        for env, scope, status, reads in [
            ({}, {}, 'Not supported', False),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1'}, {}, 'Not read', True),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1', 'ECMC_SIM': '1'}, {}, 'Simulation', False),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1', 'ECMC_DEV_MODE': '1'}, {}, 'Development mode', False),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1'}, {'READ_IDENTITY': '0'}, 'Disabled', False),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1', 'ECMC_READ_SLAVE_IDENTITY': '0'}, {}, 'Disabled', False),
            ({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1', 'ECMC_READ_SLAVE_IDENTITY': '0'}, {'READ_IDENTITY': '1'}, 'Not read', True),
        ]:
            with self.subTest(env=env, scope=scope):
                startup = self.startup(env, scope)
                self.assertEqual(startup.templates,
                                 [('ecmcEcSlave.template', {'IDENTITY_STATUS': status})])
                self.assertEqual(startup.commands,
                                 ['ecmcReadEcSlaveIdentity(13,"TEST:")'] if reads else [])
                self.assertFalse(any(key.startswith('ECMC_TEMP_SLAVE_IDENTITY')
                                     for key in startup.env))

    def test_no_records_means_no_read(self):
        startup = self.startup({'ECMC_EC_SLAVE_IDENTITY_SUPPORTED': '1',
                                'DEFAULT_SLAVE_PVS': 'False'})
        self.assertEqual(startup.templates, [])
        self.assertEqual(startup.commands, [])

    def test_epics_static_records(self):
        msi = shutil.which('msi')
        softioc = shutil.which('softIoc')
        if not msi or not softioc:
            self.skipTest('EPICS msi and softIoc are required')
        source = (ROOT / 'db/core/ecmcEcSlave.template').read_text()
        first = source.index('# Startup snapshots.')
        last = source.index('# This record is used', first)
        with tempfile.TemporaryDirectory() as temp:
            template = Path(temp) / 'identity.template'
            database = Path(temp) / 'identity.db'
            template.write_text(source[first:last])
            output = subprocess.run([msi, '-M', 'ECMC_P=TEST:,ECMC_G=TEST,IDENTITY_STATUS=Simulation',
                                     str(template)], capture_output=True, text=True, check=True).stdout
            database.write_text(output)
            self.assertNotRegex(output, r'\$[({]')
            self.assertEqual(len(re.findall(r'record\(stringin,', output)), 5)
            self.assertNotIn('field(INP', output)
            commands = '\n'.join([
                f'dbLoadRecords("{database}")',
                'dbDumpRecord(0,"stringin",2)', 'exit', ''])
            process = subprocess.run([softioc], input=commands, capture_output=True,
                                     text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertEqual(process.stdout.count('field(VAL,"Unknown")'), 3)
            self.assertEqual(process.stdout.count('field(VAL,"Simulation")'), 2)
            self.assertNotIn('ERROR', process.stdout + process.stderr)


if __name__ == '__main__':
    unittest.main()
