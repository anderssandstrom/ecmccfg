"""Measured encoder disturbances while independent/coordinated motion is active."""
import time
from .base import SlitCase
from slit_recovery import wait_checked, stationary_dwell, reset_known_errors, motor_idle, slave_fault_errors


def remove_bias_at_standstill(rig, axis, allowed):
    """Publish unbiased feedback without mistaking its derivative for motion."""
    physical = {a: rig.plant.physical_position(a) for a in rig.profile['physical']}
    rig.plant.inject(axis, encoder_bias_mm=0)
    stable_since = None
    def settled():
        nonlocal stable_since
        for name, origin in physical.items():
            if abs(rig.plant.physical_position(name)-origin) > .003:
                raise AssertionError(name+': mechanics moved while removing encoder bias')
        # Relax only the measured-velocity transient, never restarted commands
        # or motor processing. Include diagnostics if a real restart is seen.
        terminal = {'-Busy': 0, '.DMOV': 1, '.MOVN': 0, '.MIP': 0, '.PACT': 0}
        for name in rig.profile['axes']:
            for field, expected in terminal.items():
                actual = rig.get(name, field)
                if actual != expected:
                    raise AssertionError(f'{name}{field}={actual}: processing restarted while removing encoder bias')
        ready = (abs(rig.get(axis, '-PosAct')-rig.plant.physical_position(axis)) < .003
                 and motor_idle(rig, rig.profile['axes']))
        if not ready:
            stable_since = None
            return False
        if stable_since is None: stable_since = time.monotonic()
        return time.monotonic()-stable_since >= .2
    wait_checked(rig, settled, 'unbiased feedback and measured velocity settle at physical standstill', 3, allowed)
    return {a: rig.get(a, '-PosAct') for a in physical}


class DisturbanceTests(SlitCase):
    def setUp(self):
        if self.loop != 'closed': self.skipTest('requires primary EL5042 feedback')
        super().setUp()
        self.transport = self.rig.open_text_commands()
        self.addCleanup(self.rig.close_text_commands, self.transport)
        self.saved_kp = self.rig.get('TR_HI', '-Ctrl-Kp')
        self.addCleanup(self.rig.put, 'TR_HI', '-Ctrl-Kp', self.saved_kp)
        self.rig.put('TR_HI', '-Ctrl-Kp', 0)
        self.addCleanup(self.rig.plant.clear_faults)

    def independent(self, bias, fault):
        rig, axis, peer = self.rig, 'TR_HI', 'TR_LO'
        rig.put(axis, '-EnaCmd', 1)
        rig.wait(lambda: rig.get(axis, '-EnaAct') == 1, 'idle disturbed axis enabled', 10)
        rig.put(peer, '.VELO', .1)
        # start_move does not impose a single-axis isolation expectation: the
        # test intentionally changes the other axis's measurement.
        complete = rig.start_move(peer, .6)
        rig.wait(lambda: rig.get(peer, '-PosAct') > .03, 'peer moving before idle encoder disturbance', 5)
        before = rig.plant.physical_position(axis)
        rig.plant.inject(axis, encoder_bias_mm=bias)
        allowed = slave_fault_errors(rig, axis, 0x14c08) if fault else {}
        end = time.monotonic()+.7
        def observed():
            if rig.get(peer, '-Busy') != 1: raise AssertionError('idle-axis disturbance stopped independent peer')
            if abs(rig.get(peer, '.VAL')-.6) > .001: raise AssertionError('disturbance replaced peer target')
            if abs(rig.plant.physical_position(axis)-before) > .003:
                raise AssertionError('disturbance test unexpectedly drove the idle mechanics')
            if fault:
                return rig.get(axis, '-ErrId') == 0x14c08 and motor_idle(rig, (axis,))
            if rig.get(axis, '-AtTarget') != 0: return False
            if rig.get(axis, '.DMOV') != 1: raise AssertionError('idle motor record became stuck when AtTarget dropped')
            return time.monotonic() >= end
        wait_checked(rig, observed, 'idle disturbance is isolated and sustained lag trips only that axis', 5, allowed)
        rig.plant.inject(axis, encoder_bias_mm=0)
        wait_checked(rig, lambda: complete.is_set() and motor_idle(rig, (peer,))
                     and abs(rig.get(peer, '-PosAct')-.6) < .015,
                     'unaffected peer completes original move despite disturbance/fault', 15, allowed)
        if fault: reset_known_errors(rig, allowed)
        rig.put(axis, '-Ctrl-Kp', self.saved_kp)
        rig.move(peer, 0)
        rig.move(axis, .1)
        rig.move(axis, 0)
        rig.trace.append({'action': 'idle encoder disturbance isolated from physical peer', 'bias': bias, 'fault': fault})

    def test_small_idle_disturbance_keeps_peer_moving_and_motor_idle(self): self.independent(.012, False)
    def test_sustained_idle_lag_fault_does_not_stop_independent_peer(self): self.independent(.05, True)

    def test_sustained_slave_lag_stops_virtual_group_and_recovers(self):
        rig = self.rig
        complete = rig.start_move('CENTERY', .6)
        rig.wait(lambda: rig.get('TR_HI', '-PosAct') > .03, 'virtual movement before slave disturbance', 5)
        rig.plant.inject('TR_HI', encoder_bias_mm=.05)
        allowed = {'TR_HI': (0x14c08,), 'CENTERY': (0x1432b, 0x1432e), 'GAPY': (0x1432b, 0x1432e)}
        wait_checked(rig, lambda: rig.get('TR_HI', '-ErrId') == 0x14c08
                     and motor_idle(rig, rig.names) and complete.is_set(),
                     'sustained slave disturbance stops the coordinated group', 10, allowed)
        if abs(rig.get('CENTERY', '-PosAct')-.6) < .015:
            raise AssertionError('slave fault failed to stop the coordinated move early')
        positions = remove_bias_at_standstill(rig, 'TR_HI', allowed)
        stationary_dwell(rig, positions, allowed)
        reset_known_errors(rig, allowed)
        stationary_dwell(rig, positions)
        rig.put('TR_HI', '-Ctrl-Kp', self.saved_kp)
        rig.move('CENTERY', 0)
        rig.move('GAPY', 0)
        rig.trace.append({'action': 'slave disturbance stops virtual group and fresh motion recovers'})
