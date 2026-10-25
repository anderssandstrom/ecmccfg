"""Verify shared IOC-shell environment cannot leak options across slave loads."""
import itertools
import unittest

from test_ex72xx_opt import HW, MODELS, Startup


class StartupSequenceTests(unittest.TestCase):
    def test_previous_slave_does_not_change_next_slave(self):
        # Exercise both directions, including EL7411-specific defaults and SDO
        # options followed by Ex72xx, and two-channel ELM followed by one channel.
        for first, second, mode in itertools.product(MODELS + ['EL7411'],
                                                     MODELS + ['EL7411'],
                                                     ['CSTCA', 'CSV']):
            with self.subTest(first=first, second=second, mode=mode):
                shared = Startup(first, dict(MODE=mode))
                shared.commands.clear()
                shared.substitutions.clear()
                shared.templates.clear()
                family = 'ELM' if second.startswith('ELM') else second[:2]
                shared.run(HW / family / f'ecmc{second}_OPT.cmd', {})
                fresh = Startup(second)
                self.assertEqual(shared.commands, fresh.commands)
                self.assertEqual(shared.substitutions, fresh.substitutions)
                self.assertEqual(shared.templates, fresh.templates)
                self.assertFalse(any(key.startswith(('ECMC_EX72XX_OPT_',
                                                     'ECMC_EL7411_OPT_'))
                                     for key in shared.env))


if __name__ == '__main__':
    unittest.main()
