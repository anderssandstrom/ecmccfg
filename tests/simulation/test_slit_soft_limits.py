#!/usr/bin/env python3
"""Live-harness soft-limit verdicts without an IOC.

DOC: ecmcAxisSequencer::checkSoftLimits sets direction-specific warning IDs;
ecmcMonitor::checkLimitsInterlock sets predictive target interlocks. This can
stop at the starting position without a fatal error or reaching the boundary.
An unrelated error, stale/no diagnostic or overrun must not count as success.
"""
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/simulation'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integration'))
from slit.cases.limits import LimitTests, controller_soft_limit_stopped

sample = {'position': 0, 'setpoint': 0, 'warning': 0x114D00, 'error': 0,
          'interlock': 1, 'busy': 0, 'stationary': True}
assert controller_soft_limit_stopped(sample, True, -1, 1)
assert controller_soft_limit_stopped({**sample, 'interlock': 0}, True, -1, 1)
assert controller_soft_limit_stopped({**sample, 'warning': 0}, True, -1, 1)
assert controller_soft_limit_stopped({**sample, 'warning': 0x114D01}, False, -1, 1)
# Early predictive stops and boundary stops both require a specific response.
assert controller_soft_limit_stopped({**sample, 'position': .999, 'setpoint': 1}, True, -1, 1)
assert not controller_soft_limit_stopped({**sample, 'warning': 0, 'interlock': 0}, True, -1, 1)
assert not controller_soft_limit_stopped({**sample, 'busy': 1}, True, -1, 1)
assert not controller_soft_limit_stopped({**sample, 'stationary': False}, True, -1, 1)

for change in ({'warning': 0x114D01}, {'error': 0x14C08}, {'error': 0x14417},
               {'position': 1.1}, {'setpoint': -1.1}):
    try:
        controller_soft_limit_stopped({**sample, **change}, True, -1, 1)
    except AssertionError:
        pass
    else:
        raise AssertionError('must reject wrong-direction/unrelated fault or overrun: ' + repr(change))

print('Slit soft limits: predictive warning/interlock stops pass; no-op, moving, wrong-direction, unrelated fault and overrun do not.')


class MotorRig:
    """Rejected targets roll back VAL; same-target writes retain prior LVIO."""
    def __init__(self):
        self.position = self.target = 0
        self.low, self.high, self.lvio = -1, 1, 1
        self.moves, self.rejections, self.writes = [], [], []
    def get(self, axis, suffix):
        return {'.LLM': self.low, '.HLM': self.high, '.LVIO': self.lvio,
                '-PosAct': self.position}[suffix]
    def move(self, axis, target):
        if target == self.target and self.lvio:
            raise RuntimeError('same-target no-op retains stale LVIO')
        assert self.low <= target <= self.high
        self.position = self.target = target
        self.lvio = 0
        self.moves.append(target)
    def put(self, axis, suffix, value):
        self.writes.append((suffix, value))
        if suffix == '.LLM': self.low = value
        elif suffix == '.HLM': self.high = value
        elif suffix == '.VAL':
            assert not self.low <= value <= self.high
            assert self.lvio == 0  # Each rejection must establish fresh LVIO.
            self.lvio = 1
            self.rejections.append((value, self.position))
            complete = threading.Event()
            complete.set()
            return complete
        else:
            raise AssertionError('test must not manually clear LVIO')
    def wait(self, predicate, description, timeout):
        assert predicate(), description


rig = MotorRig()
case = LimitTests('test_motor_soft_limits')
case.rig = rig
case.test_motor_soft_limits()
assert rig.moves == [-.1, .1]
assert rig.rejections == [(.6, -.1), (-.6, .1)]
assert (rig.low, rig.high) == (-1, 1)
assert all(suffix != '.LVIO' for suffix, _ in rig.writes)
print('Motor soft-limit sequence: distinct valid moves clear stale LVIO, both invalid targets reject without motion, original bounds restored.')


class ControllerRig:
    """Retain a rejected target across disable/reset, as in the live failure."""
    def __init__(self):
        self.position = self.target = 0
        self.enabled, self.execute = True, False
        self.warning = self.interlock = 0
        self.trace, self.requests, self.recoveries = [], [], 0
    def get(self, axis, suffix):
        return {'.LLM': -1, '.HLM': 1, '.LVIO': 0, '-EnaAct': self.enabled,
                '-PosAct': self.position, '-PosSet': self.position, '-Busy': 0,
                '-ErrId': 0, '-WrnId': self.warning, '-TgtPosCmd': self.target,
                '-SftLimBwdEna-RB': 1, '-SftLimFwdEna-RB': 1,
                '-SftLimBwdIlock': self.interlock == -1,
                '-SftLimFwdIlock': self.interlock == 1}[suffix]
    def put(self, axis, suffix, value):
        if suffix == '-TgtPosCmd': self.target = value
        elif suffix == '-ExeCmd':
            self.execute = bool(value)
            if value:
                assert self.enabled
                self.requests.append(self.target)
                if -1 <= self.target <= 1:
                    self.position = self.target
                    self.warning = self.interlock = 0
                else:
                    self.interlock = 1 if self.target > 1 else -1
                    self.warning = 0x114D00 if self.target > 1 else 0x114D01
        elif suffix == '-EnaCmd' and not self.enabled:
            # Recovery must not carry the old rejected target/execute request
            # into a write of another bit in the shared control word.
            assert -1 <= self.target <= 1, 'stale rejected target during enable'
            assert not self.execute, 'pending execute during enable'
            self.enabled = True
            self.recoveries += 1
    def wait(self, predicate, description, timeout):
        assert predicate(), description
    def _drive_stationary(self, axis): return True
    def snapshot(self): return {'target': self.target, 'enabled': self.enabled}
    def stop_all(self):
        self.enabled = False
        return []
    def reset(self):
        self.warning = self.interlock = 0
        # Model a pending execute/readback retained with the rejected target.
        self.execute = True


rig = ControllerRig()
case = LimitTests('test_controller_soft_limits_without_motor_rejection')
case.rig = rig
case.test_controller_soft_limits_without_motor_rejection()
assert rig.recoveries == 2
assert [target for target in rig.requests if abs(target) > 1] == [1.2, -1.2]
assert rig.requests[-1] == 0 and rig.position == 0
print('Controller soft-limit recovery: replace rejected target and clear execute before re-enabling; both directions tested.')


class SingleSidedRig:
    """ecmc enforces each enabled soft limit independently of the other flag.

    A zero limit value is a real boundary while its flag is set; the motor
    record's 0,0-disable convention does not apply to the ecmc enable flags.
    """
    profile = {'physical': {'TR_LO': {}, 'TR_HI': {}}}
    STAGING = ('-MtnCmd', '-MtnCmdData', '-TgtVelCmd')

    def __init__(self, defect=None):
        self.defect = defect
        self.trace, self.moved, self.target = [], [], {}
        self.values = {axis: {'-CfgDLLM-RB': -1., '-CfgDHLM-RB': 1.,
                              '-SftLimBwdEna-RB': 1, '-SftLimFwdEna-RB': 1,
                              '-PosAct': 0., '-PosSet': 0., '-Busy': 0, '-ErrId': 0,
                              '-WrnId': 0, '-SftLimFwdIlock': 0, '-SftLimBwdIlock': 0,
                              '-EnaAct': 0, '.LVIO': 0}
                       for axis in self.profile['physical']}

    def get(self, axis, suffix): return self.values[axis][suffix]

    def put(self, axis, suffix, value):
        values = self.values[axis]
        if suffix == '-CfgDLLM': values['-CfgDLLM-RB'] = float(value)
        elif suffix == '-CfgDHLM': values['-CfgDHLM-RB'] = float(value)
        elif suffix == '-SftLimBwdEna': values['-SftLimBwdEna-RB'] = int(value)
        elif suffix == '-SftLimFwdEna': values['-SftLimFwdEna-RB'] = int(value)
        elif suffix == '-EnaCmd': values['-EnaAct'] = int(value)
        elif suffix == '-TgtPosCmd': self.target[axis] = float(value)
        elif suffix == '-ExeCmd':
            if value: self.execute(axis)
        elif suffix not in self.STAGING:
            raise AssertionError('unexpected write ' + suffix)

    def execute(self, axis):
        values = self.values[axis]
        target = self.target[axis]
        low, high = values['-CfgDLLM-RB'], values['-CfgDHLM-RB']
        bwd, fwd = values['-SftLimBwdEna-RB'], values['-SftLimFwdEna-RB']
        if self.defect == 'zero_means_disabled':
            bwd, fwd = (bwd and low != 0), (fwd and high != 0)
        elif self.defect == 'disabled_still_limits':
            bwd = fwd = 1
        blocked_low = bool(bwd) and target < low
        blocked_high = bool(fwd) and target > high
        if blocked_low or blocked_high:
            values['-SftLimBwdIlock'] = int(blocked_low)
            values['-SftLimFwdIlock'] = int(blocked_high)
            values['-WrnId'] = 0x114D01 if blocked_low else 0x114D00
            return
        values['-SftLimBwdIlock'] = values['-SftLimFwdIlock'] = 0
        values['-WrnId'] = 0
        values['-PosAct'] = values['-PosSet'] = target
        self.moved.append((axis, target))

    def wait(self, predicate, description, timeout=15):
        assert predicate(), description

    def stop_all(self): return []

    def reset(self):
        for values in self.values.values():
            values['-WrnId'] = values['-SftLimFwdIlock'] = values['-SftLimBwdIlock'] = 0

    def _drive_stationary(self, axis): return True

    def snapshot(self): return {axis: dict(values) for axis, values in self.values.items()}


def run_single_sided(method, defect=None):
    rig = SingleSidedRig(defect)
    case = LimitTests(method)
    case.rig = rig
    getattr(case, method)()
    assert case.doCleanups()
    for axis in rig.profile['physical']:
        values = rig.values[axis]
        assert values['-CfgDLLM-RB'] == -1. and values['-CfgDHLM-RB'] == 1.
        assert values['-SftLimBwdEna-RB'] == values['-SftLimFwdEna-RB'] == 1
        assert values['-PosAct'] == values['-PosSet'] == 0.
    return rig


method = 'test_single_sided_softlimit_low_enabled_at_zero'
rig = run_single_sided(method)
# Each axis: setup move, rejected zero-boundary crossing, unbounded move, return.
assert rig.moved == [('TR_LO', .1), ('TR_LO', .5), ('TR_LO', 0.),
                     ('TR_HI', .1), ('TR_HI', .5), ('TR_HI', 0.)]
method = 'test_single_sided_softlimit_high_enabled_at_zero'
rig = run_single_sided(method)
assert rig.moved == [('TR_LO', -.1), ('TR_LO', -.5), ('TR_LO', 0.),
                     ('TR_HI', -.1), ('TR_HI', -.5), ('TR_HI', 0.)]
print('Single-sided soft limits: enabled zero boundary rejects the crossing target, disabled side travels past its value.')

# An enabled zero limit that ecmc treated as "off" would move into the rejected target.
for method, defect in (('test_single_sided_softlimit_low_enabled_at_zero', 'zero_means_disabled'),
                       ('test_single_sided_softlimit_high_enabled_at_zero', 'zero_means_disabled'),
                       ('test_single_sided_softlimit_low_enabled_at_zero', 'disabled_still_limits'),
                       ('test_single_sided_softlimit_high_enabled_at_zero', 'disabled_still_limits')):
    try: run_single_sided(method, defect)
    except AssertionError: pass
    else: raise AssertionError('case must reject single-sided defect ' + defect)
print('Single-sided defect controls: zero-treated-as-off and disabled-still-limiting both fail.')
