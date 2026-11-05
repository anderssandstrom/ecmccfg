"""Native monitor settings and bounded fault/disable/recovery experiments."""
from .settings import SettingsCase


class MonitoringTests(SettingsCase):
    def test_monitor_parameter_readback(self):
        values = {'MonMaxVel': .3, 'MonEnableMaxVel': 1,
                  'MonMaxVelTrajILDelay': 100, 'MonMaxVelDriveILDelay': 200,
                  'MonAtTargetTol': .005, 'MonAtTargetTime': 200, 'MonEnableAtTargetMon': 1,
                  'MonPosLagTol': .015, 'MonPosLagTime': 100, 'MonEnableLagMon': 1,
                  'MonVelDiffTol': .1, 'MonEnableVelocityDiff': 1,
                  'MonVelDiffTrajILDelay': 30, 'MonVelDiffDriveILDelay': 50}
        for key, value in values.items():
            with self.subTest(setting=key): self.config(key, value)

    def recover(self, code):
        self.allowed[self.axis] = (code,)
        self.rig.fault_stopped(self.axis, code)
        self.rig.plant.clear_faults()
        self.rig.put(self.axis, '-RstCmd', 1)
        self.rig.wait(lambda: self.rig.get(self.axis, '-ErrId') == 0,
                      'native monitor reset', 5)
        self.allowed.clear()
        position = self.rig.plant.physical_position(self.axis)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-Busy') == 0
                              and self.rig.get(self.axis, '-EnaAct') == 0
                              and abs(self.rig.plant.physical_position(self.axis)-position) < .005,
                              'monitor reset must not replay the interrupted move', .3)

    def test_max_velocity_trip_disable_and_fresh_command(self):
        self.config('MonMaxVel', .12)
        self.config('MonEnableMaxVel', 1)
        self.config('MonMaxVelTrajILDelay', 30)
        self.config('MonMaxVelDriveILDelay', 50)
        self.rig.native_move(self.axis, .04, velocity=.08)
        self.rig.stage_native(self.axis, 3, .5, .3)
        self.rig.execute_native(self.axis)
        self.recover(0x14c07)
        self.assertLess(self.rig.plant.physical_position(self.axis), .4)
        self.config('MonEnableMaxVel', 0)
        self.rig.native_move(self.axis, -.1, velocity=.3)
        self.healthy()
        self.config('MonEnableMaxVel', 1)
        self.config('MonMaxVel', .4)
        self.rig.native_move(self.axis, 0, velocity=.3)

    def test_position_lag_trip_and_recovery(self):
        self.closed()
        self.controller()
        self.config('MonPosLagTol', .006)
        self.config('MonPosLagTime', 100)
        self.config('MonEnableLagMon', 1)
        self.enable()
        self.rig.plant.inject(self.axis, encoder_bias_mm=.012)
        self.recover(0x14c08)
        self.controller(kp=2, kff=1)
        self.rig.native_move(self.axis, .1, velocity=.1)

    def test_velocity_difference_detects_frozen_feedback(self):
        self.closed()
        self.config('MonPosLagTol', .6)
        self.config('MonEnableVelocityDiff', 1)
        self.config('MonVelDiffTol', .08)
        # Long enough to tolerate the intentionally sampled CA plant while
        # still tripping well before the end of the bounded test move.
        self.config('MonVelDiffTrajILDelay', 100)
        self.config('MonVelDiffDriveILDelay', 50)
        self.rig.stage_native(self.axis, 3, .5, .15)
        self.rig.execute_native(self.axis)
        self.rig.wait(lambda: self.rig.get(self.axis, '-PosAct') > .03,
                      'measured motion before freezing feedback', 3)
        self.rig.plant.inject(self.axis, frozen=True)
        self.recover(0x14c14)
        self.config('MonEnableVelocityDiff', 0)
        self.rig.native_move(self.axis, 0, velocity=.1)

    def test_at_target_requires_tolerance_and_dwell(self):
        self.closed()
        self.controller()
        self.config('MonAtTargetTol', .006)
        self.config('MonAtTargetTime', 600)
        self.config('MonEnableAtTargetMon', 1)
        self.enable()
        self.rig.plant.inject(self.axis, encoder_bias_mm=.012)
        self.rig.wait(lambda: self.healthy() and self.rig.get(self.axis, '-AtTarget') == 0,
                      'outside tolerance clears at-target', 2)
        self.rig.plant.inject(self.axis, encoder_bias_mm=.003)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-AtTarget') == 0,
                              'within tolerance must complete a dwell before at-target', .2)
        self.rig.wait(lambda: self.healthy() and self.rig.get(self.axis, '-AtTarget') == 1,
                      'settled feedback sets at-target after dwell', 3)
