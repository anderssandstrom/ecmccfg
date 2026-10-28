"""Cross-repository PWM component checks; no hardware access or example inputs."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from n6_support import hardware_commands, PWMOutput, settings
from test_ex72xx_opt import InvalidConfiguration


class N6PWMOutputTests(unittest.TestCase):
    def component(self, raw='0', motor=True, master=0, slave=3, invert='0'):
        result = PWMOutput(hardware_commands(options={'RAW_POS': raw}, master=master, slave=slave),
                           master=master, slave=slave)
        if motor:
            result.motor(invert)
        return result

    def test_defaults_match_the_working_trial_and_start_disarmed(self):
        component = self.component()
        commands = component.apply()
        self.assertEqual(settings(commands), {(0x323a, 1): (0, 1), (0x323a, 2): (0, 1),
                                              (0x3260, 1): (2000, 4), (0x3260, 2): (50, 4),
                                              (0x3252, 2): (0x1210, 2)})
        self.assertEqual(commands[0], 'Cfg.WriteEcEntryEcPath(ec0.s3.binaryOutputArray01.16,0)')
        self.assertEqual(commands[-1], commands[0])
        self.assertLess(commands.index('Cfg.EcAddSdo(3,0x3260,0x02,0,4)'),
                        commands.index('Cfg.EcAddSdo(3,0x3260,0x01,2000,4)'))
        self.assertFalse(any(key.startswith('N6_PWM_') for key in component.env))
        for key in ['FREQUENCY_HZ', 'DUTY_PERCENT', 'PWM_ID', 'ARM', 'OUTPUT',
                    'N6_IO_24V', 'N6_INPUT_PULLUP', 'COMP_S_ID']:
            self.assertNotIn(key, component.env)

    def test_integer_frequency_duty_generators_and_outputs(self):
        for hz in [50, 501, 1753, 2000]:
            for duty in [0, 1, 50, 99, 100]:
                for generator in [0, 1]:
                    for output in [1, 2, 3]:
                        with self.subTest(hz=hz, duty=duty, generator=generator, output=output):
                            component = self.component(invert='1')  # PWM does not depend on direction
                            commands = component.apply({'FREQUENCY_HZ': hz, 'DUTY_PERCENT': duty,
                                                        'PWM_ID': generator, 'OUTPUT': output, 'ARM': 1})
                            sdos = settings(commands)
                            index, bit = 0x3260 + generator, 15 + output
                            self.assertEqual(sdos[index, 1], (hz, 4))
                            self.assertEqual(sdos[index, 2], (duty, 4))
                            self.assertEqual(sdos[0x3252, output+1], (0x1200+256*generator+bit, 2))
                            self.assertEqual({i for i, _ in sdos}, {0x323a, 0x3252, index})
                            self.assertEqual(commands[-1],
                                             f'Cfg.WriteEcEntryEcPath(ec0.s3.binaryOutputArray01.{bit},1)')

    def test_invalid_options_fail_before_hardware_writes(self):
        cases = [{key: value} for key, values in [
            ('FREQUENCY_HZ', ['0', '49', '2001', '-1', '50.5', '1000.0', '1e3', 'NaN', 'x', '']),
            ('DUTY_PERCENT', ['-1', '101', '0.5', '50.0', 'NaN', 'x', '']),
            ('OUTPUT', ['0', '4', '1.0', '']), ('PWM_ID', ['2', '-1', '0.0', '']),
            ('ARM', ['2', 'true', '']), ('N6_IO_24V', ['2', '24', '']),
            ('N6_INPUT_PULLUP', ['2', 'true', '']), ('UNKNOWN', ['1'])]
                 for value in values]
        for options in cases:
            with self.subTest(options=options):
                component = self.component()
                # The capture evaluator raises for invalid numeric expressions;
                # IOC code keeps BAD on its rejecting branch if evaluation fails.
                with self.assertRaises((InvalidConfiguration, NameError, SyntaxError,
                                        TypeError, ValueError, OverflowError)):
                    component.apply(options)
                self.assertEqual(component.commands, [])

    def test_required_capabilities_and_scope(self):
        for change in ['no_motor', 'wrong_master', 'wrong_slave', 'wrong_type', 'wrong_channel']:
            component = self.component(motor=change != 'no_motor', master=1, slave=7)
            kwargs = {}
            if change == 'wrong_master': component.env['ECMC_EC_MASTER_ID'] = '0'
            if change == 'wrong_slave': component.slave = '3'
            if change == 'wrong_type': kwargs['comp_type'] = 'EL7062'
            if change == 'wrong_channel': kwargs['channel'] = '2'
            with self.assertRaises(InvalidConfiguration): component.apply(**kwargs)
            self.assertEqual(component.commands, [])
        component = PWMOutput(hardware_commands('N6-1-1-1-S'))
        component.motor()
        with self.assertRaises(InvalidConfiguration): component.apply()
        self.assertEqual(component.commands, [])
        component = self.component(master=1, slave=7)
        self.assertEqual(component.apply()[-1],
                         'Cfg.WriteEcEntryEcPath(ec1.s7.binaryOutputArray01.16,0)')

    def test_shared_generator_settings_cannot_silently_change(self):
        component = self.component()
        component.apply({'FREQUENCY_HZ': 1000})
        component.apply({'FREQUENCY_HZ': 1000, 'OUTPUT': 2})
        for options in [{'OUTPUT': 3}, {'FREQUENCY_HZ': 1000, 'DUTY_PERCENT': 25, 'OUTPUT': 3}]:
            with self.assertRaises(InvalidConfiguration): component.apply(options)
            self.assertEqual(component.commands, [])
        component.apply({'FREQUENCY_HZ': 1500, 'DUTY_PERCENT': 25, 'PWM_ID': 1, 'OUTPUT': 3})
        with self.assertRaises(InvalidConfiguration): component.motor()
        self.assertEqual(component.commands, [])

    def test_position_and_pwm_share_io_but_not_the_same_output(self):
        for pwm_first in [False, True]:
            component = self.component(raw='1')
            position = lambda options: component.apply_output('PositionOutput', 'POSITION_OUTPUT', options)
            if pwm_first:
                component.apply({'OUTPUT': 1, 'N6_IO_24V': 1, 'N6_INPUT_PULLUP': 1})
                with self.assertRaises(InvalidConfiguration): position({'OUTPUT': 1})
                for options in [{'OUTPUT': 2, 'N6_IO_24V': 0}, {'OUTPUT': 2, 'N6_INPUT_PULLUP': 0}]:
                    with self.assertRaises(InvalidConfiguration): position(options)
                    self.assertEqual(component.commands, [])
                self.assertEqual(settings(position({'OUTPUT': 2}))[0x323a, 1], (1, 1))
            else:
                position({'OUTPUT': 1, 'N6_IO_24V': 1, 'N6_INPUT_PULLUP': 1})
                with self.assertRaises(InvalidConfiguration): component.apply({'OUTPUT': 1})
                for options in [{'OUTPUT': 2, 'N6_IO_24V': 0}, {'OUTPUT': 2, 'N6_INPUT_PULLUP': 0}]:
                    with self.assertRaises(InvalidConfiguration): component.apply(options)
                    self.assertEqual(component.commands, [])
                self.assertEqual(settings(component.apply({'OUTPUT': 2}))[0x323a, 2], (1, 1))

    def test_gate_writes_preserve_other_outputs_and_brake(self):
        initial = 0xa5aff00f
        for output in [1, 2, 3]:
            for arm in [0, 1]:
                component = self.component()
                word = initial
                for command in component.apply({'OUTPUT': output, 'ARM': arm}):
                    if command.startswith('Cfg.WriteEcEntryEcPath('):
                        path, value = command.split('(', 1)[1].rstrip(')').split(',')
                        bit = int(path.rsplit('.', 1)[1])
                        word = (word & ~(1 << bit)) | (int(value) << bit)
                mask = 1 << (15+output)
                self.assertEqual(word & ~mask, initial & ~mask)
                self.assertEqual(bool(word & mask), bool(arm))


if __name__ == '__main__':
    unittest.main(verbosity=2)
