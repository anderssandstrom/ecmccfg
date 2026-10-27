"""Regression checks for the commissioned N6 example after packaging."""
import unittest
import yaml

from n6_support import EXAMPLE, hardware_commands


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
        axis = yaml.safe_load((EXAMPLE / 'cfg/axis_position_output.yaml').read_text())
        self.assertEqual(axis['encoder']['position'], 'ec0.s$(ENC_SID).positionActual01')
        for part in ['drive', 'encoder']:
            self.assertEqual((axis[part]['numerator'], axis[part]['denominator']), (360, 3276800))
        self.assertEqual(axis['encoder']['bits'], 32)
        self.assertTrue(axis['monitoring']['lag']['enable'])

    def test_example_uses_packaged_components_in_required_order(self):
        startup = (EXAMPLE / 'startup_position_output_100_steps.cmd').read_text()
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
