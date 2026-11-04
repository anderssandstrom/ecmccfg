"""Bounded motor moves and read-only status checks for the hardware slit IOC."""
import math
import time

# Numeric PV access is shared; no simulated Plant or simulation Rig is used.
from slit.rig import Client


def validate_profile(profile):
    if profile['schema'] != 1 or profile['axes'] != {
            'TR_LO': 5, 'TR_HI': 6, 'CENTERY': 12, 'GAPY': 13}:
        raise ValueError('profile must describe hardware slit schema 1 and its four axis IDs')
    if set(profile['physical']) != {'TR_LO', 'TR_HI'}:
        raise ValueError('physical travel bounds required for TR_LO and TR_HI')
    for axis, limits in profile['physical'].items():
        if len(limits) != 2 or not all(math.isfinite(v) for v in limits) or limits[0] >= limits[1]:
            raise ValueError('invalid travel bounds: ' + axis)
    for key in ('step', 'velocity', 'tolerance', 'timeout'):
        if not math.isfinite(profile[key]) or profile[key] <= 0:
            raise ValueError('profile ' + key + ' must be finite and positive')
    if profile['step'] <= 2 * profile['tolerance']:
        raise ValueError('step must exceed twice the position tolerance')
    power = profile['encoder_power']
    if (power['axis'] != 'TR_HI' or power['encoder'] != 2 or power['backup'] != 1
            or not math.isfinite(power['timeout']) or power['timeout'] <= 0):
        raise ValueError('encoder-power mapping must match the hardware IOC')


class Rig:
    def __init__(self, profile, prefix, client):
        validate_profile(profile)
        self.profile, self.prefix, self.client = profile, prefix, client
        self.origins, self.saved_velocity, self.touched, self.trace = {}, {}, set(), []
        self.authorized = False
        self.stop_requested, self.stop_errors = False, []

    def get(self, axis, field): return self.client.get(self.prefix + axis + field)
    def read(self, suffix): return self.client.get(self.prefix + suffix)

    def healthy(self):
        for suffix, expected in (('MCU-Cfg-Sim-Mode', 0), ('MCU-AppMode', 1), ('m0-Stat-OK', 1)):
            if self.read(suffix) != expected:
                raise AssertionError('IOC/bus state changed: ' + suffix)
        for axis in self.profile['axes']:
            for suffix in ('-ErrId', '-WrnId', '.SEVR'):
                if self.get(axis, suffix):
                    raise AssertionError(axis + ': unexpected ' + suffix + '=' + str(self.get(axis, suffix)))
        self.check_envelope({a: self.get(a, '-PosAct') for a in self.profile['physical']})
        return True

    def check_envelope(self, positions):
        for axis, value in positions.items():
            low, high = self.profile['physical'][axis]
            if not math.isfinite(value) or not low <= value <= high:
                raise AssertionError(f'{axis}: position {value} outside hardware test bounds [{low}, {high}]')

    def guard(self):
        # Read-only identity checks precede every possible write, including cleanup.
        if self.read('MCU-Cfg-Sim-Mode') != 0 or self.read('HardwareSlitTest:Schema') != self.profile['schema']:
            raise RuntimeError('requires the dedicated real-hardware slit IOC; no writes performed')
        for axis, number in self.profile['axes'].items():
            if self.get(axis, '-Id') != number:
                raise RuntimeError('axis identity mismatch: ' + axis)
            for suffix, expected in (('.DIR', 0), ('.OFF', 0), ('.SPMG', 3),
                                     ('.DMOV', 1), ('.MOVN', 0), ('-Busy', 0), ('-InStartup', 0)):
                if self.get(axis, suffix) != expected:
                    raise RuntimeError(axis + ': preflight requires ' + suffix + '=' + str(expected))
            if not self.get(axis, '-LimBwd') or not self.get(axis, '-LimFwd'):
                raise RuntimeError(axis + ': active hardware limit')
            self.origins[axis] = self.get(axis, '.RBV')
            if abs(self.origins[axis] - self.get(axis, '-PosAct')) > self.profile['tolerance']:
                raise RuntimeError(axis + ': motor/native coordinate mismatch')
        if self.get('TR_LO', '-EncCnt') != 1 or self.get('TR_HI', '-EncCnt') != 2:
            raise RuntimeError('encoder count does not match the commissioned hardware setup')
        if self.read('SM00-EnaCmd') != 1:
            raise RuntimeError('hardware suite requires the configured slit state machine enabled')
        self.healthy()
        self.authorized = True

    def validate_target(self, axis, target):
        if not math.isfinite(target): raise ValueError('non-finite target')
        for side in ('Bwd', 'Fwd'):
            if not self.get(axis, '-CfgD' + ('LLM' if side == 'Bwd' else 'HLM') + '-En-RB'):
                raise RuntimeError(axis + ': native soft limits must be enabled')
        low = max(self.get(axis, '.LLM'), self.get(axis, '-CfgDLLM-RB'))
        high = min(self.get(axis, '.HLM'), self.get(axis, '-CfgDHLM-RB'))
        # Virtual motor limits may be disabled (0/0); native dynamic limits still apply.
        if axis in ('CENTERY', 'GAPY') and self.get(axis, '.LLM') == self.get(axis, '.HLM') == 0:
            low, high = self.get(axis, '-CfgDLLM-RB'), self.get(axis, '-CfgDHLM-RB')
        if not low < target < high:
            raise RuntimeError(f'{axis}: target {target} outside active soft limits [{low}, {high}]')
        positions = {a: self.get(a, '-PosAct') for a in self.profile['physical']}
        if axis in positions:
            positions[axis] = target
        else:
            center = target if axis == 'CENTERY' else self.get('CENTERY', '-PosSet')
            gap = target if axis == 'GAPY' else self.get('GAPY', '-PosSet')
            positions = {'TR_LO': center-gap/2, 'TR_HI': center+gap/2}
        self.check_envelope(positions)

    def preflight_moves(self, axes):
        for axis in axes:
            vmax = self.get(axis, '.VMAX')
            if vmax > 0 and self.profile['velocity'] > vmax:
                raise RuntimeError(axis + ': test velocity exceeds motor VMAX')
            for offset in (-self.profile['step'], 0, self.profile['step']):
                self.validate_target(axis, self.origins[axis] + offset)

    def put(self, axis, field, value):
        if not self.authorized: raise RuntimeError('hardware writes require successful preflight')
        if axis not in self.profile['axes'] or field not in ('.VAL', '.VELO', '.STOP'):
            raise RuntimeError('hardware runner only writes motor VAL, VELO and STOP')
        if field == '.VAL':
            self.stop_requested = False
            self.healthy()
            self.validate_target(axis, value)
        self.touched.add(axis)
        return self.client.put(self.prefix + axis + field, value,
                               wait=field not in ('.VAL', '.STOP'), notify=field != '.STOP')

    def wait(self, predicate, description, timeout=None):
        end = time.monotonic() + (timeout or self.profile['timeout'])
        while time.monotonic() < end:
            self.healthy()
            if predicate(): return
            time.sleep(.02)
        raise AssertionError('timeout: ' + description)

    def idle(self):
        return all(self.get(a, '-Busy') == 0 and self.get(a, '.DMOV') == 1
                   and self.get(a, '.MOVN') == 0 for a in self.profile['axes'])

    def start(self, axis, target):
        self.healthy()
        if not self.idle(): raise RuntimeError('axes must be idle before a move')
        self.validate_target(axis, target)
        if axis not in self.saved_velocity:
            self.saved_velocity[axis] = self.get(axis, '.VELO')
        self.put(axis, '.VELO', self.profile['velocity'])
        complete = self.put(axis, '.VAL', target)
        self.wait(lambda: self.get(axis, '-Busy') == 1 or self.get(axis, '.DMOV') == 0,
                  axis + ' motion starts')
        if self.get(axis, '.LVIO'): raise AssertionError(axis + ': move rejected by motor limits')
        return complete

    def move(self, axis, target):
        self.finish(axis, target, self.start(axis, target))

    def finish(self, axis, target, complete):
        self.wait(lambda: complete.is_set() and self.idle()
                  and self.get(axis, '-AtTarget') == 1
                  and abs(self.get(axis, '.RBV') - target) <= self.profile['tolerance']
                  and abs(self.get(axis, '-PosAct') - target) <= self.profile['tolerance'],
                  axis + ' completes commanded move')
        if self.get(axis, '.LVIO'): raise AssertionError(axis + ': motor limit violation')
        self.kinematics()
        self.trace.append({'axis': axis, 'target': target, 'snapshot': self.snapshot()})

    def kinematics(self):
        # Separate CA reads may lag by one publication period; evaluate at rest.
        low, high = self.get('TR_LO', '-PosAct'), self.get('TR_HI', '-PosAct')
        tolerance = 2 * self.profile['tolerance']
        self.wait(lambda: abs(self.get('CENTERY', '-PosAct')-(low+high)/2) <= tolerance
                  and abs(self.get('GAPY', '-PosAct')-(high-low)) <= tolerance,
                  'virtual feedback agrees with physical blade positions')

    def snapshot(self):
        result = {}
        for axis in self.profile['axes']:
            result[axis] = {}
            for field in ('.RBV', '.VAL', '.DMOV', '.MOVN', '.SEVR', '.LVIO', '-PosAct',
                          '-PosSet', '-Busy', '-EnaAct', '-AtTarget', '-ErrId', '-WrnId',
                          '-SetEncIdCmd-RB', '-Enc02-PwrState'):
                if axis != 'TR_HI' and field == '-Enc02-PwrState': continue
                try: result[axis][field] = self.get(axis, field)
                except Exception as error: result[axis][field] = str(error)
        return result

    def stop_all(self, retry=False):
        if not self.authorized or not self.touched or (self.stop_requested and not retry): return
        self.stop_requested = True
        # Request STOP before gathering diagnostic snapshots. Stop the directly
        # commanded axes first, then the remaining members of the coupled group.
        axes = sorted(self.profile['axes'], key=lambda axis: axis not in self.saved_velocity)
        for axis in axes:
            try: self.put(axis, '.STOP', 1)
            except Exception as error: self.stop_errors.append(str(error))

    def cleanup(self):
        if not self.authorized or not self.touched: return []
        self.stop_all(retry=bool(self.stop_errors))
        errors = list(self.stop_errors)
        end = time.monotonic() + self.profile['timeout']
        try:
            while not self.idle():
                if time.monotonic() >= end: raise RuntimeError('cleanup: axes did not stop')
                time.sleep(.02)
        except Exception as error: errors.append(str(error))
        for axis, value in self.saved_velocity.items():
            try: self.put(axis, '.VELO', value)
            except Exception as error: errors.append(str(error))
        return errors
