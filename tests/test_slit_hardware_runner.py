"""Hardware runner boundary checks; no EPICS imports, connections or physical I/O."""
from contextlib import redirect_stdout, redirect_stderr
import copy
import io
import json
import re
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
        self.put_options = []
        self.timeout = 1
        self.pvt_active = None
        self.values['HW:m0s005-BO05-RB'] = 0
        self.brake_phases = {}
        self.closed, self.active, self.fault_on_move = False, None, False
        self.completed_at = 0
        self.interrupt_on_move, self.stall = False, False
        for axis, number in run.json.loads(run.DEFAULT_PROFILE.read_text())['axes'].items():
            fields = {'.DIR': 0, '.OFF': 0, '.SPMG': 3, '.DMOV': 1, '.MOVN': 0,
                      '.VELO': .4, '.VMAX': 5, '.SET': 0, '.FOFF': 1, '.SYNC': 0, '-Homed': 0, '.SEVR': 0, '.LVIO': 0, '-Busy': 0,
                      '-InStartup': 0, '-EnaCmd-RB': 0, '-LimBwd': 1, '-LimFwd': 1, '-ErrId': 0,
                      '-WrnId': 0, '-VelAct': 0, '-AtTarget': 1, '-Id': number, '-EnaAct': 0,
                      '.LLM': -10, '.HLM': 10, '-CfgDLLM-RB': -10, '-CfgDHLM-RB': 10,
                      '-CfgDLLM-En-RB': 1, '-CfgDHLM-En-RB': 1, '-EncMode-RB': 0,
                      '-EncForceOn-RB': 0, '-EncCnt': 2 if axis == 'TR_HI' else 1,
                      '-SetEncIdCmd-RB': 2 if axis == 'TR_HI' else 1,
                      '-Enc02-PwrState': 3, '-Enc02-PwrEnable-RB': 1, '-Enc02-Ready': 1,
                      '-Enc02-PwrOn': 1, '-Enc02-Absolute': 1, '-Enc01-Absolute': 0, '-Enc01-Ready': 1,
                      '-Enc01-Homed': 0, '-Enc02-Homed': 0, '.DLLM': -10, '.DHLM': 10, '.DVAL': 0, '.ACCS': 1,
                      '-CfgSyncSftLim': 0, '-TrjSrcTyp-RB': 0, '-AutoExecuteOnTargetPos-RB': 0, '-ExeCmd-RB': 0,
                      '-MtnCmd': 3, '-MtnCmdData': 0, '-TgtVelCmd': 1, '-TgtPosCmd': 0,
                      '-PVT-UseAxis': 0, '-PVT-Positions': [], '-PVT-Readbacks': []}
            for field, value in fields.items(): self.values['HW:'+axis+field] = value
        self.values.update({'HW:MCU-Cfg-Sim-Mode': 0, 'HW:MCU-AppMode': 1,
                            'HW:m0-Stat-OK': 1, 'HW:HardwareSlitTest:Schema': 1,
                            'HW:SM00-EnaCmd': 1, 'HW:SM00-StateCmd': 0, 'HW:MCU-Cmd.TMOD': 0, 'HW:MCU-Cmd.IFMT': 0,
                            'HW:MCU-Cmd.OFMT': 0, 'HW:MCU-Cmd.SEVR': 0, 'HW:MCU-Cmd.AINP': 'OK'})
        self.values.update({'HW:PVT-'+key: value for key, value in {
            'NumPoints': 64, 'NumPulses': 0, 'StartPulses': 1, 'EndPulses': 64,
            'TimeMode': 0, 'FixedTime': 1., 'Acceleration': .5, 'MoveMode': 0, 'MaxSize': 64,
            'BuildStatus': 0, 'BuildState': 0, 'Build.SEVR': 0, 'ExecuteStatus': 0,
            'ExecuteState': 0, 'Execute.SEVR': 0, 'ReadbackState': 0, 'ReadbackStatus': 0,
            'CurrentPoint': 0, 'Times': [], 'SftTrg': 0}.items()})
        self.positions = {'TR_LO': -.15, 'TR_HI': .15}
        self.mechanical_positions = dict(self.positions)
        self.update_coordinates()
        for axis in ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY'):
            self.values['HW:'+axis+'.VAL'] = self.values['HW:'+axis+'-PosAct']

    def update_coordinates(self):
        low, high = self.positions['TR_LO'], self.positions['TR_HI']
        for axis, pos in dict(self.positions, CENTERY=(low+high)/2, GAPY=high-low).items():
            for field in ('-PosAct', '-PosSet', '-Enc01-PosAct', '-Enc02-PosAct'):
                self.values['HW:'+axis+field] = pos
            sign = -1 if self.values['HW:'+axis+'.DIR'] else 1
            self.values['HW:'+axis+'.RBV'] = self.values['HW:'+axis+'.OFF']+sign*pos

    def update(self):
        if self.pvt_active:
            axis, points, started = self.pvt_active
            fraction = min(len(points)-1, max(0., (self.clock.now-started)*2.5))
            index = min(int(fraction), len(points)-2)
            blend = fraction-index
            before = self.positions[axis]
            self.positions[axis] = points[index]*(1-blend)+points[index+1]*blend
            self.mechanical_positions[axis] += self.positions[axis]-before
            self.update_coordinates()
            self.values['HW:PVT-CurrentPoint'] = int(fraction)
            count = int(self.values['HW:PVT-NumPulses'])
            if count:
                self.values['HW:PVT-SftTrg'] = sum(fraction >= i for i in (2, 3, 4))
                pulse = self.values['HW:PVT-SftTrg']
                self.values['HW:m0s005-BO05-RB'] = int(pulse > 0 and fraction < pulse+1.4)
            if self.fault_on_move: self.values['HW:'+axis+'-ErrId'] = 123
            if fraction >= len(points)-1:
                self.pvt_active = None
                self.stop()
                self.values['HW:m0s005-BO05-RB'] = 0
                self.values['HW:PVT-ExecuteState'] = 0
                self.values['HW:PVT-ExecuteStatus'] = 1
                self.completed_at = self.clock.now
            return
        if self.active:
            axis, target, end = self.active
            if self.fault_on_move: self.values['HW:TR_HI-ErrId'] = 123
            start = max(end-.5, self.brake_phases.get(axis, (0, -1))[1])
            fraction = 0 if self.stall else max(0, min(1, (self.clock.now-start)/(end-start)))
            self.values['HW:'+axis+'-VelAct'] = .1 if fraction > 0 else 0
            previous = dict(self.positions)
            self.positions = {a: before+(self.destination[a]-before)*fraction
                              for a, before in self.initial_positions.items()}
            for axis in self.positions:
                self.mechanical_positions[axis] += self.positions[axis]-previous[axis]
            self.update_coordinates()
            if fraction >= 1:
                self.stop()
                self.completed_at = self.clock.now
        elif self.clock.now-self.completed_at > 2:
            self.values['HW:TR_HI-Enc02-PwrState'] = 1
            self.values['HW:TR_HI-SetEncIdCmd-RB'] = 1
            self.values['HW:TR_HI-Enc02-Ready'] = 0
            self.values['HW:TR_HI-Enc02-PwrOn'] = 0
            self.values['HW:TR_HI-Enc01-Homed'] = self.values['HW:TR_HI-Enc02-Homed']

    def enable_brake(self, axis, enabled):
        if axis not in self.positions: return
        self.brake_phases[axis] = (enabled, self.clock.now+(.25 if enabled else .2))
        if enabled: self.completed_at = self.clock.now

    def update_brakes(self):
        for axis, channel, slave in (('TR_LO', '01', '014'), ('TR_HI', '02', '012')):
            if (not self.active and not self.pvt_active and self.clock.now-self.completed_at > 2
                    and self.values['HW:'+axis+'-EnaAct']):
                self.values['HW:'+axis+'-EnaAct'] = 0
                self.values['HW:'+axis+'-EnaCmd-RB'] = 0
                self.enable_brake(axis, 0)
            enabled, transition = self.brake_phases.get(axis, (0, -1))
            self.values['HW:m0s005-BO'+channel+'-RB'] = int(enabled and self.clock.now >= transition)
            self.values['HW:m0s'+slave+'-Drv01-Cmd-RB'] = int(enabled or self.clock.now < transition)

    def stop(self):
        for axis in ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY'):
            for field, value in (('-Busy', 0), ('.DMOV', 1), ('.MOVN', 0), ('-VelAct', 0), ('-ExeCmd-RB', 0)):
                self.values['HW:'+axis+field] = value
        for event in self.pending: event.set()
        self.pending = []
        self.active = None

    def get(self, name):
        self.update()
        self.update_brakes()
        return self.values[name]

    def pv(self, name):
        return SimpleNamespace(get=lambda **kwargs: self.values[name])

    def put(self, name, value, **kwargs):
        self.writes.append((name, value))
        self.put_options.append((name, dict(kwargs)))
        if name.endswith('.VAL') and kwargs.get('notify', True) and self.pending:
            raise RuntimeError('second put-notify would queue behind active motor processing')
        self.values[name] = value
        if name.endswith('-TrjSrcTyp-Cmd'):
            self.values[name.replace('-Cmd', '-RB')] = value
            return None
        if name == 'HW:SM00-EnaCmd':
            self.values['HW:SM00-StateCmd'] = 0
            return None
        if name.startswith('HW:PVT-') or '-PVT-' in name:
            if name.endswith('-PVT-Positions') or name in ('HW:PVT-Times', 'HW:PVT-NumPoints', 'HW:PVT-FixedTime'):
                self.values['HW:PVT-BuildStatus'] = 0
            if name == 'HW:PVT-Build':
                self.values['HW:PVT-BuildStatus'] = 1
                self.values['HW:PVT-BuildState'] = 0
            elif name == 'HW:PVT-Execute':
                self.values['HW:PVT-SftTrg'] = 0
                selected = [a for a in self.positions if self.values['HW:'+a+'-PVT-UseAxis']]
                assert len(selected) == 1
                axis = selected[0]
                self.pvt_active = (axis, list(self.values['HW:'+axis+'-PVT-Positions']), self.clock.now)
                self.values['HW:PVT-ExecuteState'] = 2
                self.values['HW:PVT-ExecuteStatus'] = 0
                for field, state in (('-Busy', 1), ('.DMOV', 0), ('.MOVN', 1), ('-EnaAct', 1)):
                    self.values['HW:'+axis+field] = state
            elif name == 'HW:PVT-Readback':
                for axis in self.positions:
                    self.values['HW:'+axis+'-PVT-Readbacks'] = list(self.values['HW:'+axis+'-PVT-Positions'])[2:5] if self.values['HW:PVT-NumPulses'] else list(self.values['HW:'+axis+'-PVT-Positions'])
                self.values['HW:PVT-ReadbackState'] = 0
                self.values['HW:PVT-ReadbackStatus'] = 1
            elif name == 'HW:PVT-Abort':
                self.pvt_active = None
                self.stop()
                self.values['HW:m0s005-BO05-RB'] = 0
                self.values['HW:PVT-ExecuteState'] = 0
                self.values['HW:PVT-ExecuteStatus'] = 3
            return None
        if name == 'HW:MCU-Cmd.AOUT':
            match = re.fullmatch(r'Cfg.SetAxisAutoExec\((\d+),(\d+)\)', value)
            if match:
                axis = 'TR_LO' if int(match[1]) == 5 else 'TR_HI'
                self.values['HW:'+axis+'-AutoExecuteOnTargetPos-RB'] = int(match[2])
                reply = 'OK'
            elif value.startswith('GetAxisAutoExec'):
                axis = 'TR_LO' if '(5)' in value else 'TR_HI'
                reply = str(self.values['HW:'+axis+'-AutoExecuteOnTargetPos-RB'])
            elif value.startswith('GetAxisEnableAutoEnable'): reply = '1'
            else: raise AssertionError('unsupported text command: '+value)
            self.values['HW:MCU-Cmd.AINP'] = reply
            return None
        for suffix in ('-EnaCmd', '-ExeCmd', '-MtnCmd', '-MtnCmdData', '-TgtVelCmd', '-TgtPosCmd'):
            if name.endswith(suffix):
                axis = name[3:-len(suffix)]
                if suffix == '-EnaCmd':
                    self.enable_brake(axis, value)
                    self.values['HW:'+axis+'-EnaAct'] = value
                    self.values['HW:'+axis+'-EnaCmd-RB'] = value
                    if value:
                        for name in self.positions: self.values['HW:'+name+'-TrjSrcTyp-RB'] = 0
                if suffix == '-ExeCmd': self.values['HW:'+axis+'-ExeCmd-RB'] = value
                if ((suffix == '-ExeCmd' and value == 1) or
                    (suffix == '-TgtPosCmd' and self.values['HW:'+axis+'-AutoExecuteOnTargetPos-RB'])):
                    target = self.values['HW:'+axis+'-TgtPosCmd']
                    if self.values['HW:'+axis+'-MtnCmd'] == 2: target += self.positions[axis]
                    return self.begin_move(axis, target, notify=False)
                return None
        if name.endswith(('.DIR', '.OFF', '.FOFF', '-CfgSyncSftLim')):
            if name.endswith('.FOFF') and value == 'Frozen': self.values[name] = 1
            if name.endswith(('.DIR', '.OFF')):
                axis = name[3:-4]
                sign = -1 if self.values['HW:'+axis+'.DIR'] else 1
                off = self.values['HW:'+axis+'.OFF']
                limits = [off+sign*self.values['HW:'+axis+f] for f in ('.DLLM', '.DHLM')]
                self.values['HW:'+axis+'.LLM'], self.values['HW:'+axis+'.HLM'] = min(limits), max(limits)
                self.update_coordinates()
            return None
        if name.endswith('-EncForceOn'):
            self.values[name+'-RB'] = value
            return None
        if name.endswith('-SetEncPosCmd'):
            axis = name[3:-len('-SetEncPosCmd')]
            assert axis in ('TR_LO', 'TR_HI')
            assert self.values['HW:'+axis+'-EnaAct'] == 0
            self.positions[axis] = value  # reference only; mechanics do not move
            self.update_coordinates()
            self.values['HW:'+axis+'-Homed'] = 1
            self.values['HW:'+axis+('-Enc02-Homed' if axis == 'TR_HI' else '-Enc01-Homed')] = 1
            return None
        if name.endswith('.SYNC'):
            axis = name[3:-5]
            self.values['HW:'+axis+'.VAL'] = self.values['HW:'+axis+'.RBV']
            self.values['HW:'+axis+'.DVAL'] = self.values['HW:'+axis+'-PosAct']
            self.values[name] = 0
            return None
        if name.endswith('.STOP'):
            self.stop()
            return None
        if not name.endswith('.VAL'): return None
        axis = name[3:-4]
        sign = -1 if self.values['HW:'+axis+'.DIR'] else 1
        target = sign*(value-self.values['HW:'+axis+'.OFF'])
        self.values['HW:'+axis+'.DVAL'] = target
        return self.begin_move(axis, target, **kwargs)

    def begin_move(self, axis, value, **kwargs):
        if not self.values['HW:'+axis+'-EnaAct']: self.enable_brake(axis, 1)
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
        self.values['HW:'+axis+'-VelAct'] = 0
        self.values['HW:TR_HI-Enc02-PwrState'] = 3
        self.values['HW:TR_HI-Enc02-Ready'] = 1
        self.values['HW:TR_HI-Enc02-PwrOn'] = 1
        self.values['HW:TR_HI-SetEncIdCmd-RB'] = 2
        if self.interrupt_on_move: raise KeyboardInterrupt
        if not kwargs.get('notify', True): return None
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
        self.assertEqual(make_suite(None, GROUPS).countTestCases(), 49)
        self.assertEqual(make_suite(None, GROUPS, ('motor_stop',)).countTestCases(), 2)

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
        for axis, target in (('TR_LO', .6), ('TR_HI', -2), ('CENTERY', .6), ('GAPY', 1.4)):
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
        profile_path = Path(temporary.name)/'profile.json'
        profile_path.write_text(json.dumps(self.profile))
        with patch.dict(sys.modules, {'epics': SimpleNamespace(PV=object())}), \
                patch.object(run, 'Client', return_value=self.client), \
                patch('slit_hardware.rig.time.monotonic', self.clock.monotonic), \
                patch('slit_hardware.rig.time.sleep', self.clock.sleep), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = run.main(['--prefix', 'HW:', '--run', '--report', str(report),
                             '--profile', str(profile_path), *extra])
        return code, json.loads(report.read_text()), ET.parse(report.with_suffix('.xml')).getroot()

    def test_all_cases_reference_zero_restore_velocities_and_use_expected_fields(self):
        code, report, xml = self.run_live_boundary()
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 49)
        self.assertTrue(all(t['status'] == 'passed' for t in report['tests']), report)
        self.assertEqual(xml.attrib['errors'], '0')
        self.assertTrue(self.client.closed)
        self.assertAlmostEqual(self.client.positions['TR_LO'], 0)
        self.assertAlmostEqual(self.client.positions['TR_HI'], 0)
        for axis in self.profile['axes']:
            self.assertEqual(self.client.values['HW:'+axis+'.VELO'], .4)
        self.assertTrue(self.client.writes)
        self.assertTrue(all(n.endswith(('.VAL', '.VELO', '.STOP', '-SetEncPosCmd', '.DIR', '.OFF', '.FOFF',
                                       '.SYNC', '-EncForceOn', '-CfgSyncSftLim', '-EnaCmd', '-ExeCmd',
                                       '-MtnCmd', '-MtnCmdData', '-TgtVelCmd', '-TgtPosCmd', '-TrjSrcTyp-Cmd', 'SM00-EnaCmd'))
                            or n.startswith(('HW:MCU-Cmd.', 'HW:PVT-')) or '-PVT-' in n
                            for n, _ in self.client.writes))
        self.assertAlmostEqual(self.client.mechanical_positions['TR_LO'], -.15)
        self.assertAlmostEqual(self.client.mechanical_positions['TR_HI'], .15)
        self.assertEqual(report['origins'], {a: 0 for a in self.profile['axes']})
        for axis in self.profile['physical']:
            self.assertEqual(self.client.values['HW:'+axis+'.SET'], 0)
            self.assertEqual(self.client.values['HW:'+axis+'.FOFF'], 1)
            self.assertEqual(self.client.values['HW:'+axis+'-Enc01-Homed'], 1)

    def test_no_sm_cases_disable_management_for_every_motion_and_restore_sources(self):
        for axis in self.profile['physical']:
            self.client.values['HW:'+axis+'-TrjSrcTyp-RB'] = 1
        original_move = self.client.begin_move
        def begin(*args, **kwargs):
            self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 0)
            for axis in self.profile['physical']:
                self.assertEqual(self.client.values['HW:'+axis+'-TrjSrcTyp-RB'], 0)
            return original_move(*args, **kwargs)
        original_put = self.client.put
        def put(name, value, **kwargs):
            if name == 'HW:PVT-Execute':
                self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 0)
            return original_put(name, value, **kwargs)
        with patch.object(self.client, 'begin_move', begin), patch.object(self.client, 'put', put):
            code, report, _ = self.run_live_boundary(('--case', 'no_sm'))
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 23)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)
        for axis in self.profile['physical']:
            self.assertEqual(self.client.values['HW:'+axis+'-TrjSrcTyp-RB'], 1)
            self.assertEqual(self.client.values['HW:'+axis+'-EnaAct'], 0)
        self.assertEqual(len([x for x in report['trace'] if x.get('action') == 'disable state machine']), 23)

    def test_no_sm_fault_restores_state_machine_without_return_move(self):
        self.client.fault_on_move = True
        code, report, _ = self.run_live_boundary(('--case', 'no_sm'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['tests']), 1)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)
        self.assertIsNone(self.client.active)
        self.assertEqual(len([n for n, _ in self.client.writes if n.endswith('.VAL')]), 1)

    def test_no_sm_restoration_failure_is_retried_by_runner_cleanup(self):
        original = self.client.put
        failed = []
        def put(name, value, **kwargs):
            if name == 'HW:SM00-EnaCmd' and value == 1 and not failed:
                failed.append(True)
                raise RuntimeError('temporary enable restore failure')
            return original(name, value, **kwargs)
        with patch.object(self.client, 'put', put):
            code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'physical_lo'))
        self.assertEqual(code, 1)
        self.assertIn('temporary enable restore failure', report['tests'][0]['detail'])
        self.assertEqual(report['cleanup_errors'], [])
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)

    def test_no_sm_detects_unexpected_state_machine_enable(self):
        original = self.client.begin_move
        def begin(*args, **kwargs):
            event = original(*args, **kwargs)
            self.client.values['HW:SM00-EnaCmd'] = 1
            return event
        with patch.object(self.client, 'begin_move', begin):
            code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'physical_lo'))
        self.assertEqual(code, 1)
        self.assertIn('must remain disabled', report['tests'][0]['detail'])
        self.assertIsNone(self.client.active)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)

    def test_no_sm_interrupt_stops_and_restores_management(self):
        self.client.interrupt_on_move = True
        code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'physical_lo'))
        self.assertEqual(code, 130, report)
        self.assertIsNone(self.client.active)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)
        self.assertEqual(report['cleanup_errors'], [])

    def test_no_sm_pvt_support_is_checked_before_any_writes(self):
        del self.client.values['HW:PVT-MaxSize']
        code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'pvt'))
        self.assertEqual(code, 1)
        self.assertIn('PVT preflight failed', report['error'])
        self.assertEqual(self.client.writes, [])

    def test_brake_outputs_are_observed_and_never_written_directly(self):
        code, report, _ = self.run_live_boundary(('--case', 'brake'))
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 6)
        actions = [t.get('action') for t in report['trace']]
        self.assertEqual(actions.count('brake opening phase'), 2)
        self.assertEqual(actions.count('brake closing phase'), 2)
        self.assertEqual(actions.count('brake applied after move'), 2)
        self.assertEqual(actions.count('brake applied after STOP'), 2)
        self.assertFalse(any('m0s005-BO' in n or '-Drv01-' in n for n, _ in self.client.writes))

    def test_stuck_closed_brake_fails_release_and_stops(self):
        original = self.client.get
        def get(name):
            value = original(name)
            return 0 if name == 'HW:m0s005-BO01-RB' else value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'brake', '--test', 'lo_release'))
        self.assertEqual(code, 1)
        self.assertIn('brake released', report['tests'][0]['detail'])
        self.assertIsNone(self.client.active)

    def test_brake_application_during_motion_fails(self):
        original = self.client.get
        def get(name):
            value = original(name)
            if (name == 'HW:m0s005-BO01-RB' and self.client.active
                    and self.clock.now > self.client.active[2]-.15): return 0
            return value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'brake', '--test', 'lo_motion'))
        self.assertEqual(code, 1)
        self.assertIn('brake applied during movement', report['tests'][0]['detail'])
        self.assertIsNone(self.client.active)

    def test_missing_brake_readback_prevents_setup_writes(self):
        original = self.client.get
        def get(name):
            if name == 'HW:m0s005-BO01-RB': raise RuntimeError('brake readback unavailable')
            return original(name)
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'brake'))
        self.assertEqual(code, 1)
        self.assertIn('brake readback unavailable', report['error'])
        self.assertEqual(self.client.writes, [])

    def test_pvt_triggers_count_and_latched_samples_in_both_management_modes(self):
        code, report, _ = self.run_live_boundary(('--case', 'pvt', '--case', 'no_sm', '--test', 'triggers'))
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 4)
        profiles = [x for x in report['trace'] if x.get('action') == 'PVT completed']
        self.assertEqual(len(profiles), 4)
        for trace in profiles:
            self.assertEqual(trace['trigger_counts'], [0, 1, 2, 3])
            self.assertEqual(trace['verdict']['pulses'], 3)
            self.assertEqual(trace['readbacks'], trace['geometry']['positions'][2:5])
            self.assertEqual([e['level'] for e in trace['output_edges']], [1, 0, 1, 0, 1, 0])
        self.assertEqual(self.client.values['HW:PVT-NumPulses'], 0)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)

    def test_pvt_extra_trigger_aborts_and_restores_configuration(self):
        original = self.client.get
        def get(name):
            value = original(name)
            if name == 'HW:PVT-SftTrg' and value > 0: return 4
            return value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'pvt', '--test', 'lo_triggers'))
        self.assertEqual(code, 1)
        self.assertIn('unexpected software trigger count', report['tests'][0]['detail'])
        self.assertIn(('HW:PVT-Abort', 1), self.client.writes)
        self.assertEqual(self.client.values['HW:PVT-NumPulses'], 0)

    def test_pvt_missing_trigger_is_detected(self):
        original = self.client.get
        def get(name):
            value = original(name)
            return min(value, 2) if name == 'HW:PVT-SftTrg' else value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'pvt', '--test', 'lo_triggers'))
        self.assertEqual(code, 1)
        self.assertIn('matches requested pulses', report['tests'][0]['detail'])
        self.assertIn(('HW:PVT-Abort', 1), self.client.writes)

    def test_pvt_wrong_trigger_sample_is_detected(self):
        original = self.client.pv
        def pv(name):
            if name.endswith('-PVT-Readbacks'):
                return SimpleNamespace(get=lambda **kwargs: [0, 0, 0])
            return original(name)
        with patch.object(self.client, 'pv', pv):
            code, report, _ = self.run_live_boundary(('--case', 'pvt', '--test', 'lo_triggers'))
        self.assertEqual(code, 1)
        self.assertIn('PVT trigger sample', report['tests'][0]['detail'])

    def test_pvt_unlinked_output_fails_even_when_software_triggers_pass(self):
        original = self.client.get
        def get(name):
            value = original(name)
            return 0 if name == 'HW:m0s005-BO05-RB' else value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'pvt', '--test', 'lo_triggers'))
        self.assertEqual(code, 1)
        self.assertIn('expected three output pulses', report['tests'][0]['detail'])
        self.assertIn(('HW:PVT-Abort', 1), self.client.writes)

    def test_pvt_abort_lowers_output_after_a_pulse(self):
        original = self.client.get
        def get(name):
            value = original(name)
            if name == 'HW:PVT-SftTrg' and value > 0: return 4
            return value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'no_sm', '--test', 'lo_triggers'))
        self.assertEqual(code, 1)
        self.assertEqual(self.client.values['HW:m0s005-BO05-RB'], 0)
        self.assertEqual(self.client.values['HW:SM00-EnaCmd'], 1)
        self.assertFalse(any('BO05' in n for n, _ in self.client.writes))

    def test_untriggered_pvt_rejects_an_unexpected_output_pulse(self):
        original = self.client.get
        def get(name):
            value = original(name)
            if name == 'HW:m0s005-BO05-RB' and self.client.pvt_active: return 1
            return value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'pvt', '--test', 'lo_round_trip'))
        self.assertEqual(code, 1)
        self.assertIn('output pulsed with triggers disabled', report['tests'][0]['detail'])
        self.assertIn(('HW:PVT-Abort', 1), self.client.writes)

    def test_high_pvt_output_prevents_setup_writes(self):
        original = self.client.get
        def get(name):
            value = original(name)
            return 1 if name == 'HW:m0s005-BO05-RB' else value
        with patch.object(self.client, 'get', get):
            code, report, _ = self.run_live_boundary(('--case', 'pvt'))
        self.assertEqual(code, 1)
        self.assertIn('output must be low', report['error'])
        self.assertEqual(self.client.writes, [])

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
        code, report, xml = self.run_live_boundary(('--case', 'motion', '--test', 'lo_both'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['cleanup_errors']), 4)
        self.assertEqual(xml.attrib['errors'], '1')
        self.assertTrue(self.client.closed)


    def test_larger_moves_reject_narrow_ioc_limits(self):
        self.assertEqual(self.profile['step'], 5.0)
        self.assertEqual(self.profile['velocity'], 1.0)
        for axis in self.profile['axes']:
            for field, value in (('.LLM', -1), ('.HLM', 1),
                                 ('-CfgDLLM-RB', -1), ('-CfgDHLM-RB', 1)):
                self.client.values['HW:'+axis+field] = value
        self.rig.guard()
        with self.assertRaisesRegex(RuntimeError, 'outside active soft limits'):
            self.rig.preflight_moves(('TR_LO', 'TR_HI'))
        self.assertEqual(self.client.writes, [])

    def test_timeout_preserves_actual_completion_conditions(self):
        self.client.positions['TR_HI'] = .900634765625
        self.client.update_coordinates()
        self.client.values['HW:TR_HI-AtTarget'] = 0
        self.rig.guard()
        complete = Event()
        complete.set()
        with patch('slit_hardware.rig.time.monotonic', self.clock.monotonic), \
                patch('slit_hardware.rig.time.sleep', self.clock.sleep):
            with self.assertRaisesRegex(AssertionError, 'Completion conditions before STOP'):
                self.rig.finish('TR_HI', .05, complete)
        observed = self.rig.trace[-1]['completion_conditions']
        self.assertEqual(observed['target'], .05)
        self.assertEqual(observed['native_position'], .900634765625)
        self.assertEqual(observed['motor_position'], .900634765625)
        self.assertEqual(observed['at_target'], 0)
        self.assertTrue(observed['put_complete'])
        self.assertEqual(observed['axes']['TR_HI'], {'-Busy': 0, '.DMOV': 1, '.MOVN': 0})


    def test_relative_window_uses_fresh_encoder_position_outside_absolute_ten_mm(self):
        self.profile['reference_to_zero'] = False
        self.client.positions.update(TR_LO=35, TR_HI=0)  # startup counter is not yet referenced
        self.client.update_coordinates()
        for axis in self.profile['axes']:
            for field, value in (('.LLM', -100), ('.HLM', 100), ('.DLLM', -100), ('.DHLM', 100),
                                 ('-CfgDLLM-RB', -100), ('-CfgDHLM-RB', 100)):
                self.client.values['HW:'+axis+field] = value
        self.client.values['HW:TR_HI-Enc02-PwrState'] = 1
        self.client.values['HW:TR_HI-Enc02-Ready'] = 0
        self.client.values['HW:TR_HI-SetEncIdCmd-RB'] = 1
        original = self.client.put
        def put(name, value, **kwargs):
            result = original(name, value, **kwargs)
            if name == 'HW:TR_HI-EncForceOn':
                self.client.values[name+'-RB'] = value
                if value:
                    self.client.positions['TR_HI'] = 40  # first real BiSS sample
                    self.client.update_coordinates()
                    self.client.values['HW:TR_HI-Enc02-PwrState'] = 3
                    self.client.values['HW:TR_HI-Enc02-Ready'] = 1
                    self.client.values['HW:TR_HI-SetEncIdCmd-RB'] = 2
            return result
        self.client.put = put
        code, report, _ = self.run_live_boundary()
        self.assertEqual(code, 0, report)
        self.assertEqual(report['origins']['TR_LO'], 35)
        self.assertEqual(report['origins']['TR_HI'], 40)
        holds = [(name, value) for name, value in self.client.writes if name.endswith('-EncForceOn')]
        self.assertEqual(holds, [('HW:TR_HI-EncForceOn', 1), ('HW:TR_HI-EncForceOn', 0)])
        self.assertEqual(self.client.writes[:2], holds)
        self.assertAlmostEqual(self.client.positions['TR_LO'], 35)
        self.assertAlmostEqual(self.client.positions['TR_HI'], 40)
        self.assertIn(('HW:TR_LO.VAL', 40), self.client.writes)
        self.assertIn(('HW:TR_HI.VAL', 45), self.client.writes)

    def test_failed_startup_wake_restores_hold_without_motor_writes(self):
        self.client.values['HW:TR_HI-Enc02-PwrState'] = 1
        self.client.values['HW:TR_HI-Enc02-Ready'] = 0
        self.client.values['HW:TR_HI-SetEncIdCmd-RB'] = 1
        code, report, _ = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 1)
        self.assertIn('BiSS ready', report['error'])
        self.assertEqual(self.client.writes, [('HW:TR_HI-EncForceOn', 1), ('HW:TR_HI-EncForceOn', 0)])
        self.assertEqual(report['cleanup_errors'], [])
        self.assertTrue(self.client.closed)

    def test_sleeping_source_is_not_woken_with_drive_enabled(self):
        self.client.values['HW:TR_HI-Enc02-PwrState'] = 1
        self.client.values['HW:TR_HI-SetEncIdCmd-RB'] = 1
        self.client.values['HW:TR_HI-EnaAct'] = 1
        code, report, _ = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 1)
        self.assertIn('disable', report['error'])
        self.assertEqual(self.client.writes, [])

    def test_existing_absolute_profile_keeps_absolute_envelope(self):
        del self.profile['relative_to_start']
        self.client.positions['TR_HI'] = 35
        self.client.update_coordinates()
        with self.assertRaisesRegex(AssertionError, 'outside hardware test bounds'):
            self.rig.guard()
        self.assertEqual(self.client.writes, [])


    def test_zero_reference_after_wake_preserves_physical_position(self):
        self.client.positions.update(TR_LO=35, TR_HI=40)
        self.client.mechanical_positions = dict(self.client.positions)
        self.client.update_coordinates()
        self.rig.guard()
        with patch('slit_hardware.rig.time.monotonic', self.clock.monotonic), \
                patch('slit_hardware.rig.time.sleep', self.clock.sleep):
            self.rig.initialize_origins()
        self.assertEqual(self.client.positions, {'TR_LO': 0, 'TR_HI': 0})
        self.assertEqual(self.client.mechanical_positions, {'TR_LO': 35, 'TR_HI': 40})
        self.assertFalse(any(n.endswith('.VAL') for n, _ in self.client.writes))
        self.assertEqual(self.rig.origins, {a: 0 for a in self.profile['axes']})
        self.assertEqual([(n, v) for n, v in self.client.writes if n.endswith('-SetEncPosCmd')],
                         [('HW:TR_LO-SetEncPosCmd', 0), ('HW:TR_HI-SetEncPosCmd', 0)])
        self.assertFalse(any(n.endswith(('.SET', '.FOFF', '.DVAL')) for n, _ in self.client.writes))
        self.assertEqual(self.client.values['HW:TR_HI-Enc01-Homed'], 1)
        self.assertEqual(self.client.values['HW:TR_HI-Enc02-Homed'], 1)
        self.rig.preflight_moves(self.profile['axes'])

    def test_zero_reference_failure_restores_encoder_hold(self):
        original = self.client.put
        def put(name, value, **kwargs):
            if name.endswith('-SetEncPosCmd'): raise RuntimeError('reference write failed')
            return original(name, value, **kwargs)
        self.client.put = put
        code, report, _ = self.run_live_boundary(('--case', 'motion'))
        self.assertEqual(code, 1)
        self.assertIn('reference write failed', report['error'])
        self.assertEqual(self.client.values['HW:TR_LO.SET'], 0)
        self.assertEqual(self.client.values['HW:TR_LO.FOFF'], 1)
        self.assertEqual(self.client.values['HW:TR_HI-EncForceOn-RB'], 0)
        self.assertFalse(any(n.endswith('.VAL') for n, _ in self.client.writes))
        self.assertTrue(self.client.closed)


    def test_zero_reference_waits_for_motor_acknowledgement(self):
        original_put, original_get = self.client.put, self.client.get
        acknowledgements = {}
        def put(name, value, **kwargs):
            result = original_put(name, value, **kwargs)
            if name.endswith('-SetEncPosCmd'):
                axis = name[3:-len('-SetEncPosCmd')]
                self.client.values['HW:'+axis+'.DMOV'] = 0
                acknowledgements['HW:'+axis+'.DMOV'] = self.clock.now+.2
            return result
        def get(name):
            if name in acknowledgements and self.clock.now >= acknowledgements[name]:
                self.client.values[name] = 1
                del acknowledgements[name]
            return original_get(name)
        self.client.put, self.client.get = put, get
        self.rig.guard()
        with patch('slit_hardware.rig.time.monotonic', self.clock.monotonic), \
                patch('slit_hardware.rig.time.sleep', self.clock.sleep):
            self.rig.initialize_origins()
        self.assertFalse(acknowledgements)
        self.assertEqual(self.client.values['HW:TR_LO.SET'], 0)
        self.assertEqual(self.client.values['HW:TR_HI.SET'], 0)
        self.assertFalse(any(n.endswith('.VAL') for n, _ in self.client.writes))


    def test_repeated_targets_use_one_completion_request_and_ordinary_burst(self):
        code, report, _ = self.run_live_boundary(('--case', 'motion', '--test', 'repeated_motor_targets'))
        self.assertEqual(code, 0, report)
        flags = [options for name, options in self.client.put_options if name.endswith('.VAL')]
        self.assertEqual([options['notify'] for options in flags], [True, False, False, False, True])
        self.assertTrue(all(options['wait'] is False for options in flags))
        self.assertEqual(report['tests'][0]['status'], 'passed')
        self.assertTrue(self.client.closed)


    def test_target_write_moves_do_not_write_execute_high_and_restore_mode(self):
        code, report, _ = self.run_live_boundary(('--case', 'target_write'))
        self.assertEqual(code, 0, report)
        self.assertEqual(len(report['tests']), 4)
        self.assertFalse(any(n.endswith('-ExeCmd') and v == 1 for n, v in self.client.writes))
        for axis in self.profile['physical']:
            self.assertEqual(self.client.values['HW:'+axis+'-AutoExecuteOnTargetPos-RB'], 0)
            self.assertEqual(self.client.values['HW:'+axis+'-EnaAct'], 0)
        self.assertEqual(self.client.values['HW:MCU-Cmd.TMOD'], 0)

    def test_native_failure_restores_mode_and_staged_parameters(self):
        self.client.fault_on_move = True
        code, report, _ = self.run_live_boundary(('--case', 'target_write'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['tests']), 1)
        self.assertEqual(self.client.values['HW:TR_LO-AutoExecuteOnTargetPos-RB'], 0)
        self.assertEqual(self.client.values['HW:TR_LO-TgtPosCmd'], 0)
        self.assertEqual(self.client.values['HW:TR_LO-MtnCmd'], 3)
        self.assertEqual(self.client.values['HW:MCU-Cmd.TMOD'], 0)
        self.assertEqual(self.client.values['HW:MCU-Cmd.OFMT'], 0)

    def test_motor_offset_direction_checks_native_travel_and_restores_fields(self):
        code, report, _ = self.run_live_boundary(('--case', 'motor'))
        self.assertEqual(code, 0, report)
        for axis in self.profile['physical']:
            for field, expected in (('.DIR', 0), ('.OFF', 0), ('.FOFF', 1),
                                    ('-CfgSyncSftLim', 0), ('-CfgDLLM-RB', -10), ('-CfgDHLM-RB', 10)):
                self.assertEqual(self.client.values['HW:'+axis+field], expected)
            targets = [v for n, v in self.client.writes if n == 'HW:'+axis+'.VAL']
            self.assertIn(7.5, targets)
            self.assertIn(-7.5, targets)

    def test_motor_mapping_cannot_bypass_native_or_physical_bounds(self):
        self.rig.guard()
        self.client.put('HW:TR_LO.DIR', 1)
        self.client.put('HW:TR_LO.OFF', 25)
        self.rig.validate_target('TR_LO', 5)  # user coordinate 20 is within transformed motor limits
        self.assertEqual(self.rig.user_position('TR_LO', 5), 20)
        self.assertEqual(self.rig.dial_position('TR_LO', 20), 5)
        self.client.values['HW:TR_LO.LLM'] = -100
        self.client.values['HW:TR_LO.HLM'] = 100
        with self.assertRaisesRegex(RuntimeError, 'outside active soft limits'):
            self.rig.put('TR_LO', '.VAL', 40)  # dial -15, even though user target looks valid
        self.assertFalse(any(n.endswith('.VAL') for n, _ in self.client.writes))

    def test_pvt_restores_controller_selection_and_requires_measured_motion(self):
        original = self.client.put
        def put(name, value, **kwargs):
            result = original(name, value, **kwargs)
            if name == 'HW:PVT-Execute':
                axis, points, started = self.client.pvt_active
                self.client.pvt_active = (axis, [points[0]]*len(points), started)
            return result
        self.client.put = put
        code, report, _ = self.run_live_boundary(('--case', 'pvt'))
        self.assertEqual(code, 1)
        self.assertIn('physically traverse both sides', report['tests'][0]['detail'])
        self.assertTrue(any(n == 'HW:PVT-Abort' for n, _ in self.client.writes))
        self.assertEqual(self.client.values['HW:PVT-NumPoints'], 64)
        self.assertEqual(self.client.values['HW:PVT-FixedTime'], 1)
        for axis in self.profile['axes']:
            self.assertEqual(self.client.values['HW:'+axis+'-PVT-UseAxis'], 0)
        self.assertEqual(self.client.values['HW:TR_LO-EnaAct'], 0)


    def test_coordinate_failure_restores_dir_off_and_soft_limit_policy(self):
        self.client.fault_on_move = True
        code, report, _ = self.run_live_boundary(('--case', 'motor'))
        self.assertEqual(code, 1)
        self.assertEqual(len(report['tests']), 1)
        self.assertEqual(self.client.values['HW:TR_LO.DIR'], 0)
        self.assertEqual(self.client.values['HW:TR_LO.OFF'], 0)
        self.assertEqual(self.client.values['HW:TR_LO.FOFF'], 1)
        self.assertEqual(self.client.values['HW:TR_LO-CfgSyncSftLim'], 0)
        self.assertEqual(self.client.values['HW:TR_LO-CfgDLLM-RB'], -10)

    def test_missing_pvt_support_refuses_before_zero_reference_writes(self):
        del self.client.values['HW:PVT-MaxSize']
        code, report, _ = self.run_live_boundary(('--case', 'pvt'))
        self.assertEqual(code, 1)
        self.assertIn('PVT preflight failed', report['error'])
        self.assertEqual(self.client.writes, [])


    def test_target_write_can_prepare_after_virtual_axis_ownership(self):
        for axis in self.profile['physical']:
            self.client.values['HW:'+axis+'-TrjSrcTyp-RB'] = 1
        code, report, _ = self.run_live_boundary(('--test', 'test_target_write_lo_auto_enable'))
        self.assertEqual(code, 0, report)
        self.assertEqual(self.client.values['HW:TR_LO-TrjSrcTyp-RB'], 0)
        self.assertFalse(any(n.endswith('-ExeCmd') and v == 1 for n, v in self.client.writes))


if __name__ == '__main__': unittest.main()
