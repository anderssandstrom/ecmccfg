"""Hardware runner boundary checks; no EPICS imports, connections or physical I/O."""
from contextlib import redirect_stdout, redirect_stderr
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests/integration'))
from slit_hardware import run
from slit_hardware.rig import Rig, validate_profile
from slit_hardware.cases import GROUPS, make_suite


class Clock:
    now = 0.
    def monotonic(self): return self.now
    def sleep(self, duration): self.now += duration


class HardwareBoundary:
    """Controlled CA boundary to exercise the actual hardware runner methods."""
    def __init__(self, clock):
        self.clock, self.values, self.writes, self.pending = clock, {}, [], []
        self.closed, self.active, self.fault_on_move = False, None, False
        self.completed_at = 0
        self.interrupt_on_move, self.stall = False, False
        for axis, number in run.json.loads(run.DEFAULT_PROFILE.read_text())['axes'].items():
            fields = {'.DIR': 0, '.OFF': 0, '.SPMG': 3, '.DMOV': 1, '.MOVN': 0,
                      '.VELO': .4, '.VMAX': 5, '.SEVR': 0, '.LVIO': 0, '-Busy': 0,
                      '-InStartup': 0, '-LimBwd': 1, '-LimFwd': 1, '-ErrId': 0,
                      '-WrnId': 0, '-VelAct': 0, '-AtTarget': 1, '-Id': number, '-EnaAct': 0,
                      '.LLM': -1, '.HLM': 1, '-CfgDLLM-RB': -1, '-CfgDHLM-RB': 1,
                      '-CfgDLLM-En-RB': 1, '-CfgDHLM-En-RB': 1, '-EncMode-RB': 0,
                      '-EncForceOn-RB': 0, '-EncCnt': 2 if axis == 'TR_HI' else 1,
                      '-SetEncIdCmd-RB': 2 if axis == 'TR_HI' else 1,
                      '-Enc02-PwrState': 3, '-Enc02-PwrEnable-RB': 1, '-Enc02-Ready': 1,
                      '-Enc02-PwrOn': 1, '-Enc02-Absolute': 1, '-Enc01-Absolute': 0, '-Enc01-Ready': 1}
            for field, value in fields.items(): self.values['HW:'+axis+field] = value
        self.values.update({'HW:MCU-Cfg-Sim-Mode': 0, 'HW:MCU-AppMode': 1,
                            'HW:m0-Stat-OK': 1, 'HW:HardwareSlitTest:Schema': 1,
                            'HW:SM00-EnaCmd': 1})
        self.positions = {'TR_LO': -.15, 'TR_HI': .15}
        self.update_coordinates()
        for axis in ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY'):
            self.values['HW:'+axis+'.VAL'] = self.values['HW:'+axis+'-PosAct']

    def update_coordinates(self):
        low, high = self.positions['TR_LO'], self.positions['TR_HI']
        for axis, pos in dict(self.positions, CENTERY=(low+high)/2, GAPY=high-low).items():
            for field in ('-PosAct', '-PosSet', '.RBV'):
                self.values['HW:'+axis+field] = pos

    def update(self):
        if self.active:
            axis, target, end = self.active
            if self.fault_on_move: self.values['HW:TR_HI-ErrId'] = 123
            fraction = 0 if self.stall else min(1, (self.clock.now-(end-.5))/.5)
            self.positions = {a: before+(self.destination[a]-before)*fraction
                              for a, before in self.initial_positions.items()}
            self.update_coordinates()
            if fraction >= 1:
                self.stop()
                self.completed_at = self.clock.now
        elif self.clock.now-self.completed_at > 2:
            self.values['HW:TR_HI-Enc02-PwrState'] = 1
            self.values['HW:TR_HI-SetEncIdCmd-RB'] = 1
            self.values['HW:TR_HI-Enc02-Ready'] = 0
            self.values['HW:TR_HI-Enc02-PwrOn'] = 0

    def stop(self):
        for axis in ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY'):
            for field, value in (('-Busy', 0), ('.DMOV', 1), ('.MOVN', 0), ('-VelAct', 0)):
                self.values['HW:'+axis+field] = value
        for event in self.pending: event.set()
        self.pending = []
        self.active = None

    def get(self, name):
        self.update()
        return self.values[name]

    def put(self, name, value, **kwargs):
        self.writes.append((name, value))
        self.values[name] = value
        if name.endswith('.STOP'):
            self.stop()
            return None
        if not name.endswith('.VAL'): return None
        axis = name[3:-4]
        self.initial_positions = dict(self.positions)
        self.destination = dict(self.positions)
        low, high = self.positions['TR_LO'], self.positions['TR_HI']
        if axis in self.positions: self.destination[axis] = value
        elif axis == 'CENTERY':
            self.destination.update(TR_LO=value-(high-low)/2, TR_HI=value+(high-low)/2)
        else:
            self.destination.update(TR_LO=(low+high)/2-value/2, TR_HI=(low+high)/2+value/2)
        self.active = (axis, value, self.clock.now+.5)
        for field, state in (('-Busy', 1), ('.DMOV', 0), ('.MOVN', 1), ('-EnaAct', 1), ('-VelAct', .1)):
            self.values['HW:'+axis+field] = state
        self.values['HW:TR_HI-Enc02-PwrState'] = 3
        self.values['HW:TR_HI-Enc02-Ready'] = 1
        self.values['HW:TR_HI-Enc02-PwrOn'] = 1
        self.values['HW:TR_HI-SetEncIdCmd-RB'] = 2
        if self.interrupt_on_move: raise KeyboardInterrupt
        event = Event()
        self.pending.append(event)
        return event

    def close(self): self.closed = True


class HardwareRunnerTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads(run.DEFAULT_PROFILE.read_text())
        self.clock = Clock()
        self.client = HardwareBoundary(self.clock)
        self.rig = Rig(self.profile, 'HW:', self.client)

    def test_plan_never_imports_epics_or_connects(self):
        with patch.object(run, 'Client', side_effect=AssertionError('connection attempted')):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(run.main([]), 0)
        self.assertEqual(make_suite(None, GROUPS).countTestCases(), 8)
        self.assertEqual(make_suite(None, GROUPS, ('motor_stop',)).countTestCases(), 1)

    def test_bad_identity_modes_and_statuses_never_write(self):
        for field, value in (('MCU-Cfg-Sim-Mode', 1), ('HardwareSlitTest:Schema', 7),
                             ('TR_HI-Id', 5), ('TR_LO.OFF', .1), ('TR_LO.DIR', 1),
                             ('TR_LO.SPMG', 1), ('TR_LO-Busy', 1), ('TR_HI-EncCnt', 1),
                             ('TR_LO-ErrId', 123), ('TR_HI-LimFwd', 0), ('m0-Stat-OK', 0)):
            with self.subTest(field=field):
                client = HardwareBoundary(self.clock)
                client.values['HW:'+field] = value
                rig = Rig(self.profile, 'HW:', client)
                with self.assertRaises((RuntimeError, AssertionError)): rig.guard()
                self.assertEqual(rig.cleanup(), [])
                self.assertEqual(client.writes, [])

    def test_targets_and_virtual_projection_are_checked_before_writes(self):
        # Exercise a deliberately tighter custom envelope independently of IOC limits.
        self.profile["physical"] = {axis: [-.5, .5] for axis in self.profile["physical"]}
        self.rig.guard()
        for axis, target in (('TR_LO', .6), ('TR_HI', -2), ('CENTERY', .49), ('GAPY', 1.1)):
            with self.subTest(axis=axis):
                with self.assertRaises((RuntimeError, AssertionError)):
                    self.rig.start(axis, target)
                self.assertEqual(self.client.writes, [])
        self.client.values['HW:TR_LO-CfgDLLM-En-RB'] = 0
        with self.assertRaises(RuntimeError): self.rig.start('TR_LO', -.1)
        self.assertEqual(self.client.writes, [])

    def test_profile_rejects_invalid_motion_settings(self):
        for key, value in (('step', .01), ('step', float('nan')), ('velocity', 0), ('timeout', -1)):
            bad = copy.deepcopy(self.profile)
            bad[key] = value
            with self.assertRaises(ValueError): validate_profile(bad)

    def run_live_boundary(self, extra=()):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        report = Path(temporary.name)/'hardware.json'
        with patch.dict(sys.modules, {'epics': SimpleNamespace(PV=object())}), \
                patch.object(run, 'Client', return_value=self.client), \
                patch('slit_hardware.rig.time.monotonic', self.clock.monotonic), \
                patch('slit_hardware.rig.time.sleep', self.clock.sleep), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = run.main(['--prefix', 'HW:', '--run', '--report', str(report), *extra])
        return code, json.loads(report.read_text()), ET.parse(report.with_suffix('.xml')).getroot()

    def test_all_cases_restore_origins_velocities_and_write_only_motor_fields(self):
        code, report, xml = self.run_live_boundary()
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 8)
        self.assertTrue(all(t['status'] == 'passed' for t in report['tests']), report)
        self.assertEqual(xml.attrib['errors'], '0')
        self.assertTrue(self.client.closed)
        self.assertAlmostEqual(self.client.positions['TR_LO'], -.15)
        self.assertAlmostEqual(self.client.positions['TR_HI'], .15)
        for axis in self.profile['axes']:
            self.assertEqual(self.client.values['HW:'+axis+'.VELO'], .4)
        self.assertTrue(self.client.writes)
        self.assertTrue(all(n.endswith(('.VAL', '.VELO', '.STOP')) for n, _ in self.client.writes))

    def test_status_only_is_read_only(self):
        code, report, _ = self.run_live_boundary(('--case', 'status'))
        self.assertEqual(code, 0, report)
        self.assertEqual(self.client.writes, [])

    def test_guard_failure_is_reported_without_cleanup_writes(self):
        self.client.values['HW:MCU-Cfg-Sim-Mode'] = 1
        code, report, xml = self.run_live_boundary()
        self.assertEqual(code, 1)
        self.assertIn('error', report)
        self.assertEqual(xml.attrib['errors'], '1')
        self.assertEqual(self.client.writes, [])
        self.assertTrue(self.client.closed)

    def test_motion_fault_stops_suite_and_restores_velocity_without_return_move(self):
        self.client.fault_on_move = True
        original_snapshot = Rig.snapshot
        def snapshot(rig):
            self.assertIsNone(self.client.active, 'STOP must precede failure diagnostics')
            return original_snapshot(rig)
        with patch.object(Rig, 'snapshot', snapshot):
            code, report, xml = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['tests']), 1)
        self.assertEqual(xml.attrib['failures'], '1')
        self.assertEqual(len([n for n, _ in self.client.writes if n.endswith('.VAL')]), 1)
        self.assertEqual(len([n for n, _ in self.client.writes if n.endswith('.STOP')]), 4)
        self.assertEqual(self.client.values['HW:TR_LO.VELO'], .4)
        self.assertTrue(self.client.closed)


    def test_interrupt_stops_active_hardware_request_and_reports_it(self):
        self.client.interrupt_on_move = True
        code, report, xml = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 130)
        self.assertIn('Interrupted', report['error'])
        self.assertEqual(xml.attrib['errors'], '1')
        self.assertEqual(len([n for n, _ in self.client.writes if n.endswith('.STOP')]), 4)
        self.assertEqual(self.client.values['HW:TR_LO.VELO'], .4)
        self.assertTrue(self.client.closed)

    def test_motion_timeout_stops_and_restores_velocity(self):
        self.client.stall = True
        code, report, _ = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 1)
        self.assertIn('timeout:', report['tests'][0]['detail'])
        self.assertEqual(len([n for n, _ in self.client.writes if n.endswith('.STOP')]), 4)
        self.assertEqual(self.client.values['HW:TR_LO.VELO'], .4)

    def test_cleanup_error_is_reported_and_fails_the_run(self):
        original = self.client.put
        def put(name, value, **kwargs):
            if name.endswith('.STOP'): raise RuntimeError('STOP write failed')
            return original(name, value, **kwargs)
        self.client.put = put
        code, report, xml = self.run_live_boundary(('--test', 'lo_both'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['cleanup_errors']), 4)
        self.assertEqual(xml.attrib['errors'], '1')
        self.assertTrue(self.client.closed)


if __name__ == '__main__': unittest.main()
