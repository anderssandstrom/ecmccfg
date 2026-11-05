"""Hardware slit configuration checks; never start an IOC or access EtherCAT."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT/'tests/integration/slit/ioc_hardware'
SIM = ROOT/'tests/integration/slit/ioc'


class SlitHardwareConfigTests(unittest.TestCase):
    def test_real_backend_and_confirmed_single_encoder_wiring(self):
        startup = (HW/'startup.cmd').read_text()
        # The installed iocsh launcher uses grep, including comments, to decide
        # whether this file already initializes the IOC. A mention in a comment
        # used to suppress the launcher's automatic call and leave a bare prompt.
        self.assertNotIn('iocInit', startup)
        self.assertIn('dbLoadRecords("./hardware-test.db", "P=${ECMC_PREFIX}")', startup)
        marker = (HW/'hardware-test.db').read_text()
        self.assertIn('HardwareSlitTest:Schema', marker)
        self.assertIn('field(VAL,"1")', marker)
        self.assertIn('SIM=0', startup)
        self.assertIn('HWSLIT', startup)
        self.assertIn('Cfg.SetIoBackend(0,0)', startup)
        self.assertIn('SLAVE_ID=25,HW_DESC=EL2794', startup)
        self.assertEqual(startup.count('loadYamlEnc.cmd'), 1)
        self.assertIn('ENC_SID=9,ENC_CH=01', startup)
        self.assertNotIn('ENC_CH=02', startup)
        self.assertNotIn('CH_ID=2', startup)
        self.assertLess(startup.index('FILE=./cfg/axis_ax6_HI.yaml'), startup.index('loadYamlEnc.cmd'))
        for token in ('SIM=1','SimSetValue','test-marker.db','driveStatus01.13'):
            self.assertNotIn(token, startup)
        self.assertFalse((HW/'profile.json').exists())
        self.assertFalse((HW/'test-marker.db').exists())
        self.assertNotIn('Cfg.SetAxisHomeSwitchEnable', startup)
        self.assertNotIn('Cfg.SetAxisDrvBrake', startup)
        for name in ('axis_main.plc','axis_kin_slit.plc_inc'):
            self.assertEqual((HW/'cfg'/name).read_bytes(), (SIM/'cfg'/name).read_bytes())

    def test_yaml_feedback_roles_and_startup_state(self):
        import yaml
        enc = yaml.safe_load((HW/'cfg/biss-c.yaml').read_text())['encoder']
        self.assertEqual(enc['type'], 1)
        self.assertTrue(enc['primary'])
        self.assertEqual(enc['ready'], 2)
        self.assertEqual(enc['error'], [1])
        self.assertEqual(enc['warning'], 0)
        power = enc['power']
        self.assertTrue(power['enable'])
        self.assertEqual(power['output'], 'ec0.s25.binaryOutput01.0')
        self.assertEqual(power['backup']['encoder'], 1)
        self.assertGreater(power['backup']['maxPositionDifference'], 0)
        for filename in ('axis_ax5_LO.yaml','axis_ax6_HI.yaml','axis_vax5_YCEN.yaml','axis_vax6_YGAP.yaml'):
            document = yaml.safe_load((HW/'cfg'/filename).read_text())
            self.assertFalse(document['axis']['autoEnable']['atStartup'])
            if filename.startswith('axis_ax'):
                self.assertEqual(document['encoder']['type'], 0)
                self.assertNotIn('power',document['encoder'])
                self.assertNotIn('homing',document['encoder'])
                self.assertNotIn('home', document['input'])
                self.assertEqual(document['softlimits']['backward'], -10.0)
                self.assertEqual(document['softlimits']['forward'], 10.0)
                brake = document['drive']['brake']
                self.assertTrue(brake['enable'])
                self.assertEqual(brake['openDelay'], 250)
                self.assertEqual(brake['closeAhead'], 200)
                self.assertTrue(document['monitoring']['target']['enable'])
                self.assertGreater(document['monitoring']['target']['tolerance'], 0)
                for suffix, bit in (('forward',12),('backward',11)):
                    self.assertTrue(document['input']['limit'][suffix].endswith('driveStatus01.'+str(bit)))

    def test_both_yaml_generators(self):
        # Reuse the production parser comparison, not a substitute renderer.
        import test_yaml_parity as parity
        parity.YamlParityTests.setUpClass()
        check = parity.YamlParityTests(methodName='runTest')
        for source in sorted((HW/'cfg').glob('*.yaml')):
            with self.subTest(file=source.name):
                check.compare(source, 'encoder' if source.name == 'biss-c.yaml' else 'axis')


if __name__ == '__main__':
    unittest.main()
