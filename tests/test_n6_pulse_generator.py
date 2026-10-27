"""Hardware-free checks for the experimental N6 pulse-generator setup."""
from pathlib import Path
import re
import unittest

from test_ex72xx_opt import Startup

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'examples/PSI/lab_setup/N6'


def capture(scope=None, filename='pulse_per_fullstep.cmd'):
    startup = Startup.__new__(Startup)
    startup.env = {'ECMC_EC_SLAVE_NUM': '3'}
    startup.commands = []
    startup.run(EXAMPLE / 'cfg' / filename, scope or {})
    return startup.commands


def sdo_writes(commands):
    result = []
    for command in commands:
        match = re.fullmatch(r'Cfg.EcAddSdo\((.*)\)', command)
        if match:
            result.append(tuple(int(value, 0) for value in match[1].split(',')))
    return result


class N6PulseGeneratorTests(unittest.TestCase):
    def test_ratio_fits_s16_and_targets_one_full_step(self):
        writes = sdo_writes(capture())
        settings = {(index, subindex): (value, size)
                    for _, index, subindex, value, size in writes}
        numerator, denominator = (settings[0x205c, sub][0] for sub in [3, 4])
        # Native open-loop resolution from 50 pole pairs and 200 full steps.
        # This checks the intended ratio, not the unverified firmware source.
        self.assertEqual(50 * 65536 * numerator / denominator, 200)
        for _, index, _, value, size in writes:
            if index == 0x205c:
                self.assertEqual(size, 2)
                self.assertGreaterEqual(value, 0)
                self.assertLessEqual(value, 32767)
        self.assertEqual(settings[0x205c, 1], (0, 2))  # no free-running pulses
        self.assertEqual(settings[0x205c, 2], (1, 2))  # clock/direction

    def test_preserves_units_and_position_velocity_selection(self):
        writes = sdo_writes(capture())
        self.assertEqual({index for _, index, _, _, _ in writes},
                         {0x205c, 0x3203, 0x3252, 0x60e6, 0x60eb})
        feedback = [(sub, value, size) for _, index, sub, value, size in writes
                    if index == 0x3203]
        self.assertEqual({sub for sub, _, _ in feedback}, {1, 2, 3, 4})
        self.assertEqual([sub for sub, value, _ in feedback if value & 8], [1])
        self.assertTrue(all(value & 7 == 0 and size == 1 for _, value, size in feedback))
        self.assertFalse(any('EcAddEntry' in command for command in capture()))

    def test_disabled_interface_is_configured_before_source_selection(self):
        writes = sdo_writes(capture())
        revolutions = writes.index((3, 0x60eb, 1, 1, 4))
        increments = writes.index((3, 0x60e6, 1, 3276800, 4))
        select = writes.index((3, 0x3203, 1, 8, 1))
        self.assertLess(revolutions, increments)
        self.assertLess(increments, select)
        self.assertEqual([entry for entry in writes if entry[1:3] == (0x3203, 1)],
                         [(3, 0x3203, 1, 8, 1)])
        settings = {(index, sub): value for _, index, sub, value, _ in writes}
        self.assertEqual(settings[0x60e6, 1] / settings[0x60eb, 1], 200 * 16384)

    def test_recovery_clears_source_before_disabling_interface(self):
        commands = capture(filename='disable_pulse_source.cmd')
        writes = sdo_writes(commands)
        self.assertEqual(commands[0], 'Cfg.WriteEcEntryIDString(3,binaryOutputArray01,0)')
        self.assertLess(writes.index((3, 0x3203, 1, 0, 1)),
                        writes.index((3, 0x60e6, 1, 0, 4)))
        settings = {(index, sub): value for _, index, sub, value, _ in writes}
        self.assertEqual(settings[0x205c, 1], 0)
        self.assertEqual(settings[0x205c, 3], 0)
        self.assertEqual(settings[0x3252, 2], 0x0010)
        self.assertEqual(settings[0x3252, 3], 0x0011)
        self.assertFalse(any('binaryOutputArray01,196608)' in c for c in commands))

    def test_routing_gate_and_setup_order(self):
        commands = capture()
        writes = sdo_writes(commands)
        self.assertEqual(commands[0], 'Cfg.WriteEcEntryIDString(3,binaryOutputArray01,0)')
        self.assertEqual(commands[-1],
                         'Cfg.WriteEcEntryIDString(3,binaryOutputArray01,196608)')
        self.assertEqual(196608, (1 << 16) | (1 << 17))
        routing = [(sub, value, size) for _, index, sub, value, size in writes
                   if index == 0x3252]
        self.assertEqual(routing, [(2, 0x2010, 2), (3, 0x2011, 2)])
        self.assertEqual(writes[0], (3, 0x205c, 3, 0, 2))
        self.assertEqual(writes[-1], (3, 0x205c, 3, 1, 2))
        self.assertEqual(capture({'N6_SID': '7'}),
                         [command.replace('(3,', '(7,') for command in commands])

    def test_startup_uses_original_feedback_and_loads_after_component(self):
        source = (EXAMPLE / 'startup_pulse_per_fullstep.cmd').read_text()
        self.assertIn('HW_DESC=N6-1-1-1-S,', source)
        self.assertIn("MACROS='PINI=0'", source)
        self.assertIn('STEPS=200,INV_DIR=0', source)
        self.assertLess(source.index('applyComponent.cmd'), source.index('./cfg/pulse_per_fullstep.cmd'))
        self.assertLess(source.index('./cfg/pulse_per_fullstep.cmd'), source.index('loadYamlAxis.cmd'))
        yaml = (EXAMPLE / 'cfg/axis.yaml').read_text()
        self.assertIn('position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}', yaml)
        from n6_support import hardware_commands
        mapping = hardware_commands('N6-1-1-1-S').entries()['positionActual01']
        self.assertEqual(mapping, ((2, 3, 0x1a01, 0x6064, 0), 'S32'))


if __name__ == '__main__':
    unittest.main()
