"""Live terminal-state/alarm/recovery checks shared by the two slit suites."""
import time
from slit_motion_checks import MotionExpectation

STALL_ERROR = 0x14c19
SLAVE_INTERLOCK = 0x1432e


def wait_checked(rig, predicate, description, timeout, allowed=None):
    allowed = allowed or {}
    end = time.monotonic()+timeout
    while time.monotonic() < end:
        if hasattr(rig, 'plant'): rig.plant.check()
        if rig.client.get(rig.prefix+'MCU-AppMode') != 1 or rig.client.get(rig.prefix+'m0-Stat-OK') != 1:
            raise AssertionError('IOC/bus state changed during recovery test')
        accepted = {0}
        for axis in rig.profile['axes']:
            codes = set(allowed.get(axis, ())) | {0}
            accepted.update(codes)
            error = int(rig.get(axis, '-ErrId'))
            if error not in codes: raise AssertionError(f'{axis}: unexpected error {error:#x}')
        global_error = int(rig.client.get(rig.prefix+'MCU-ErrId'))
        if global_error not in accepted: raise AssertionError(f'unexpected controller error {global_error:#x}')
        if hasattr(rig, 'check_envelope'):
            rig.check_envelope({a: rig.get(a, '-PosAct') for a in rig.profile['physical']})
        else:
            for axis in rig.profile['physical']:
                if abs(rig.get(axis, '-PosAct')) >= .8: raise AssertionError('simulation recovery travel bound')
        if rig.motion_expectation is not None: rig.motion_expectation.check()
        if predicate(): return
        time.sleep(.02)
    raise AssertionError('timeout: '+description)


def motor_idle(rig, axes):
    return all(rig.get(a, '-Busy') == 0 and abs(rig.get(a, '-VelAct')) < .005
               and rig.get(a, '.DMOV') == 1 and rig.get(a, '.MOVN') == 0
               and rig.get(a, '.MIP') == 0 and rig.get(a, '.PACT') == 0 for a in axes)


def stationary_dwell(rig, positions, allowed=None, seconds=.6):
    pulses_end = time.monotonic()+seconds
    tolerance = rig.profile.get('tolerance', .015)
    def held():
        if not motor_idle(rig, rig.profile['axes']): raise AssertionError('motor record or native axis restarted after termination')
        for axis, value in positions.items():
            if abs(rig.get(axis, '-PosAct')-value) > tolerance: raise AssertionError(axis+': cancelled motion replayed')
        return time.monotonic() >= pulses_end
    wait_checked(rig, held, 'terminal motor state remains stationary', seconds+5, allowed)


def reset_known_errors(rig, allowed):
    # Validate every error before issuing a reset that affects all axes.
    wait_checked(rig, lambda: motor_idle(rig, rig.profile['axes']), 'standstill before known-error reset', 5, allowed)
    rig.client.put(rig.prefix+'MCU-ErrRst', 1)
    if rig.client.get(rig.prefix+'SM00-EnaCmd'):
        rig.client.put(rig.prefix+'SM00-StateCmd', 3)
    wait_checked(rig, lambda: all(rig.get(a, '-ErrId') == 0 for a in rig.profile['axes'])
                 and rig.client.get(rig.prefix+'SM00-StateCmd') == 0,
                 'known test fault resets without motion', 5)


def stall_alarm(rig, axis, trigger, step, velocity, validate):
    number = rig.profile['axes'][axis]
    origin = rig.get(axis, '-PosAct')
    target = origin+step
    validate(axis, target)
    transport = rig.open_text_commands()
    keys = ('MonAtTargetTol', 'MonEnableStallMon', 'MonStallMinTimeOut', 'MonStallTimeFactor')
    saved = {}
    complete = None
    allowed = {axis: (STALL_ERROR,)}
    previous = rig.motion_expectation
    try:
        query = lambda name: rig.text_command(f'GetAxis{name}({number})', query=True)
        config = lambda name, value: rig.text_command(f'Cfg.SetAxis{name}({number},{value:.12g})')
        saved = {key: query(key) for key in keys}
        if query('MonEnableAtTargetMon') != 1: raise AssertionError('stall test requires enabled AtTarget monitoring')
        config('MonEnableStallMon', 1)
        config('MonStallMinTimeOut', 1000)  # Dedicated fixtures both run at 1 kHz.
        config('MonStallTimeFactor', 0)
        config('MonAtTargetTol', 0)  # Status cannot assert; monitor itself stays enabled.
        rig.motion_expectation = MotionExpectation(rig, axis)
        if trigger == 'motor':
            if hasattr(rig, 'start'): complete = rig.start(axis, target)
            else: complete = rig.start_move(axis, target)
        else:
            for field, value in (('-ExeCmd', 0), ('-MtnCmd', 3), ('-MtnCmdData', 0),
                                 ('-TgtVelCmd', velocity), ('-TgtPosCmd', target), ('-EnaCmd', 1)):
                rig.client.put(rig.prefix+axis+field, value)
            wait_checked(rig, lambda: rig.get(axis, '-EnaAct') == 1, 'enabled for native stall test', 10)
            rig.client.put(rig.prefix+axis+'-ExeCmd', 1)
        wait_checked(rig, lambda: rig.get(axis, '-BusyLocal') == 0
                     and abs(rig.get(axis, '-VelAct')) < .005
                     and abs(rig.get(axis, '-PosAct')-target) < rig.profile.get('tolerance', .015),
                     'trajectory ends before AtTarget stall timeout', rig.profile.get('timeout', 15))
        if rig.get(axis, '-AtTarget') != 0: raise AssertionError('stall setup did not hold AtTarget low')
        if rig.get(axis, '.DMOV') != 0 or (complete is not None and complete.is_set()):
            raise AssertionError('unfulfilled AtTarget incorrectly completed the motor request before the alarm')
        wait_checked(rig, lambda: rig.get(axis, '-ErrId') == STALL_ERROR
                     and rig.get(axis, '-AtTarget') == 0 and rig.get(axis, '-EnaAct') == 0
                     and motor_idle(rig, (axis,)) and int(rig.get(axis, '.MSTA')) & (1 << 9)
                     and rig.get(axis, '.SEVR') > 0 and (complete is None or complete.is_set()),
                     'stall alarm terminates motor processing despite AtTarget=0', 8, allowed)
        rig.trace.append({'action': 'AtTarget stall alarm terminates motor record', 'axis': axis,
                          'trigger': trigger, 'snapshot': rig.snapshot()})
        positions = {a: rig.get(a, '-PosAct') for a in rig.profile['physical']}
        rig.client.put(rig.prefix+axis+'.STOP', 1, wait=False, notify=False)
        stationary_dwell(rig, positions, allowed)
        for key, value in saved.items(): config(key, value)
        saved = {}
        reset_known_errors(rig, allowed)
        stationary_dwell(rig, positions)
        rig.client.put(rig.prefix+axis+'.SYNC', 1)
        wait_checked(rig, lambda: rig.get(axis, '.SEVR') == 0
                     and not int(rig.get(axis, '.MSTA')) & (1 << 9), 'motor alarm clears after reset', 5)
        rig.motion_expectation = None
        rig.move(axis, origin)
        rig.trace.append({'action': 'stall recovery completed', 'axis': axis, 'trigger': trigger})
    finally:
        rig.motion_expectation = previous
        for key, value in saved.items():
            rig.text_command(f'Cfg.SetAxis{key}({number},{value:.12g})')
        rig.close_text_commands(transport)


def stop_blade_during_virtual(rig, master, blade, interface, step, validate):
    origin = rig.get(master, '-PosAct')
    target = origin+step
    validate(master, target)
    if rig.client.get(rig.prefix+'SM00-EnaCmd') != 1:
        raise AssertionError('coordinated stop requires the master/slave state machine')
    previous = rig.motion_expectation
    expectation = MotionExpectation(rig, master)
    rig.motion_expectation = expectation
    allowed = {a: (SLAVE_INTERLOCK,) for a in ('CENTERY', 'GAPY')}
    try:
        complete = rig.start(master, target) if hasattr(rig, 'start') else rig.start_move(master, target)
        wait_checked(rig, lambda: rig.get(master, '-Busy') == 1
                     and all(rig.get(a, '-TrjSrcTyp-RB') == 1 and abs(rig.get(a, '-VelAct')) > .005
                             and abs(rig.get(a, '-PosAct')-expectation.before[a]) > .03 for a in rig.profile['physical']),
                     'both blades move under virtual ownership before physical STOP', 10)
        before = {a: rig.get(a, '-PosAct') for a in rig.profile['physical']}
        field = '.STOP' if interface == 'motor' else '-StpCmd'
        rig.client.put(rig.prefix+blade+field, 1, wait=False, notify=False)
        wait_checked(rig, lambda: motor_idle(rig, rig.profile['axes']) and complete.is_set(),
                     'physical STOP terminates the complete coordinated group', 8, allowed)
        if abs(rig.get(master, '-PosAct')-target) <= rig.profile.get('tolerance', .015):
            raise AssertionError('physical STOP was ignored until virtual target completion')
        positions = {a: rig.get(a, '-PosAct') for a in rig.profile['physical']}
        for a, value in positions.items():
            bound = rig.profile.get('velocity', .4)**2/(2*rig.get(a, '.ACCS'))+rig.profile.get('velocity', .4)+.05
            if abs(value-before[a]) > bound: raise AssertionError(a+': excessive coordinated stopping travel')
        stationary_dwell(rig, positions, allowed)
        reset_known_errors(rig, allowed)
        stationary_dwell(rig, positions)
        rig.motion_expectation = None
        rig.move(master, origin)
        rig.kinematics()
        rig.trace.append({'action': 'physical STOP interrupts virtual motion and recovers',
                          'master': master, 'blade': blade, 'interface': interface, 'snapshot': rig.snapshot()})
    finally:
        rig.motion_expectation = previous


class StallCases:
    pass


class CoupledStopCases:
    pass


def _stall(axis, trigger):
    def test(self): self.exercise_stall(axis, trigger)
    test.__name__ = 'test_stall_'+('lo' if axis == 'TR_LO' else 'hi')+'_'+trigger+'_at_target_zero'
    return test


def _coupled(master, blade, interface):
    def test(self): self.exercise_coupled_stop(master, blade, interface)
    test.__name__ = 'test_'+('center' if master == 'CENTERY' else 'gap')+'_stop_'+('lo' if blade == 'TR_LO' else 'hi')+'_'+interface
    return test


STALL_NAMES = []
COUPLED_STOP_NAMES = []
for _axis in ('TR_LO', 'TR_HI'):
    for _trigger in ('motor', 'native'):
        _test = _stall(_axis, _trigger)
        setattr(StallCases, _test.__name__, _test)
        STALL_NAMES.append(_test.__name__)
    for _master in ('CENTERY', 'GAPY'):
        for _interface in ('motor', 'native'):
            _test = _coupled(_master, _axis, _interface)
            setattr(CoupledStopCases, _test.__name__, _test)
            COUPLED_STOP_NAMES.append(_test.__name__)
STALL_NAMES, COUPLED_STOP_NAMES = tuple(STALL_NAMES), tuple(COUPLED_STOP_NAMES)


def concurrent_physical_moves(rig, primary, secondary, step, velocity, validate):
    """Bounded commanded perturbations; no claim of external-force injection."""
    origins = {a: rig.get(a, '-PosAct') for a in rig.profile['physical']}
    target = origins[primary]+step
    nudge = min(.2, step/10)
    validate(primary, target)
    for offset in (nudge, -nudge, 0): validate(secondary, origins[secondary]+offset)
    saved = {a: rig.get(a, '.VELO') for a in origins}
    previous = rig.motion_expectation
    rig.motion_expectation = None
    successful = False
    try:
        if hasattr(rig, 'touched'): rig.touched.update(origins)
        slow = min(velocity, max(.05, velocity/4))
        rig.client.put(rig.prefix+primary+'.VELO', slow)
        rig.client.put(rig.prefix+secondary+'.VELO', velocity)
        complete = rig.client.put(rig.prefix+primary+'.VAL', target, wait=False)
        wait_checked(rig, lambda: rig.get(primary, '-Busy') == 1
                     and abs(rig.get(primary, '-PosAct')-origins[primary]) > .03,
                     'primary physical move active before secondary perturbation', 10)
        for offset in (nudge, -nudge, 0):
            destination = origins[secondary]+offset
            rig.client.put(rig.prefix+secondary+'.VAL', destination, wait=False, notify=False)
            def secondary_done():
                if rig.get(primary, '-Busy') != 1 or complete.is_set():
                    raise AssertionError('secondary motion prematurely stopped/completed the independent primary axis')
                if abs(rig.get(primary, '.VAL')-target) > rig.profile.get('tolerance', .015):
                    raise AssertionError('secondary motion replaced the independent primary target')
                return (rig.get(secondary, '-Busy') == 0 and rig.get(secondary, '.DMOV') == 1
                        and abs(rig.get(secondary, '-PosAct')-destination) <= rig.profile.get('tolerance', .015))
            wait_checked(rig, secondary_done, 'secondary nudge completes while primary continues', 10)
        wait_checked(rig, lambda: complete.is_set() and motor_idle(rig, rig.profile['axes'])
                     and abs(rig.get(primary, '-PosAct')-target) <= rig.profile.get('tolerance', .015),
                     'independent primary completes its original target', step/slow+15)
        rig.move(primary, origins[primary])
        rig.trace.append({'action': 'independent physical moves overlap without interference',
                          'primary': primary, 'secondary': secondary, 'snapshot': rig.snapshot()})
        successful = True
    finally:
        if not successful:
            for a in origins: rig.client.put(rig.prefix+a+'.STOP', 1, wait=False, notify=False)
        for a, value in saved.items(): rig.client.put(rig.prefix+a+'.VELO', value)
        rig.motion_expectation = previous
