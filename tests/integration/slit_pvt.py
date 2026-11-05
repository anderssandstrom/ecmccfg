"""Shared bounded asyn profile-move exercise for the separate slit runners."""
import math
import time

TRIGGER_READBACK = "m0s005-BO05-RB"


def profile_geometry(origin, amplitude, velocity, acceleration):
    """Match ECMC's fixed-time averaged-slope cubics, including their extrema."""
    if not all(math.isfinite(v) for v in (origin, amplitude, velocity, acceleration)):
        raise ValueError('finite PVT geometry required')
    if min(amplitude, velocity, acceleration) <= 0: raise ValueError('positive PVT settings required')
    dt = max(1., 3*amplitude/velocity, math.sqrt(12*amplitude/acceleration))
    positions = [origin, origin, origin+amplitude, origin-amplitude, origin, origin]
    slopes = [(b-a)/dt for a, b in zip(positions, positions[1:])]
    velocities = [slopes[0]]+[(a+b)/2 for a, b in zip(slopes, slopes[1:])]+[slopes[-1]]
    extrema, peak_velocity, peak_acceleration = list(positions), 0., 0.
    for x0, x1, v0, v1 in zip(positions, positions[1:], velocities, velocities[1:]):
        a, b, c = 2*x0-2*x1+(v0+v1)*dt, -3*x0+3*x1-(2*v0+v1)*dt, v0*dt
        roots = []
        if abs(a) > 1e-14:
            discriminant = 4*b*b-12*a*c
            if discriminant >= 0:
                roots = [(-2*b+sign*math.sqrt(discriminant))/(6*a) for sign in (-1, 1)]
        elif abs(b) > 1e-14: roots = [-c/(2*b)]
        for u in roots:
            if 0 < u < 1: extrema.append(((a*u+b)*u+c)*u+x0)
        candidates = [0., 1.]+([-b/(3*a)] if abs(a) > 1e-14 and 0 < -b/(3*a) < 1 else [])
        peak_velocity = max(peak_velocity, *(abs((3*a*u*u+2*b*u+c)/dt) for u in candidates))
        peak_acceleration = max(peak_acceleration, abs(2*b/dt**2), abs((6*a+2*b)/dt**2))
    if peak_velocity > velocity*(1+1e-9) or peak_acceleration > acceleration*(1+1e-9):
        raise ValueError('PVT cubic exceeds requested velocity/acceleration bound')
    return dict(positions=positions, interval=dt, extrema=extrema,
                peak_velocity=peak_velocity, peak_acceleration=peak_acceleration,
                duration=dt*(len(positions)-1)+2.)


def array_value(client, name):
    value = client.pv(name).get(use_monitor=False, timeout=client.timeout)
    if value is None: return []
    values = list(value)
    if not all(math.isfinite(v) for v in values): raise AssertionError('non-finite PVT array: '+name)
    return values


def check_profile_support(client, prefix, axes):
    """Read-only capability check before either runner performs setup writes."""
    try:
        if client.get(prefix+'PVT-MaxSize') < 6:
            raise RuntimeError('PVT buffers require at least six points')
        if client.get(prefix+'PVT-ExecuteState') != 0:
            raise RuntimeError('PVT controller already executing')
        for axis in axes: client.get(prefix+axis+'-PVT-UseAxis')
        client.get(prefix+'PVT-SftTrg')
        if client.get(prefix+TRIGGER_READBACK) != 0:
            raise RuntimeError('PVT trigger output must be low before testing')
    except Exception as error:
        raise RuntimeError('PVT preflight failed: deploy the updated slit axis YAML and restart the IOC; '+str(error)) from error


def run_profile(rig, axis, amplitude, velocity, validate, triggers=False):
    """Build/execute/read back one physical-axis profile; restore its controls."""
    axes = list(rig.profile['axes'])
    prefix, client = rig.prefix, rig.client
    origin = rig.get(axis, '-PosAct')
    tolerance = rig.profile.get('tolerance', .015)
    geometry = profile_geometry(origin, amplitude, velocity, rig.get(axis, '.ACCS'))
    for point in geometry['extrema']: validate(axis, point)
    if client.get(prefix+'PVT-ExecuteState') != 0: raise RuntimeError('PVT controller already executing')
    for name in axes:
        if rig.get(name, '.DIR') != 0 or rig.get(name, '.OFF') != 0:
            raise RuntimeError('PVT case requires original DIR/OFF coordinates')
    if rig.get(axis, '-AutoExecuteOnTargetPos-RB') != 0:
        raise RuntimeError('PVT case requires execute-on-target-write disabled')
    if client.get(prefix+'PVT-MaxSize') < len(geometry['positions']):
        raise RuntimeError('PVT buffers too small; restart with updated IOC YAML')
    scalar_keys = ('NumPoints', 'NumPulses', 'StartPulses', 'EndPulses', 'TimeMode',
                   'FixedTime', 'Acceleration', 'MoveMode')
    saved = {prefix+'PVT-'+key: client.get(prefix+'PVT-'+key) for key in scalar_keys}
    saved.update({prefix+name+'-PVT-UseAxis': rig.get(name, '-PVT-UseAxis') for name in axes})
    arrays = {prefix+name+'-PVT-Positions': array_value(client, prefix+name+'-PVT-Positions') for name in axes}
    arrays[prefix+'PVT-Times'] = array_value(client, prefix+'PVT-Times')
    native = {field: rig.get(axis, field) for field in ('-MtnCmd', '-MtnCmdData', '-TgtVelCmd', '-TgtPosCmd')}
    expected_pulses = 3 if triggers else 0
    pulse_counts = []
    output_levels = [0]
    output_edges = []
    if client.get(prefix+TRIGGER_READBACK) != 0:
        raise RuntimeError('PVT trigger output is not low before execution')
    successful = False
    lows, highs = origin, origin
    verdict = {}
    try:
        for name in axes:
            client.put(prefix+name+'-PVT-UseAxis', int(name == axis))
            flat = [rig.get(name, '-PosAct')]*len(geometry['positions'])
            client.put(prefix+name+'-PVT-Positions', geometry['positions'] if name == axis else flat)
        for key, value in (('NumPoints', len(geometry['positions'])), ('NumPulses', expected_pulses),
                           ('StartPulses', 3 if triggers else 1),
                           ('EndPulses', 5 if triggers else len(geometry['positions'])),
                           ('TimeMode', 0), ('FixedTime', geometry['interval']),
                           ('Acceleration', 1.), ('MoveMode', 0)):
            client.put(prefix+'PVT-'+key, value)
        client.put(prefix+'PVT-Times', [geometry['interval']]*len(geometry['positions']))
        rig.wait(lambda: client.get(prefix+'PVT-BuildStatus') == 0, 'PVT new data invalidates previous build', 5)
        client.put(prefix+'PVT-Build', 1)
        rig.wait(lambda: client.get(prefix+'PVT-BuildState') == 0
                 and client.get(prefix+'PVT-BuildStatus') == 1, 'PVT build succeeds', 10)
        if client.get(prefix+'PVT-Build.SEVR'): raise AssertionError('PVT build record alarm')
        client.put(prefix+axis+'-EnaCmd', 1)
        rig.wait(lambda: rig.get(axis, '-EnaAct') == 1, axis+' enabled before profile', 10)
        client.put(prefix+'PVT-Execute', 1, wait=False, notify=False)
        rig.wait(lambda: client.get(prefix+'PVT-ExecuteState') in (1, 2, 3), 'PVT execution becomes active', 5)
        # Read the input record once: its I/O Intr callbacks normally publish
        # pulse increments, and a previous run's count may still be cached.
        client.put(prefix+'PVT-SftTrg.PROC', 1)
        rig.wait(lambda: client.get(prefix+'PVT-SftTrg') == 0, 'PVT trigger counter resets before first pulse', 5)
        def finished():
            nonlocal lows, highs
            for name in axes:
                if rig.get(name, '-ErrId'): raise AssertionError(name+': controller fault during PVT')
            count = client.get(prefix+'PVT-SftTrg')
            if count != int(count) or not 0 <= count <= expected_pulses:
                raise AssertionError('PVT unexpected software trigger count: '+str(count))
            if pulse_counts and count < pulse_counts[-1]:
                raise AssertionError('PVT trigger counter decreased during execution')
            if not pulse_counts or count != pulse_counts[-1]: pulse_counts.append(count)
            level = client.get(prefix+TRIGGER_READBACK)
            if level not in (0, 1): raise AssertionError('PVT invalid trigger output level')
            if not triggers and level: raise AssertionError('PVT output pulsed with triggers disabled')
            if level != output_levels[-1]:
                output_levels.append(level)
                output_edges.append({'level': level, 'count': count, 'time': time.monotonic()})
            position = rig.get(axis, '-PosAct')
            lows, highs = min(lows, position), max(highs, position)
            validate(axis, position)
            state, status = client.get(prefix+'PVT-ExecuteState'), client.get(prefix+'PVT-ExecuteStatus')
            if status in (2, 3, 4): raise AssertionError('PVT execution failed/aborted/timed out: '+str(status))
            if rig.get(axis, '.LVIO') or rig.get(axis, '.SEVR'):
                raise AssertionError(axis+': motor limit violation/alarm during PVT')
            verdict.update(state=state, status=status, minimum=lows, maximum=highs,
                           point=client.get(prefix+'PVT-CurrentPoint'), pulses=count, expected_pulses=expected_pulses)
            return (state == 0 and status == 1 and rig.get(axis, '-Busy') == 0
                    and rig.get(axis, '.DMOV') == 1 and rig.get(axis, '.MOVN') == 0
                    and rig.get(axis, '-AtTarget') == 1 and abs(position-origin) <= tolerance
                    and abs(rig.get(axis, '.RBV')-origin) <= tolerance)
        rig.wait(finished, 'PVT completes and returns to its start', geometry['duration']+15)
        rig.wait(lambda: client.get(prefix+'PVT-SftTrg') == expected_pulses,
                 'PVT software trigger count matches requested pulses', 5)
        if client.get(prefix+TRIGGER_READBACK) != 0:
            raise AssertionError('PVT trigger output remains high after completion')
        if triggers and output_levels != [0, 1, 0, 1, 0, 1, 0]:
            raise AssertionError('PVT expected three output pulses, observed levels '+str(output_levels))
        if lows >= origin-amplitude/2 or highs <= origin+amplitude/2:
            raise AssertionError('PVT must physically traverse both sides of its starting coordinate')
        if client.get(prefix+'PVT-Execute.SEVR'): raise AssertionError('PVT execute record alarm')
        client.put(prefix+'PVT-Readback', 1)
        rig.wait(lambda: client.get(prefix+'PVT-ReadbackState') == 0
                 and client.get(prefix+'PVT-ReadbackStatus') == 1, 'PVT readback succeeds', 10)
        readbacks = array_value(client, prefix+axis+'-PVT-Readbacks')
        if len(readbacks) < 2: raise AssertionError('PVT returned no useful readback samples')
        if triggers:
            expected_samples = geometry['positions'][2:5]
            if len(readbacks) != expected_pulses:
                raise AssertionError(f'PVT expected {expected_pulses} pulse-latched samples, got {len(readbacks)}')
            for index, (actual, expected) in enumerate(zip(readbacks, expected_samples)):
                if abs(actual-expected) > tolerance:
                    raise AssertionError(f'PVT trigger sample {index+1}: {actual} differs from {expected}')
        rig.kinematics()
        rig.trace.append({'action': 'PVT completed', 'axis': axis, 'geometry': geometry,
                          'verdict': dict(verdict), 'trigger_counts': pulse_counts, 'output_edges': output_edges, 'readbacks': readbacks, 'snapshot': rig.snapshot()})
        successful = True
    finally:
        errors = []
        if not successful:
            rig.trace.append({'action': 'PVT failed', 'axis': axis,
                              'geometry': geometry, 'verdict': dict(verdict), 'output_edges': output_edges})
            try: client.put(prefix+'PVT-Abort', 1, wait=False, notify=False)
            except Exception as error: errors.append(str(error))
            for name in axes:
                try: client.put(prefix+name+'.STOP', 1, wait=False, notify=False)
                except Exception as error: errors.append(str(error))
        try:
            client.put(prefix+axis+'-EnaCmd', 0)
            # Restoration must also work when a controller error remains latched.
            end = time.monotonic()+10
            while rig.get(axis, '-Busy') or rig.get(axis, '-EnaAct'):
                if time.monotonic() >= end: raise RuntimeError('PVT cleanup did not reach disabled standstill')
                time.sleep(.02)
        except Exception as error: errors.append(str(error))
        try:
            end = time.monotonic()+5
            while client.get(prefix+TRIGGER_READBACK) != 0:
                if time.monotonic() >= end:
                    raise RuntimeError('PVT cleanup: trigger output did not return low')
                time.sleep(.02)
        except Exception as error: errors.append(str(error))
        for name in axes:
            try: client.put(prefix+name+'-PVT-UseAxis', 0)
            except Exception as error: errors.append(str(error))
        for name, values in arrays.items():
            if values:
                try: client.put(name, values)
                except Exception as error: errors.append(str(error))
        for name, value in saved.items():
            try: client.put(name, value)
            except Exception as error: errors.append(str(error))
        try:
            if rig.get(axis, '-AutoExecuteOnTargetPos-RB') != 0:
                raise RuntimeError('refusing PVT target restoration with execute-on-write active')
            client.put(prefix+axis+'-ExeCmd', 0)
            for field, value in native.items(): client.put(prefix+axis+field, value)
        except Exception as error: errors.append(str(error))
        if errors: raise RuntimeError('PVT cleanup: '+'; '.join(errors))
