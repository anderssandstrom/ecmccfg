"""EL7411 OPT/CSTCA integration; captures commands without accessing hardware."""
import itertools
import re
import unittest
import xml.etree.ElementTree as ET

import test_ex72xx_opt as harness
from test_ex72xx_opt import Startup, InvalidConfiguration, ROOT, HW, MODELS, legacy_entries


class El7411OptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        harness.OptTests.setUpClass()
        cls.helper=harness.OptTests()

    def test_defaults_preserve_legacy_csv_and_csp(self):
        for mode,file in [('CSV',HW/'ecmcEX72XX_CSV.cmd'),('CSP',HW/'EL/ecmcEL7411_CSP.cmd')]:
            with self.subTest(mode=mode):
                s=Startup('EL7411',dict(MODE=mode))
                self.assertEqual(s.entries(),legacy_entries(file))
                self.helper.check_records_and_panels(s)
                self.assertEqual(s.env['ECMC_EC_COMP_TYPE'],'EL7411')
                self.assertEqual(s.env['ECMC_EC_PRODUCT_ID'],'0x1cf33052')
                self.assertEqual(s.env['ECMC_HW_PANEL'],'EX72XX_OPT')
                self.assertFalse(any(key.startswith(('ECMC_EX72XX_OPT_','ECMC_EL7411_OPT_')) for key in s.env))
                db=self.helper.database(s)
                self.assertIn('field(ESLO, "1")',db)
                self.assertNotIn('ComAngle',db)
                self.assertNotIn('TrqOff',db)
                self.assertNotIn('Enc01-Stat',db)

    def test_all_modes_and_optional_pdos(self):
        for mode,tp,info,diag in itertools.product(['CSV','CSP','CST','CSTCA'],['0','1'],['NONE','INPUTS','TEMP'],['0','1']):
            with self.subTest(mode=mode,tp=tp,info=info,diag=diag):
                s=Startup('EL7411',dict(MODE=mode,TP=tp,INFO2=info,DIAG=diag))
                cfg=self.helper.check_records_and_panels(s)
                entries=s.entries()
                code=dict(CSV=9,CSP=8,CST=10,CSTCA=11)[mode]
                mode_sdos=[c for c in s.commands if c.startswith('Cfg.EcAddSdo(1,0x7010,0x03,')]
                self.assertEqual(mode_sdos,[f'Cfg.EcAddSdo(1,0x7010,0x03,{code},1)'])
                self.assertEqual(cfg['TEST:CfgMode'],['CSV','CSP','CST','CSTCA'].index(mode))
                self.assertEqual('commutationAngle01' in entries,mode=='CSTCA')
                self.assertEqual('torqueSetpoint01' in entries,mode in ['CST','CSTCA'])
                self.assertEqual('touchProbeStatus01' in entries,tp=='1')
                self.assertEqual('velocityActual01' in entries,diag=='1')
                self.assertEqual('torqueActual01' in entries,diag=='1')
                self.assertEqual('voltageActual01' in entries,diag=='1')
                self.assertEqual('followingError01' in entries,mode=='CSP' and diag=='1')
                self.assertEqual('binaryInputs01' in entries,info=='INPUTS')
                self.assertEqual('temperatureActual01' in entries,info=='TEMP')
                if info!='NONE':
                    selection=10 if info=='INPUTS' else 4
                    self.assertIn(f'Cfg.EcWriteSdo(1,0x8010,0x3A,{selection},1)',s.commands)
                self.assertNotIn('torqueOffset01',entries)
                self.assertNotIn('encoderStatus01',entries)
                if mode=='CSTCA':
                    self.assertEqual(entries['commutationAngle01'],((1,2,0x1603,0x7010,0x0e),'U16'))
                    self.assertEqual(entries['torqueSetpoint01'],((1,2,0x1602,0x7010,9),'S16'))

    def test_angle_pvs_scale_bounds_and_panel(self):
        s=Startup('EL7411',dict(MODE_1='CSTCA'))
        db=self.helper.database(s)
        for typ,suffix in [('ao','ComAngle'),('ai','ComAngle-RB')]:
            body=re.search(r'record\('+typ+r',\s*"TEST:Drv01-'+suffix+r'"\)\s*\{(.*?)\n\}',db,re.S)[1]
            self.assertIn('commutationAngle01',body)
            self.assertIn('0.0054931640625',body)
            self.assertRegex(body,r'field\(EGU,\s*"deg"\)')
            if typ=='ao':
                self.assertIn('359.9945068359375',body)
                self.assertRegex(body,r'field\(DRVL,\s*"0"\)')
                self.assertRegex(body,r'field\(DRVH,\s*"359.9945068359375"\)')
        scale=0.0054931640625
        self.assertEqual(scale*65536,360)
        self.assertEqual(scale*65535,359.9945068359375)
        root=ET.parse(ROOT/'qt/ecmcEX72XX_OPT_cstca.ui').getroot()
        target=root.find(".//widget[@name='commutationAngle']")
        self.assertEqual(target.get('class'),'caTextEntry')
        self.assertEqual(target.findtext("property[@name='readOnly']/bool"),'false')
        self.assertTrue(target.findtext("property[@name='channel']/string").endswith('-ComAngle'))
        self.helper.check_records_and_panels(s)

    def test_hardware_enable_uses_bit12(self):
        db=self.helper.database(Startup('EL7411',dict(INFO2='INPUTS')))
        body=re.search(r'record\(bi,\s*"TEST:Drv01-STO01"\)\s*\{(.*?)\n\}',db,re.S)[1]
        self.assertIn('TEST:Drv01-InfoData2.BC',body)
        self.assertNotIn('InfoData2.B8',body)

    def test_invalid_choices_fail_before_reset(self):
        for options in [dict(MODE='BAD'),dict(MODE_2='CSTCA'),dict(INFO2='ERRORS'),
                        dict(ENC_STAT='1'),dict(ENC_STAT_1='1'),dict(TP='2'),dict(DIAG='2')]:
            with self.subTest(options=options):
                with self.assertRaises(InvalidConfiguration):Startup('EL7411',options)
    def test_el7411_timing_and_overrides(self):
        for rate in [500,1000,2000]:
            s=Startup('EL7411',rate=rate)
            period=1000000000//rate
            self.assertIn(f'Cfg.EcSlaveConfigDC(1,0x700,62500,0,{period-62500},0)',s.commands)
            self.assertIn('Cfg.EcAddSdo(1,0x8011,0x11,1000,4)',s.commands)
            for index in ['0x1C32','0x1C33']:
                self.assertIn(f'Cfg.EcAddSdo(1,{index},0x1,3,2)',s.commands)
                self.assertIn(f'Cfg.EcAddSdo(1,{index},0x2,{period},4)',s.commands)
            self.assertFalse(any('PortWiring' in c for c in s.commands))
        s=Startup('EL7411',dict(SYNC_0_CYCLE='125000',SYNC_0_SHIFT='123',
                               SYNC_1_CYCLE='1000000',SYNC_1_SHIFT='456',
                               WATCHDOG_DIVIDER='200',WATCHDOG_INTERVALS='300'))
        self.assertIn('Cfg.EcSlaveConfigDC(1,0x700,125000,123,1000000,456)',s.commands)
        self.assertIn('Cfg.EcSlaveConfigWatchDog(1,200,300)',s.commands)


if __name__=='__main__':unittest.main()
