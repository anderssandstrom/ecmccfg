#!/usr/bin/env python3
"""Bias removal must settle measured velocity without masking actual restart."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/simulation'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'integration'))
import slit_recovery
from slit.cases import disturbance


def scenario(defect=None):
    clock = SimpleNamespace(now=0.)
    clock.monotonic = lambda: clock.now
    def sleep(seconds): clock.now += seconds
    clock.sleep = sleep
    removed = []
    names = ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY')
    allowed = {'TR_HI': (0x14c08,), 'CENTERY': (0x1432b,), 'GAPY': (0x1432b,)}
    def get(axis, field):
        if field == '-ErrId': return 0xdead if defect == 'fault' else (allowed.get(axis, (0,))[0])
        if field == '-PosAct':
            return .15 if axis == 'TR_HI' and (defect == 'stale' or clock.now < .04) else .1
        if field == '-VelAct': return 2 if axis == 'TR_HI' and (defect == 'velocity' or clock.now < .14) else 0
        if axis == 'TR_HI' and defect == 'busy' and field == '-Busy': return 1
        if axis == 'TR_HI' and defect == 'pact' and field == '.PACT': return 1
        return 1 if field == '.DMOV' else 0
    rig = SimpleNamespace(
        prefix='SIMSLIT:', profile={'axes': dict.fromkeys(names), 'physical': {'TR_LO': {}, 'TR_HI': {}}},
        motion_expectation=None, get=get,
        client=SimpleNamespace(get=lambda name: 0 if name.endswith('MCU-ErrId') else 1),
        plant=SimpleNamespace(check=lambda: None,
            physical_position=lambda axis: .1+(.01 if defect == 'mechanics' and removed else 0),
            inject=lambda axis, **kw: removed.append((axis, kw))))
    with patch.object(disturbance, 'time', clock), patch.object(slit_recovery, 'time', clock):
        try: positions = disturbance.remove_bias_at_standstill(rig, 'TR_HI', allowed)
        except AssertionError as error:
            assert defect is not None, str(error)
            expected = {'fault': 'unexpected error', 'busy': 'processing restarted',
                        'pact': 'processing restarted', 'mechanics': 'mechanics moved',
                        'velocity': 'timeout:', 'stale': 'timeout:'}[defect]
            assert expected in str(error), str(error)
        else:
            assert defect is None, 'bias settling accepted '+str(defect)
            assert clock.now >= .34
            assert positions == {'TR_LO': .1, 'TR_HI': .1}
    assert removed == [('TR_HI', {'encoder_bias_mm': 0})]


for defect in (None, 'velocity', 'stale', 'busy', 'pact', 'mechanics', 'fault'): scenario(defect)
print('Bias removal waits for derivative settling; physical motion, processing restart, stale feedback and faults fail.')
