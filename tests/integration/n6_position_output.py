"""Cross-repository checks. Run with current sibling ecmccomp sources present."""
from pathlib import Path
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from n6_support import hardware_commands, PositionOutput, settings
from test_ex72xx_opt import InvalidConfiguration


class N6PositionOutputIntegrationTests(unittest.TestCase):
    def component(self, raw='1', slave=3, master=0, invert='0', motor=True):
        hardware = hardware_commands(options={'RAW_POS': raw}, slave=slave, master=master)
        component = PositionOutput(hardware, slave=slave, master=master)
        if motor:
            component.motor(invert)
        return component

    def test_commissioned_settings_and_arm_are_preserved(self):
        component = self.component()
        commands = component.apply({'FULL_STEPS': 100, 'OUTPUT': 1, 'ARM': 1})
        self.assertEqual(settings(commands), {(0x323a, 1): (0, 1),
                                              (0x323a, 2): (0, 1),
                                              (0x60e6, 1): (0, 4),
                                              (0x60a8, 0): (0x02ac0000, 4),
                                              (0x3252, 2): (0x0910, 2)})
        self.assertEqual(commands[0], 'Cfg.WriteEcEntryEcPath(ec0.s3.binaryOutputArray01.16,0)')
        self.assertEqual(commands[-1], 'Cfg.WriteEcEntryEcPath(ec0.s3.binaryOutputArray01.16,1)')

    def test_every_supported_interval_and_output(self):
        for exponent in range(7):
            for divider in [1, 2, 4, 8, 16, 32, 64]:
                for output in [1, 2, 3]:
                    interval = 10**exponent * divider
                    with self.subTest(interval=interval, output=output):
                        component = self.component()
                        commands = component.apply({'FULL_STEPS': interval, 'OUTPUT': output})
                        sdos = settings(commands)
                        unit, size = sdos[0x60a8, 0]
                        self.assertEqual(size, 4)
                        self.assertEqual((unit >> 16) & 0xff, 0xac)
                        route, size = sdos[0x3252, output + 1]
                        self.assertEqual(size, 2)
                        self.assertEqual(route & 0x1f, 15 + output)
                        actual_interval = 10**(unit >> 24) * 2**((route >> 8) - 9)
                        self.assertEqual(actual_interval, interval)
                        self.assertEqual(route >> 8, 9 + int(math.log2(divider)))
                        self.assertEqual(sdos[0x60e6, 1], (0, 4))
                        self.assertEqual(set(index for index, _ in sdos), {0x60a8, 0x60e6, 0x3252, 0x323a})
                        self.assertEqual(commands[-1],
                                         f'Cfg.WriteEcEntryEcPath(ec0.s3.binaryOutputArray01.{15+output},0)')
                        self.assertFalse(any(key.startswith('N6_PO_') for key in component.env))
                        self.assertFalse(any(key in component.env for key in ['COMP_S_ID', 'FULL_STEPS', 'OUTPUT', 'ARM', 'N6_IO_24V', 'N6_INPUT_PULLUP']))

    def test_invalid_choices_do_not_change_slave_state(self):
        cases = [{'FULL_STEPS': value} for value in ['0', '-1', '3', '50', '125', '100.0', 'NaN', '10000000', '']]
        cases += [{'OUTPUT': value} for value in ['0', '4', '-1', '1.0', 'x']]
        cases += [{'ARM': value} for value in ['2', 'true', '']]
        cases += [{key: value} for key in ['N6_IO_24V', 'N6_INPUT_PULLUP']
                  for value in ['2', '-1', 'true', '']]
        cases += [{'UNKNOWN': '1'}]
        for options in cases:
            with self.subTest(options=options):
                component = self.component()
                with self.assertRaises(InvalidConfiguration):
                    component.apply(options)
                self.assertEqual(component.commands, [])

    def test_voltage_defaults_apply_to_io_only(self):
        component = self.component(motor=False)
        motor = settings(component.motor())
        self.assertEqual(motor[0x323a, 1], (1, 1))  # existing motor I/O default
        output = settings(component.apply())
        self.assertEqual(output[0x323a, 1], (0, 1))  # new output default: 5 V
        self.assertEqual(output[0x323a, 2], (0, 1))
        self.assertEqual(set(index for index, _ in output), {0x323a, 0x60e6, 0x60a8, 0x3252})

    def test_shared_electrical_options_and_inheritance(self):
        component = self.component(motor=False)
        component.motor(options={'N6_INPUT_PULLUP': 1})
        first = settings(component.apply({'N6_IO_24V': 1}))
        self.assertEqual(first[0x323a, 1], (1, 1))
        self.assertEqual(first[0x323a, 2], (1, 1))
        second = settings(component.apply({'OUTPUT': 2}))
        self.assertEqual(second[0x323a, 1], (1, 1))
        self.assertEqual(second[0x323a, 2], (1, 1))
        for option in [{'N6_IO_24V': 0}, {'N6_INPUT_PULLUP': 0}]:
            with self.assertRaises(InvalidConfiguration):
                component.apply(option)
            self.assertEqual(component.commands, [])
        other = self.component(master=1, slave=7)
        self.assertEqual(settings(other.apply())[0x323a, 1], (0, 1))

    def test_invalid_motor_io_is_rejected_before_writes(self):
        for options in [{'N6_IO_24V': 2}, {'N6_INPUT_PULLUP': -1}]:
            component = self.component(motor=False)
            with self.assertRaises(InvalidConfiguration):
                component.motor(options=options)
            self.assertEqual(component.commands, [])

    def test_raw_mapping_and_motor_are_required(self):
        for raw, motor, invert in [('0', True, '0'), ('1', False, '0'), ('1', True, '1')]:
            with self.subTest(raw=raw, motor=motor, invert=invert):
                component = self.component(raw=raw, motor=motor, invert=invert)
                with self.assertRaises(InvalidConfiguration):
                    component.apply()
                self.assertEqual(component.commands, [])

    def test_capabilities_are_scoped_to_master_and_slave(self):
        for wrong_master in [False, True]:
            component = self.component(slave=7, master=1)
            if wrong_master:
                component.env['ECMC_EC_MASTER_ID'] = '0'
            else:
                component.slave = '3'
            with self.assertRaises(InvalidConfiguration):
                component.apply()
            self.assertEqual(component.commands, [])
        component = self.component(slave=7, master=1)
        commands = component.apply({'ARM': 1})
        self.assertEqual(commands[-1], 'Cfg.WriteEcEntryEcPath(ec1.s7.binaryOutputArray01.16,1)')

    def test_gate_operation_preserves_unrelated_bits(self):
        initial_word = 0xa5aff00f
        for output in [1, 2, 3]:
            for arm in [0, 1]:
                component = self.component()
                commands = component.apply({'OUTPUT': output, 'ARM': arm})
                word = initial_word
                for command in commands:
                    if command.startswith('Cfg.WriteEcEntryEcPath('):
                        path, value = command.split('(', 1)[1].rstrip(')').split(',')
                        bit = int(path.rsplit('.', 1)[1])
                        mask = 1 << bit
                        word = (word & ~mask) | (int(value) << bit)
                mask = 1 << (15 + output)
                self.assertEqual(word & ~mask, initial_word & ~mask)
                self.assertEqual(bool(word & mask), bool(arm))

    def test_shared_unit_conflicts_and_motor_order_are_rejected(self):
        component = self.component()
        component.apply({'FULL_STEPS': 100, 'OUTPUT': 1})
        component.apply({'FULL_STEPS': 200, 'OUTPUT': 2})  # same unit, divider 2
        with self.assertRaises(InvalidConfiguration):
            component.apply({'FULL_STEPS': 10, 'OUTPUT': 3})
        self.assertEqual(component.commands, [])
        with self.assertRaises(InvalidConfiguration):
            component.motor()
        self.assertEqual(component.commands, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
