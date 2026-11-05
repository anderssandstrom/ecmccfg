"""Temporary native settings for the SIM-only filter/controller/monitor cases."""
import math
import time
from .base import SlitCase


def number(value):
    text = format(value, '.8g')
    return (
        '.' + text[2:] if text.startswith('0.') else
        '-.' + text[3:] if text.startswith('-0.') else text)


class SettingsCase(SlitCase):
    axis = 'TR_HI'

    def setUp(self):
        super().setUp()
        self.number = self.rig.profile['axes'][self.axis]
        self.saved, self.allowed = {}, {}
        self.previous_encoder = None
        self.state_machine = None
        self.restored = False
        transport = self.rig.open_text_commands()
        self.addCleanup(self.rig.close_text_commands, transport)
        self.addCleanup(self.restore)
        # Enter physical ownership before disabling the master/slave state
        # machine; disabling it while virtual ownership is active preserves
        # external trajectory sources on the blades.
        self.rig.move(self.axis, .03)
        self.rig.move(self.axis, 0)
        self.assertEqual(self.rig.stop_all(), [])
        self.state_machine = self.rig.client.get(self.rig.prefix + 'SM00-EnaCmd')
        self.rig.client.put(self.rig.prefix + 'SM00-EnaCmd', 0)
        self.rig.wait(lambda: self.rig.client.get(self.rig.prefix + 'SM00-EnaCmd') == 0
                      and self.rig.get(self.axis, '-TrjSrcTyp-RB') == 0,
                      'independent physical axis before temporary settings', 5)
        self.config('AutoDisableAfterTime', 60)

    def query(self, key):
        return self.rig.text_command(f'GetAxis{key}({self.number})', query=True)

    def config(self, key, value):
        if key not in self.saved:
            self.saved[key] = self.query(key)
        self.rig.text_command(f'Cfg.SetAxis{key}({self.number},{number(value)})')
        actual = self.query(key)
        self.assertAlmostEqual(actual, value, delta=max(1e-7, abs(value)*1e-6),
                               msg=key + ' native readback does not match the request')

    def encoder(self, index=2):
        if self.previous_encoder is None:
            self.previous_encoder = self.query('EncConfigIndex')
        self.rig.text_command(f'Cfg.SelectAxisEncConfig({self.number},{index})')

    def healthy(self):
        self.rig.plant.check()
        for axis in self.rig.profile['axes']:
            code = int(self.rig.get(axis, '-ErrId'))
            if code not in {0, *self.allowed.get(axis, ())}:
                raise AssertionError(f'{axis}: unexpected error {code:#x}')
        for axis in self.rig.profile['physical']:
            if abs(self.rig.plant.physical_position(axis)) >= .8:
                raise AssertionError(axis + ': tuning experiment exceeded SIM travel bound')
        return True

    def closed(self):
        if self.loop != 'closed':
            self.skipTest('behavior requires primary EL5042 feedback and ECMC position control')

    def enable(self):
        self.rig.put(self.axis, '-EnaCmd', 1)
        self.rig.wait(lambda: self.healthy() and self.rig.get(self.axis, '-EnaAct') == 1,
                      'axis enabled for controller observation', 6)

    def controller(self, kp=0, ki=0, kd=0, kff=0):
        for key, value in [('CntrlKp', kp), ('CntrlKi', ki), ('CntrlKd', kd), ('CntrlKff', kff),
                           ('CntrlInnerTol', 0), ('CntrlDeadband', 0),
                           ('CntrlResetIAtRmp', 0), ('CntrlFreezeIAtRmp', 0)]:
            self.config(key, value)

    def observe(self, readers, seconds=1, minimum=5):
        samples = []
        deadline = time.monotonic() + seconds
        def sample():
            self.healthy()
            row = {key: float(read()) for key, read in readers.items()}
            if not all(math.isfinite(v) for v in row.values()):
                raise AssertionError('nonfinite tuning observation')
            samples.append(row)
            return time.monotonic() >= deadline
        self.rig.wait(sample, 'bounded tuning observation', seconds + 3)
        self.assertGreaterEqual(len(samples), minimum, 'insufficient CA samples for this observation')
        return samples

    def restore(self):
        if self.restored:
            return
        self.rig.plant.clear_faults()
        errors = self.rig.stop_all()
        # Disabled feedback also clears the integrator before gains are restored.
        self.rig.wait(lambda: self.rig.get(self.axis, '-EnaAct') == 0,
                      'disabled axis before restoring tuning parameters', 5)
        # Position-filter resize may implicitly enable it. Restore size first,
        # then enable flags, independent of the order in which tests saved them.
        flags = [key for key in self.saved if key.endswith('FilterEnable')]
        for key in [key for key in reversed(self.saved) if key not in flags] + flags:
            self.rig.text_command(f'Cfg.SetAxis{key}({self.number},{number(self.saved[key])})')
        if self.previous_encoder is not None:
            self.rig.text_command(f'Cfg.SelectAxisEncConfig({self.number},{int(self.previous_encoder)})')
        for axis in self.rig.names:
            self.rig.put(axis, '-RstCmd', 1)
        self.rig.wait(lambda: all(self.rig.get(axis, '-ErrId') == 0 for axis in self.rig.names),
                      'errors cleared after settings restoration', 5)
        if self.state_machine is not None:
            self.rig.client.put(self.rig.prefix + 'SM00-EnaCmd', self.state_machine)
        self.restored = True
        self.assertFalse(errors, 'STOP before settings restoration: ' + str(errors))

    def tearDown(self):
        try:
            self.restore()
        finally:
            super().tearDown()
