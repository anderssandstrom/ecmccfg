"""Controller gain selection, clamping, ramp flags and settling behavior."""
from .settings import SettingsCase


class ControllerTests(SettingsCase):
    def test_controller_parameter_readback(self):
        values = {'CntrlKp': 1.5, 'CntrlKi': .002, 'CntrlKd': .01, 'CntrlKff': .8,
                  'CntrlInnerKp': .5, 'CntrlInnerKi': .001, 'CntrlInnerKd': .005,
                  'CntrlInnerTol': .006, 'CntrlDeadband': .002, 'CntrlDeadbandTime': 200,
                  'CntrlOutLL': -.2, 'CntrlOutHL': .2,
                  'CntrlIPartLL': -.03, 'CntrlIPartHL': .03,
                  'CntrlResetIAtRmp': 1, 'CntrlFreezeIAtRmp': 1}
        for key, value in values.items():
            with self.subTest(setting=key): self.config(key, value)

    def error(self): return self.query('CntrlError')
    def output(self): return self.query('CntrlOutput')
    def integral(self): return self.query('CntrlOutIpart')

    def test_inner_and_outer_proportional_gains(self):
        self.closed()
        self.controller(kp=.5)
        for key, value in [('CntrlInnerKp', .1), ('CntrlInnerKi', 0),
                           ('CntrlInnerKd', 0), ('CntrlInnerTol', .008)]:
            self.config(key, value)
        self.enable()
        # Low gains leave time to observe each band through CA without
        # approaching the normal 0.02 mm following-error threshold.
        for bias, gain, low, high in ((.014, .5, .009, .017), (.004, .1, .002, .007)):
            self.rig.plant.inject(self.axis, encoder_bias_mm=bias)
            def correct_gain():
                self.healthy()
                error = self.error()
                part = self.query('CntrlOutPpart')
                return low < abs(error) < high and abs(part-error*gain) < .0007
            self.rig.wait(correct_gain, 'nonzero P contribution uses the expected gain band', 2)

    def test_output_limits_bound_both_polarities(self):
        self.closed()
        self.controller(kp=10)
        self.config('CntrlOutLL', -.02)
        self.config('CntrlOutHL', .02)
        self.enable()
        for bias, sign in ((.015, -1), (-.015, 1)):
            self.rig.plant.inject(self.axis, encoder_bias_mm=bias)
            self.rig.wait(lambda: self.healthy() and sign*self.query('CntrlOutPpart') > .04
                          and abs(self.output()-sign*.02) < .002,
                          'unclamped P exceeds the limit while controller output saturates', 2)
        self.config('CntrlOutLL', 0)
        self.config('CntrlOutHL', 0)
        self.rig.wait(lambda: self.healthy() and abs(self.output()) > .03,
                      'zero/zero limits disable output clamping', 2)

    def test_integral_limits_and_release(self):
        self.closed()
        self.controller(ki=.01)
        for key, value in [('CntrlIPartLL', -.01), ('CntrlIPartHL', .01),
                           ('CntrlOutLL', -.003), ('CntrlOutHL', .003)]:
            self.config(key, value)
        self.enable()
        for bias, sign in ((.015, -1), (-.015, 1)):
            self.rig.plant.inject(self.axis, encoder_bias_mm=bias)
            self.rig.wait(lambda: self.healthy() and abs(self.integral()-sign*.01) < .001,
                          'integral reaches the signed clamp', 3)
            self.rig.assert_stays(lambda: self.healthy() and abs(self.integral()) <= .0101,
                                  'integral remains bounded under sustained error', .2)
        self.config('CntrlIPartLL', 0)
        self.config('CntrlIPartHL', 0)
        self.rig.wait(lambda: self.healthy() and self.integral() > .015,
                      'unlimited integrator grows beyond its former clamp', 2)

    def test_integral_freeze_release_and_reset_during_motion(self):
        self.closed()
        self.controller(ki=.005)
        for key, value in [('CntrlIPartLL', -.1), ('CntrlIPartHL', .1),
                           ('CntrlOutLL', -.003), ('CntrlOutHL', .003),
                           ('MonPosLagTol', .6)]:
            self.config(key, value)
        self.enable()
        self.rig.plant.inject(self.axis, encoder_bias_mm=.012)
        self.rig.wait(lambda: self.healthy() and -.04 < self.integral() < -.01,
                      'nonzero unsaturated integral before freeze', 3)
        # Keep the preloaded value stable during CA command staging, before
        # the native busy flag can engage the freeze setting.
        self.config('CntrlKi', 0)
        self.config('CntrlFreezeIAtRmp', 1)
        self.rig.stage_native(self.axis, 3, .3, .1)
        self.rig.execute_native(self.axis)
        frozen = self.integral()
        self.assertGreater(abs(frozen), .005)
        self.assertLess(abs(frozen), .08, 'freeze needs an unsaturated I contribution')
        self.config('CntrlKi', .005)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-Busy') == 1
                              and abs(self.integral()-frozen) < .001,
                              'busy trajectory preserves nonzero I contribution', .3)
        self.config('CntrlFreezeIAtRmp', 0)
        self.rig.wait(lambda: self.healthy() and abs(self.integral()-frozen) > .005,
                      'releasing freeze resumes integration', 2)
        self.config('CntrlFreezeIAtRmp', 1)
        self.config('CntrlResetIAtRmp', 1)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-Busy') == 1
                              and abs(self.integral()) < .0001,
                              'reset takes precedence over freeze while busy', .2)

    def test_deadband_dwell_and_reactivation(self):
        self.closed()
        self.controller(kp=.5)
        self.config('CntrlDeadband', .006)
        self.config('CntrlDeadbandTime', 600)
        self.enable()
        self.rig.plant.inject(self.axis, encoder_bias_mm=.012)
        self.rig.wait(lambda: self.healthy() and abs(self.output()) > .003,
                      'outside deadband produces a correction', 2)
        self.rig.plant.inject(self.axis, encoder_bias_mm=.004)
        self.rig.wait(lambda: self.healthy() and .001 < abs(self.error()) < .006
                      and abs(self.output()) > .0003,
                      'inside band still corrects before dwell expires', 1)
        self.rig.wait(lambda: self.healthy() and abs(self.error()) > .001
                      and abs(self.output()) < 1e-6 and self.rig.get(self.axis, '-EnaAct') == 1,
                      'deadband suppresses correction after dwell with residual error', 3)
        self.config('CntrlDeadband', .0005)
        self.rig.wait(lambda: self.healthy() and abs(self.output()) > .0003,
                      'tightening deadband restores position correction', 2)

    def test_velocity_feedforward_can_be_disabled_and_restored(self):
        self.closed()
        self.controller(kff=1)
        self.config('MonPosLagTol', .6)
        self.rig.stage_native(self.axis, 3, .4, .1)
        self.rig.execute_native(self.axis)
        self.rig.wait(lambda: self.healthy() and self.query('CntrlOutFFpart') > .07,
                      'running trajectory generates velocity feedforward', 3)
        self.config('CntrlKff', 0)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-Busy') == 1
                              and abs(self.output()) < 1e-6,
                              'zero feedforward gain suppresses output with PID zero', .2)
        self.config('CntrlKff', 1)
        self.rig.wait(lambda: self.healthy() and self.query('CntrlOutFFpart') > .07,
                      'restored feedforward resumes output on the same trajectory', 2)
