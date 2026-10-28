"""Regression checks for N6 mappings and configuration-generation fixtures."""
import unittest
import yaml
from jinja2 import Environment, FileSystemLoader

from n6_support import ROOT, FIXTURES, hardware_commands


class N6PositionOutputTests(unittest.TestCase):
    def test_opt_keeps_commissioned_raw_mapping(self):
        baseline = hardware_commands('N6-1-1-1-S').entries()
        dedicated = hardware_commands(options={'RAW_POS': '1'})
        entries = dedicated.entries()
        self.assertEqual(set(entries) - set(baseline), {'positionActualScaled01'})
        for name, mapping in baseline.items():
            if name != 'positionActual01':
                self.assertEqual(entries[name], mapping)
        self.assertEqual(entries['positionActualScaled01'], baseline['positionActual01'])
        self.assertEqual(entries['positionActual01'], ((2, 3, 0x1a03, 0x6063, 0), 'S32'))
        self.assertEqual({mapping[0][2] for mapping in entries.values() if mapping[0][0] == 2},
                         {0x1a00, 0x1a01, 0x1a02, 0x1a03})
        self.assertEqual(dedicated.env['ECMC_EC_COMP_TYPE'], 'N6')

    def test_axis_uses_fine_open_loop_counter_at_native_scale(self):
        axis = yaml.safe_load((FIXTURES / 'cfg/axis_position_output.yaml').read_text())
        self.assertEqual(axis['encoder']['position'], 'ec0.s$(ENC_SID).positionActual01')
        # The same native counter can be expressed in degrees or full steps.
        # Check the physical scale against the selected units, not a fixed unit.
        units_per_revolution = {'steps': 200, 'deg': 360}
        unit = axis['epics']['unit']
        self.assertIn(unit, units_per_revolution)
        self.assertEqual(axis['encoder']['unit'], unit)
        for part in ['drive', 'encoder']:
            self.assertEqual((axis[part]['numerator'], axis[part]['denominator']),
                             (units_per_revolution[unit], 3276800))
        self.assertEqual(axis['encoder']['bits'], 32)
        self.assertTrue(axis['monitoring']['lag']['enable'])

    def test_axis_renders_sequence_26_and_mode_handshake(self):
        config = yaml.safe_load((FIXTURES / 'cfg/axis_position_output.yaml').read_text())
        env = Environment(loader=FileSystemLoader(ROOT / 'scripts/jinja2/templates'))
        axis = env.get_template('axis.jinja2').render(**config)
        encoder = env.get_template('encoder.jinja2').render(**config)
        for text in ['ec0.s$(DRV_SID).modeControl01', 'ec0.s$(DRV_SID).modeActual01',
                     'Cfg.SetAxisAutoModeCmdHoming(${ECMC_AXIS_NO},6)',
                     'Cfg.SetAxisAutoModeCmdMotion(${ECMC_AXIS_NO},9)']:
            self.assertIn(text, axis)
        for text in ['ec0.s$(DRV_SID).driveCmdExe01.0',
                     'ec0.s$(DRV_SID).driveStatus01.12',
                     'Cfg.SetAxisHomeSeqId(${ECMC_AXIS_NO},26)',
                     'Cfg.SetAxisSeqTimeout(${ECMC_AXIS_NO},10)']:
            self.assertIn(text, encoder)
        home = config['encoder']['homing']
        self.assertTrue(home['postMoveEnable'])
        self.assertEqual(home['postMovePosition'], home['position'])
        self.assertEqual(home['position'], 0)
        self.assertEqual(home['refAtHome'], 1)
        for direction in ['to', 'from']:
            self.assertGreater(home['velocity'][direction], 0)

    def test_startup_fixture_uses_packaged_components_in_required_order(self):
        startup = (FIXTURES / 'startup_position_output_100_steps.cmd').read_text()
        active = '\n'.join(line for line in startup.splitlines() if not line.lstrip().startswith('#'))
        self.assertIn("HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1,HOMING=1'", active)
        self.assertIn('FULL_STEPS=100,OUTPUT=1,ARM=1', active)
        self.assertLess(active.index('COMP=Motor-'), active.index('COMP=Drive-Generic-PositionOutput'))
        self.assertLess(active.index('COMP=Drive-Generic-PositionOutput'), active.index('loadYamlAxis.cmd'))
        self.assertIn('FILE=./cfg/axis_position_output.yaml', active)
        self.assertNotIn('cfg/position_output_100_steps.cmd', active)
        self.assertNotIn('N6_POS_UNIT=', active)


if __name__ == '__main__':
    unittest.main()
