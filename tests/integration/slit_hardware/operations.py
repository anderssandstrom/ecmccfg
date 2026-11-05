"""Temporary native-mode and motor-coordinate settings for live hardware cases."""
from contextlib import contextmanager
import time
from slit.rig import Rig as SimulationTransport


class Operations:
    # Share checked MCU-Cmd transport only; hardware keeps its own identity guard.
    open_text_commands = SimulationTransport.open_text_commands
    close_text_commands = SimulationTransport.close_text_commands
    text_command = SimulationTransport.text_command

    def wait_configuration(self, predicate, description):
        end = time.monotonic()+self.profile['timeout']
        while time.monotonic() < end:
            if predicate(): return
            time.sleep(.02)
        raise AssertionError('timeout restoring/checking configuration: '+description)

    def stop_and_disable_axes(self):
        self.touched.update(self.profile['physical'])
        self.stop_all(retry=True)
        self.wait_configuration(self.idle, 'axes stopped before state-machine change')
        for axis in self.profile['axes']:
            self.client.put(self.prefix+axis+'-EnaCmd', 0)
        self.wait_configuration(lambda: all(self.get(a, '-EnaAct') == 0
            and self.get(a, '-EnaCmd-RB') == 0 for a in self.profile['axes']),
            'all drives disabled before state-machine change')

    def restore_state_machine(self):
        if self.saved_state_machine is None: return
        enabled, sources = self.saved_state_machine
        self.stop_and_disable_axes()
        for axis, source in sources.items():
            self.client.put(self.prefix+axis+'-TrjSrcTyp-Cmd', source)
        self.wait_configuration(lambda: all(self.get(a, '-TrjSrcTyp-RB') == s
            for a, s in sources.items()), 'original physical trajectory sources')
        self.client.put(self.prefix+'SM00-EnaCmd', enabled)
        self.wait_configuration(lambda: self.read('SM00-EnaCmd') == enabled,
                                'original state-machine enable')
        self.standalone_axis = None
        self.saved_state_machine = None
        self.trace.append({'action': 'restore state machine', 'enabled': enabled})

    @contextmanager
    def without_state_machine(self, axis):
        if not self.authorized or axis not in self.profile['physical']:
            raise RuntimeError('standalone cases require authorized physical axes')
        if self.saved_state_machine is not None:
            raise RuntimeError('state-machine test already active')
        saved = (self.read('SM00-EnaCmd'),
                 {a: self.get(a, '-TrjSrcTyp-RB') for a in self.profile['physical']})
        self.saved_state_machine = saved
        try:
            self.stop_and_disable_axes()
            before = {a: self.get(a, '-PosAct') for a in self.profile['physical']}
            self.client.put(self.prefix+'SM00-EnaCmd', 0)
            self.wait_configuration(lambda: self.read('SM00-EnaCmd') == 0
                and self.read('SM00-StateCmd') == 0, 'disabled state machine is idle')
            # Disable can leave sources unchanged when the SM was already idle.
            for a in self.profile['physical']:
                self.client.put(self.prefix+a+'-TrjSrcTyp-Cmd', 0)
            self.wait_configuration(lambda: all(self.get(a, '-TrjSrcTyp-RB') == 0
                for a in self.profile['physical']), 'standalone physical trajectories')
            self.standalone_axis = axis
            self.standalone_positions = before
            for a, position in before.items(): self.holds_position(a, position)
            self.trace.append({'action': 'disable state machine', 'axis': axis})
            yield
        finally:
            self.restore_state_machine()

    def brake(self, axis):
        channel = {'TR_LO': '01', 'TR_HI': '02'}[axis]
        return self.read('m0s005-BO'+channel+'-RB')

    def drive_control(self, axis):
        slave = {'TR_LO': '014', 'TR_HI': '012'}[axis]
        return int(self.read('m0s'+slave+'-Drv01-Cmd-RB'))

    def check_brake_support(self):
        # Read back native output process images, never command the brake coils.
        for axis in self.profile['physical']:
            value = self.brake(axis)
            if value not in (0, 1): raise RuntimeError(axis+': invalid brake output readback')
            self.drive_control(axis)
        self.brake_checks = True

    def native_put(self, axis, field, value, expected=None):
        fields = ('-EnaCmd', '-ExeCmd', '-MtnCmd', '-MtnCmdData', '-TgtVelCmd', '-TgtPosCmd')
        if not self.authorized or axis not in self.profile['physical'] or field not in fields:
            raise RuntimeError('unsupported native test write')
        if ((field == '-TgtPosCmd' and self.get(axis, '-AutoExecuteOnTargetPos-RB'))
                or (field == '-ExeCmd' and value == 1)):
            if expected is None: raise ValueError('motion trigger requires an independent expected position')
            self.healthy()
            self.validate_target(axis, expected)
            self.stop_requested = False
        self.touched.add(axis)
        self.client.put(self.prefix+axis+field, value)

    def set_auto_execute(self, axis, enabled):
        number = self.profile['axes'][axis]
        self.text_command(f'Cfg.SetAxisAutoExec({number},{int(enabled)})')
        self.wait_configuration(lambda: self.get(axis, '-AutoExecuteOnTargetPos-RB') == enabled,
                                axis+' target-write mode readback')

    def disable_axis(self, axis):
        self.native_put(axis, '-EnaCmd', 0)
        self.wait_configuration(lambda: self.get(axis, '-EnaAct') == 0
                                and self.get(axis, '-EnaCmd-RB') == 0, axis+' drive disabled')

    @contextmanager
    def native_configuration(self, axis):
        transport = self.open_text_commands()
        saved = None
        try:
            number = self.profile['axes'][axis]
            mode = self.text_command(f'GetAxisAutoExec({number})', query=True)
            fields = {s: self.get(axis, s) for s in ('-MtnCmd', '-MtnCmdData', '-TgtVelCmd', '-TgtPosCmd')}
            saved = (mode, fields)
            self.set_auto_execute(axis, 0)
            self.touched.add(axis)
            self.stop_all()
            self.wait_configuration(self.idle, 'idle before native configuration')
            self.disable_axis(axis)
            self.native_put(axis, '-ExeCmd', 0)
            # A previous virtual move may have left physical trajectories in
            # external mode. Acquire physical ownership without executing a move.
            if self.get(axis, '-TrjSrcTyp-RB') != 0:
                before = self.get(axis, '-PosAct')
                self.native_put(axis, '-EnaCmd', 1)
                self.wait(lambda: self.get(axis, '-EnaAct') == 1
                          and self.get(axis, '-TrjSrcTyp-RB') == 0, axis+' physical ownership')
                self.holds_position(axis, before)
                self.disable_axis(axis)
            yield
        finally:
            errors = []
            if saved is not None:
                self.stop_all()
                for action in (
                    lambda: self.set_auto_execute(axis, 0),
                    lambda: self.wait_configuration(self.idle, 'idle before native settings restoration'),
                    lambda: self.disable_axis(axis),
                    lambda: self.native_put(axis, '-ExeCmd', 0),
                ):
                    try: action()
                    except Exception as error: errors.append(str(error))
                # A target must never be restored while execute-on-write is active.
                try:
                    if self.get(axis, '-AutoExecuteOnTargetPos-RB') != 0:
                        raise RuntimeError('refusing target restoration while execute-on-write remains active')
                    for field, value in saved[1].items(): self.native_put(axis, field, value)
                    self.set_auto_execute(axis, saved[0])
                except Exception as error: errors.append(str(error))
            try: self.close_text_commands(transport)
            except Exception as error: errors.append(str(error))
            if errors: raise RuntimeError('native test cleanup: '+'; '.join(errors))

    def native_move(self, axis, value, expected, command=3, on_write=False):
        self.healthy()
        if not self.idle(): raise RuntimeError('native move requires idle axes')
        if self.get(axis, '-AutoExecuteOnTargetPos-RB') != int(on_write):
            raise RuntimeError('native target-write mode does not match the selected test')
        self.validate_target(axis, expected)
        self.native_put(axis, '-MtnCmd', command)
        self.native_put(axis, '-MtnCmdData', 0)
        self.native_put(axis, '-TgtVelCmd', self.profile['velocity'])
        if not on_write:
            self.native_put(axis, '-ExeCmd', 0)
            self.native_put(axis, '-TgtPosCmd', value)
            self.native_put(axis, '-EnaCmd', 1)
            self.wait(lambda: self.get(axis, '-EnaAct') == 1, axis+' enabled for native execute')
            self.native_put(axis, '-ExeCmd', 1, expected=expected)
        else:
            self.native_put(axis, '-TgtPosCmd', value, expected=expected)
        self.wait(lambda: self.get(axis, '-Busy') == 1 or self.get(axis, '.DMOV') == 0,
                  axis+' native move starts')
        self.finish(axis, expected, None)
        self.sync_motor(axis)

    def sync_motor(self, axis):
        self.client.put(self.prefix+axis+'.SYNC', 1)
        self.wait_configuration(lambda: self.get(axis, '.SYNC') == 0
                                and abs(self.get(axis, '.VAL')-self.get(axis, '.RBV')) <= self.profile['tolerance'],
                                axis+' motor target synchronization')

    def holds_position(self, axis, before, seconds=.25):
        end = time.monotonic()+seconds
        def held():
            if (self.get(axis, '-Busy') or abs(self.get(axis, '-VelAct')) > .005
                    or abs(self.get(axis, '-PosAct')-before) > self.profile['tolerance']):
                raise AssertionError(axis+': configuration/staging unexpectedly caused motion')
            return time.monotonic() >= end
        self.wait(held, axis+' stays stationary during configuration', seconds+2)

    @contextmanager
    def motor_coordinates(self, axis):
        saved = {s: self.get(axis, s) for s in ('.DIR', '.OFF', '.FOFF', '-CfgSyncSftLim',
                                               '-CfgDLLM-RB', '-CfgDHLM-RB', '.DLLM', '.DHLM')}
        self.touched.add(axis)
        try:
            self.client.put(self.prefix+axis+'-CfgSyncSftLim', 0)
            self.wait_configuration(lambda: self.get(axis, '-CfgSyncSftLim') == 0, 'independent native soft limits')
            self.client.put(self.prefix+axis+'.FOFF', 'Frozen')
            yield saved
        finally:
            self.stop_all()
            errors = []
            try: self.wait_configuration(self.idle, 'stopped before restoring coordinates')
            except Exception as error: errors.append(str(error))
            for field in ('.DIR', '.OFF', '.FOFF'):
                try: self.client.put(self.prefix+axis+field, saved[field])
                except Exception as error: errors.append(str(error))
            try: self.sync_motor(axis)
            except Exception as error: errors.append(str(error))
            try:
                self.wait_configuration(lambda: all(abs(self.get(axis, s)-saved[s]) < 1e-6
                    for s in ('-CfgDLLM-RB', '-CfgDHLM-RB', '.DLLM', '.DHLM')), 'original dial/native soft limits')
            except Exception as error: errors.append(str(error))
            try: self.client.put(self.prefix+axis+'-CfgSyncSftLim', saved['-CfgSyncSftLim'])
            except Exception as error: errors.append(str(error))
            if errors: raise RuntimeError('coordinate test cleanup: '+'; '.join(errors))

    def select_motor_coordinates(self, axis, direction, offset):
        if not self.idle(): raise RuntimeError('coordinate changes require idle axes')
        before = self.get(axis, '-PosAct')
        self.client.put(self.prefix+axis+'.DIR', direction)
        self.client.put(self.prefix+axis+'.OFF', offset)
        self.wait_configuration(lambda: self.get(axis, '.DIR') == direction
            and abs(self.get(axis, '.OFF')-offset) < 1e-6
            and abs(self.get(axis, '.RBV')-self.user_position(axis, before)) <= self.profile['tolerance'],
            'user readback reflects DIR and OFF')
        self.holds_position(axis, before)
        self.sync_motor(axis)
