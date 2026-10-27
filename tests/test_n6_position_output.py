"""Hardware-free checks for the dedicated 100-full-step position output."""
from pathlib import Path
import unittest
from unittest.mock import patch

import yaml

import test_ex72xx_opt as harness
from test_n6_pulse_generator import capture, sdo_writes

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / 'hardware/Nanotec'
EXAMPLE = ROOT / 'examples/PSI/lab_setup/N6'


def hardware_commands(filename):
    startup = harness.Startup.__new__(harness.Startup)
    startup.env = dict(SCRIPTEXEC='iocshLoad', ecmccfg_DIR='', ECMC_EC_SLAVE_NUM='3')
    startup.commands, startup.templates, startup.substitutions = [], [], []
    read_text = Path.read_text

    def source(path, *args, **kwargs):
        # The shared harness stubs identity verification. File existence and
        # the unchanged shared watchdog are outside the scope of this check.
        return '\n'.join(line for line in read_text(path, *args, **kwargs).splitlines()
                         if not line.lstrip().startswith('ecmcFileExist(')
                         and 'ecmcWatchDog.cmd' not in line)

    with patch.object(harness, 'HW', HW), patch.object(Path, 'read_text', source):
        startup.run(HW / filename, {})
    return startup


class N6PositionOutputTests(unittest.TestCase):
    def test_new_descriptor_extends_standard_mapping_with_raw_feedback(self):
        baseline = hardware_commands('ecmcN6-1-1-1-S.cmd').entries()
        dedicated = hardware_commands('ecmcN6-1-1-1-S_POS_OUT.cmd')
        entries = dedicated.entries()
        self.assertEqual(set(entries) - set(baseline), {'positionActualRaw01'})
        for name, mapping in baseline.items():
            self.assertEqual(entries[name], mapping)
        self.assertEqual(entries['positionActualRaw01'], ((2, 3, 0x1a03, 0x6063, 0), 'S32'))
        self.assertEqual({mapping[0][2] for mapping in entries.values() if mapping[0][0] == 2},
                         {0x1a00, 0x1a01, 0x1a02, 0x1a03})
        size = sum(int(typ[1:]) // 8 for fields, typ in entries.values()
                   if fields[:3] == (2, 3, 0x1a03))
        self.assertEqual(size, 20)
        self.assertEqual(dedicated.env['ECMC_SUBST_TYPE'], 'N6-1-1-1-S')
        self.assertEqual(dedicated.env['ECMC_EC_COMP_TYPE'], 'N6')

    def test_scaled_position_targets_100_full_steps_without_rejected_source(self):
        commands = capture(filename='position_output_100_steps.cmd')
        writes = sdo_writes(commands)
        settings = {(index, sub): (value, size) for _, index, sub, value, size in writes}
        self.assertEqual(set(settings), {(0x60e6, 1), (0x60a8, 0), (0x3252, 2)})
        unit, size = settings[0x60a8, 0]
        self.assertEqual(size, 4)
        self.assertEqual((unit >> 16) & 0xff, 0xac)
        full_steps_per_count = 10 ** (unit >> 24)
        self.assertEqual(full_steps_per_count, 100)
        self.assertEqual(full_steps_per_count * 16384, 1638400)
        self.assertEqual(settings[0x3252, 2], (0x0910, 2))
        self.assertEqual(settings[0x60e6, 1], (0, 4))
        # Regression: nominal nonzero resolution enabled the uncommissioned
        # sensorless observer and caused 0x7305 on the test drive.
        self.assertTrue(all(value == 0 for _, index, sub, value, _ in writes
                            if (index, sub) == (0x60e6, 1)))
        for _, _, _, value, size in writes:
            self.assertGreaterEqual(value, 0)
            self.assertLess(value, 1 << (8 * size))

    def test_output_gate_and_slave_parameter(self):
        filename = 'position_output_100_steps.cmd'
        commands = capture(filename=filename)
        self.assertEqual(commands[0], 'Cfg.WriteEcEntryIDString(3,binaryOutputArray01,0)')
        self.assertEqual(commands[-1], 'Cfg.WriteEcEntryIDString(3,binaryOutputArray01,65536)')
        self.assertEqual(65536, 1 << 16)
        self.assertEqual(capture({'N6_SID': '7'}, filename=filename),
                         [command.replace('(3,', '(7,') for command in commands])

    def test_raw_feedback_axis_is_withdrawn_from_active_trial(self):
        axis = yaml.safe_load((EXAMPLE / 'cfg/axis_position_output.yaml').read_text())
        self.assertEqual(axis['encoder']['position'], 'ec0.s$(ENC_SID).positionActualRaw01')
        for part in ['drive', 'encoder']:
            self.assertEqual((axis[part]['numerator'], axis[part]['denominator']), (360, 3276800))
        self.assertEqual(axis['encoder']['bits'], 32)
        self.assertEqual(axis['trajectory']['axis']['velocity'], 18)
        self.assertTrue(axis['monitoring']['lag']['enable'])
        self.assertIn('WITHDRAWN', (EXAMPLE / 'cfg/axis_position_output.yaml').read_text())

    def test_dedicated_startup_orders_overrides_after_component(self):
        startup = (EXAMPLE / 'startup_position_output_100_steps.cmd').read_text()
        self.assertIn('HW_DESC=N6-1-1-1-S,', startup)
        self.assertIn("MACROS='PINI=0'", startup)
        self.assertIn('N6_POS_UNIT=0x02AC0000', startup)
        self.assertIn('STEPS=200,INV_DIR=0', startup)
        self.assertLess(startup.index('applyComponent.cmd'), startup.index('./cfg/position_output_100_steps.cmd'))
        active = '\n'.join(line for line in startup.splitlines() if not line.lstrip().startswith('#'))
        self.assertNotIn('loadYamlAxis.cmd', active)
        self.assertNotIn('axis_position_output.yaml', active)
        self.assertIn('driveControl01,0)', active)
        self.assertIn('velocitySetpoint01,0)', active)
        self.assertNotIn('cfg/pulse_per_fullstep.cmd', startup)


if __name__ == '__main__':
    unittest.main()
