"""EL/ED/MO7062 OPT integration, captured commands only; no hardware access.

Run: python3 -m unittest discover -s tests -p 'test_ex*opt.py'
"""
import itertools
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import test_ex72xx_opt as harness
from test_ex72xx_opt import Startup, InvalidConfiguration, ROOT, HW, legacy_entries


class Ex7062OptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        harness.OptTests.setUpClass()
        cls.helper = harness.OptTests()

    def check(self, startup):
        return self.helper.check_records_and_panels(startup)

    def test_defaults_match_legacy_process_image(self):
        # Ignore commented-out entries when extracting the legacy baseline.
        source = (HW / 'EL/ecmcEX7062.cmd').read_text()
        with tempfile.TemporaryDirectory() as temp:
            legacy = Path(temp) / 'legacy.cmd'
            legacy.write_text('\n'.join(l for l in source.splitlines() if not l.lstrip().startswith('#')))
            expected = legacy_entries(legacy)
        for model in ['EL7062', 'ED7062', 'MO7062-0100']:
            with self.subTest(model=model):
                s = Startup(model)
                self.assertEqual(s.entries(), expected)
                self.check(s)
                db = self.helper.database(s)
                for channel in ['01','02']:
                    for suffix in ['Spd', 'Spd-RB', 'Cmd', 'Stat', 'BI01', 'BI02',
                                   'TrgDS402Ena', 'TrgDS402Dis', 'TuneTrg', 'Tune-Arr']:
                        self.assertIn(f'"TEST:Drv{channel}-{suffix}"', db)
                    self.assertIn(f'"TEST:Enc{channel}-PosAct02"', db)
                self.assertIn('"TEST:Drv01-VltAct"', db)
                self.assertIn('"TEST:Drv01-TmpAct"', db)
                self.assertFalse(any(k.startswith('EX7062_') for k in s.env))

    def test_el_ed_option_matrix(self):
        # Combine modes and each independent boolean pair with other features on/off.
        for model, mode, enabled in itertools.product(['EL7062','ED7062'], ['CSV','CSP','CST'], ['0','1']):
            opts = dict(MODE=mode, TP=enabled, INPUTS=enabled, ENC2=enabled,
                        DIAG=enabled, EXT_DIAG=enabled, AUTOTUNE=enabled, TP_DC=enabled)
            with self.subTest(model=model, mode=mode, enabled=enabled):
                s = Startup(model,opts)
                self.check(s)
                entries=s.entries()
                for ch, out in [('01','0x7010'),('02','0x7110')]:
                    demand=dict(CSV='velocitySetpoint',CSP='positionSetpoint',CST='torqueSetpoint')[mode]
                    self.assertIn(demand+ch,entries)
                    code=dict(CSV=9,CSP=8,CST=10)[mode]
                    self.assertIn(f'Cfg.EcWriteSdo(1,{out},0x03,{code},1)',s.commands)
                    self.assertIn(f'Cfg.EcAddSdo(1,{out},0x03,{code},1)',s.commands)
                    for entry in ['binaryInputs','touchProbeControl','touchProbeStatus','velocityActual','torqueActual']:
                        self.assertEqual(entry+ch in entries,enabled=='1')
                    self.assertEqual('positionActual'+ch+'_2' in entries,enabled=='1')
                    self.assertEqual('touchProbeTimestampPos'+ch+'_1' in entries,enabled=='1')
                    self.assertEqual('followingError'+ch in entries,enabled=='1' and mode=='CSP')
                self.assertEqual('voltageActual01' in entries,enabled=='1')
                self.assertNotIn('voltageActual02',entries)

    def test_independent_options_and_channels(self):
        # Individually disable features and exercise each diagnostic in isolation.
        for option in ['TP','INPUTS','ENC2','AUTOTUNE','DIAG','EXT_DIAG','TP_DC']:
            value = '1' if option in ['EXT_DIAG','TP_DC'] else '0'
            with self.subTest(option=option):
                self.check(Startup('ED7062',{option:value}))
        s=Startup('ED7062',dict(MODE_1='CSP',MODE_2='CST',TP_1='0',TP_2='1',
                               TP_DC_2='1',ENC2_1='0',INPUTS_2='0',EXT_DIAG_1='1',
                               EXT_DIAG_2='0',AUTOTUNE_2='0'))
        cfg=self.check(s)
        self.assertEqual(cfg['TEST:CfgMode'],1)
        self.assertEqual(cfg['TEST:CfgMode02'],2)
        self.assertIn('followingError01',s.entries())
        self.assertNotIn('touchProbeStatus01',s.entries())
        self.assertIn('touchProbeTimestampNeg02_1',s.entries())
        self.assertNotIn('positionActual01_2',s.entries())

    def test_invalid_choices_fail_before_reset(self):
        for opts in [dict(MODE='BAD'),dict(MODE_2='bad'),dict(TP='2'),dict(INPUTS='yes'),
                     dict(ENC2='-1'),dict(EXT_DIAG='true'),dict(AUTOTUNE='2'),
                     dict(TP_DC='1',TP='0'),dict(DIAG='3'),dict(DIAG_2='0'),
                     dict(INFO2='INPUTS'),dict(ENC_STAT='1'),dict(ENC_STAT_2='0')]:
            with self.subTest(opts=opts):
                with self.assertRaises(InvalidConfiguration):Startup('ED7062',opts)
        for opts in [dict(MODE='CSP'),dict(MODE_2='CST'),dict(TP='0'),dict(INPUTS='0'),
                     dict(ENC2='0'),dict(DIAG='0'),dict(EXT_DIAG='1'),dict(TP_DC='1')]:
            with self.subTest(mo=opts):
                with self.assertRaises(InvalidConfiguration):Startup('MO7062-0100',opts)
        self.check(Startup('MO7062-0100',dict(AUTOTUNE='0')))

    def test_timing_and_no_port_wiring_checks(self):
        for model in ['EL7062','ED7062','MO7062-0100']:
            for rate in [500,1000,2000]:
                s=Startup(model,dict(SYNC_0_SHIFT='200000'),rate=rate)
                period=1000000000//rate
                self.assertIn(f'Cfg.EcSlaveConfigDC(1,0x700,62500,200000,{period-62500},0)',s.commands)
                self.assertIn('Cfg.EcSetSlaveTimingOverride(1,2,-1,155000,31250)',s.commands)
                self.assertFalse(any('Port' in c for c in s.commands))

    def test_config_records_load_in_epics(self):
        softioc=shutil.which('softIoc')
        if not softioc or not self.helper.msi:
            self.skipTest('EPICS softIoc/msi is not installed')
        with tempfile.TemporaryDirectory() as temp:
            for mode in ['CSV','CSP','CST']:
                s=Startup('ED7062',dict(MODE=mode,EXT_DIAG='1',TP_DC='1'))
                s.substitutions=[]
                s.templates=[item for item in s.templates if 'Config.template' in item[0] or
                             item[0]=='ecmcEX7062_OPT_config.template']
                database=Path(temp)/'config.db'
                database.write_text(self.helper.database(s))
                process=subprocess.run([softioc],input=f'dbLoadRecords("{database}")\nexit\n',
                                       capture_output=True,text=True,timeout=15,check=True)
                self.assertNotIn('ERROR',process.stdout+process.stderr)
                self.assertNotIn('Illegal choice',process.stdout+process.stderr)

    def test_panels_compile(self):
        uic=shutil.which('uic-qt5') or shutil.which('uic')
        if not uic:self.skipTest('Qt uic is not installed')
        with tempfile.TemporaryDirectory() as temp:
            for panel in (ROOT/'qt').glob('ecmcEX7062_OPT*.ui'):
                subprocess.run([uic,str(panel),'-o',str(Path(temp)/(panel.stem+'.h'))],
                               capture_output=True,text=True,check=True)


if __name__=='__main__':unittest.main()
