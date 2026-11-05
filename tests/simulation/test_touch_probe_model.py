#!/usr/bin/env python3
"""DS402 probe latch, full auxiliary plant CA adapter and SIM guards; no IOC."""
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools/simulation'), str(ROOT/'tests/integration')]
import touch_probe
from slit.plant import Plant
from slit.rig import Rig
from slit.run import make_suite

p = touch_probe.Model()
assert p.step(0, True, 10, 20).status == 0
assert p.step(17, True, 30, 40).status == 1  # Already-high input is not an edge.
p.step(17, False, 30, 40)
f = p.step(17, True, -15, (1 << 32)+99)
assert f.status == 3 and f.positive == (1 << 32)-15 and f.positive_time == 99
p.step(17, False, 999, 1000)
f = p.step(17, True, 999, 1000)
assert f.positive == (1 << 32)-15 and f.positive_time == 99  # Single shot holds.
assert p.step(0, False, 100, 100).status == 0
assert p.step(49, False, 100, 100).status == 1  # Arm both polarities.
f = p.step(49, True, 100, 0xffffffff)
assert f.status == 3 and f.positive_time == 0xffffffff
f = p.step(49, False, 110, 1 << 32)
assert f.status == 7 and f.negative == 110 and f.negative_time == 0
for bad in (lambda: p.step(3, False, 0, 0), lambda: p.step(17, False, 1.1, 0),
            lambda: p.step(17, False, 0, -1)):
    try: bad()
    except ValueError: pass
    else: raise AssertionError('invalid/unsupported probe input accepted')


class PV:
    def __init__(self, name, values, writes):
        self.pvname, self.values, self.writes = name, values, writes
        self.connected = name in values
        self.read_access = self.write_access = True
    def wait_for_connection(self, timeout): return self.connected
    def get(self, **kwargs): return self.values.get(self.pvname)
    def put(self, value, **kwargs):
        self.values[self.pvname] = value
        if self.pvname+'-RB' in self.values: self.values[self.pvname+'-RB'] = value
        self.writes.append((self.pvname, value))
        return 1
    def disconnect(self): self.connected = False

config = json.loads((ROOT/'tests/integration/slit/ioc/profile.json').read_text())['probe_axis']
values, writes = {}, []
base = 'TEST:SIM:ec0:s20:'
for field, kind, value in (
    ('driveControl01','mbbiDirect',0), ('velocitySetpoint01','longin',10000),
    ('positionActual01','mbboDirect',0), ('positionActual01-RB','mbbiDirect',0),
    ('driveStatus01','mbboDirect',64), ('touchProbeControl01','mbbiDirect',17),
    ('touchProbeStatus01','mbboDirect',0),
    ('touchProbePositionPos01_1','mbboDirect',0), ('touchProbePositionNeg01_1','mbboDirect',0),
    ('touchProbeTimestampPos01_1','mbboDirect',0), ('touchProbeTimestampNeg01_1','mbboDirect',0)):
    values[base+field], values[base+field+'.RTYP'] = value, kind
plant = Plant({'physical': {}, 'probe_axis': config}, 'TEST:SIM:',
              lambda name, **kw: PV(name, values, writes), threading.Thread, timeout=.02)

def wait(predicate):
    deadline = time.monotonic()+2
    while not predicate():
        plant.check()
        assert time.monotonic() < deadline, plant.snapshot()
        time.sleep(.01)

try:
    plant.start()
    plant.configure_probe(.02)
    values[base+'driveControl01'] = 15
    time.sleep(.04)
    assert plant.probe_snapshot()['position_mm'] == 0  # Cannot skip DS402 states.
    for command, status in ((6,0x21), (7,0x23), (15,0x27)):
        values[base+'driveControl01'] = command
        wait(lambda: values[base+'driveStatus01'] == status)
    wait(lambda: values[base+'touchProbeStatus01'] == 3)
    event = plant.probe_snapshot()['event']
    assert event['raw'] == values[base+'touchProbePositionPos01_1'] == 2000
    assert event['time_raw'] == values[base+'touchProbeTimestampPos01_1']
    wait(lambda: plant.probe_snapshot()['position_mm'] > .025)
    assert values[base+'positionActual01'] > 2500
    assert values[base+'touchProbePositionPos01_1'] == 2000  # Latch independent of live counter.
    status_index = next(i for i, pair in enumerate(writes) if pair == (base+'touchProbeStatus01',3))
    assert (base+'touchProbePositionPos01_1',2000) in writes[:status_index]
    values[base+'driveControl01'] = 7
    wait(lambda: values[base+'driveStatus01'] == 0x23)
finally:
    plant.close()
assert values[base+'driveStatus01'] == 8  # Withdraw drive feedback on shutdown.
assert all('PROBE-' not in name for name, value in writes)  # Never write ECMC result PVs.

# Guard auxiliary identity before starting any plant or command writes.
class Client:
    def get(self, name):
        return 1 if name.endswith('MCU-Cfg-Sim-Mode') else 4 if name.endswith('Schema') else 99
    def put(self, *args): raise AssertionError('guard must be read-only')
try: Rig({'schema':4, 'axes':{}, 'probe_axis': config}, 'TEST:', Client(), None).guard()
except RuntimeError as error: assert 'identity' in str(error)
else: raise AssertionError('wrong DS402 axis accepted')

assert len(list(make_suite(None, ('closed',), ('touch_probe','position_compare')))) == 5
print('DS402 probe: edges, status bits, one-shot hold/rearm, raw wraps, native CA feedback/withdrawal and auxiliary identity guard passed; no IOC.')

# Execute the actual CA-case verdicts with controlled responses. An unexpected
# output write, invented sequence or wrong probe payload must fail acceptance.
from types import SimpleNamespace
from slit.cases.position_compare import PositionCompareTests
from slit.cases.touch_probe import TouchProbeTests


def rejects(function):
    try: function()
    except AssertionError: return
    raise AssertionError('broken native result passed acceptance')


class Boundary:
    prefix = 'TEST:'
    profile = {'probe_axis': {'sample_clock': False}}
    def __init__(self, defect=None):
        self.defect, self.state, self.seq, self.running = defect, 0, 0, False
        self.client = SimpleNamespace(get=self.field)
    def field(self, name):
        return 1 if self.running and self.defect == 'output_write' and name.endswith('binaryOutput01') else 0
    def get(self, axis, suffix):
        if suffix == '-PC-State': return self.state
        if suffix == '-PC-Seq': return int(self.running and self.defect == 'invented_event')
        results = {'-Enc01-TP-Seq': self.seq,
                   '-Enc01-TP-Valid': 1, '-Enc01-TP-TimeValid': 1,
                   '-Enc01-TP-TimeRaw': 99 if self.defect != 'wrong_timestamp' else 100,
                   '-Enc01-TP-Pos': .1 if self.defect != 'wrong_position' else .2}
        return results[suffix]
    def put(self, axis, suffix, value):
        if suffix == '-PC-ArmCmd': self.state = 1
        if suffix == '-PC-CancelCmd': self.state = 0
    def wait(self, predicate, description, timeout=15):
        for _ in range(5):
            if predicate(): return
        raise AssertionError('timeout: '+description)
    def assert_stays(self, predicate, description, seconds=1):
        for _ in range(5): assert predicate(), description


for defect in (None, 'output_write', 'invented_event'):
    rig = Boundary(defect)
    case = PositionCompareTests('runTest')
    case.rig, case.axis = rig, 'PROBE'
    case.healthy, case.arrived = lambda: True, lambda target: None
    case.start = lambda target: setattr(rig, 'running', True)
    method = case.test_missing_sample_clock_waits_without_writing_outputs_and_cancels
    if defect: rejects(method)
    else:
        method()
        assert rig.state == 0

for defect in (None, 'wrong_position', 'wrong_timestamp', 'missing_capture'):
    rig = Boundary(defect)
    rig.plant = SimpleNamespace(configure_probe=lambda *args: None,
                                probe_snapshot=lambda: {'event': {'time_raw':99}})
    case = TouchProbeTests('runTest')
    case.rig, case.axis = rig, 'PROBE'
    case.arm, case.healthy, case.arrived = lambda: None, lambda: True, lambda target: None
    case.start = lambda target: setattr(rig, 'seq', 0 if defect == 'missing_capture' else 1)
    if defect: rejects(lambda: case.capture(.1, .25))
    else: case.capture(.1, .25)
print('Live TP and missing-clock compare verdicts reject wrong/missing payloads, output writes and invented events.')
