"""Independent DS402 axis and a position-triggered probe input for the SIM IOC."""
import math
import time
import ds402
import touch_probe


class ProbeAxis:
    def __init__(self, config, prefix, factory, timeout):
        self.config, self.timeout = config, timeout
        self.io = ds402.EpicsIO(prefix, 0, config['slave'], '01', timeout, factory)
        self.io.mode = 'csv'
        self.pvs, self.owned = {}, []
        self.probe = touch_probe.Model()
        self.trigger = None
        self.triggered = False
        self.event = None
        self.model = None
        try:
            self.io.connect()
            initial = self.io.pvs['initial'].get(use_monitor=False, timeout=timeout)
            initial = ds402.signed32(initial)
            scale = config['counts_per_mm']
            self.model = ds402.Model(ds402.Settings(encoder_counts_per_rev=scale,
                                velocity_units_per_rev_per_second=scale), initial)
            for key, field, kind in (
                ('control', 'touchProbeControl01', 'mbbiDirect'),
                ('status', 'touchProbeStatus01', 'mbboDirect'),
                ('positive', 'touchProbePositionPos01_1', 'mbboDirect'),
                ('negative', 'touchProbePositionNeg01_1', 'mbboDirect'),
                ('positive_time', 'touchProbeTimestampPos01_1', 'mbboDirect'),
                ('negative_time', 'touchProbeTimestampNeg01_1', 'mbboDirect')):
                pv = factory(f'{prefix}ec0:s{config["slave"]}:{field}', auto_monitor=False)
                record = factory(pv.pvname + '.RTYP', auto_monitor=False)
                self.owned.extend((pv, record))
                if not pv.wait_for_connection(timeout=timeout) or not record.wait_for_connection(timeout=timeout):
                    raise RuntimeError('cannot connect to ' + pv.pvname)
                if record.get(as_string=True, use_monitor=False, timeout=timeout) != kind:
                    raise RuntimeError(pv.pvname + ': expected ' + kind)
                if not (pv.read_access if key == 'control' else pv.write_access):
                    raise RuntimeError('missing access: ' + pv.pvname)
                self.pvs[key] = pv
        except Exception:
            self.close()
            raise

    def configure(self, position=None, direction=1):
        if position is not None and (not math.isfinite(position) or abs(position) >= .7):
            raise ValueError('probe trigger must lie inside the SIM travel bound')
        if direction not in (-1, 1):
            raise ValueError('probe direction must be -1 or 1')
        self.trigger = None if position is None else (position*self.config['counts_per_mm'], direction)
        self.triggered = False
        self.event = None

    def read(self):
        return (*self.io.read(), self.pvs['control'].get(use_monitor=False, timeout=self.timeout))

    def step(self, commands, seconds):
        before = self.model.position_counts
        drive = self.model.step(*commands[:2], seconds)
        after = self.model.position_counts
        scale = self.config['counts_per_mm']
        if abs(after / scale) >= .8:
            raise RuntimeError('DS402 probe axis exceeded SIM travel bound')
        position, stamp, level = math.floor(after), time.monotonic_ns(), False
        if self.trigger is not None and not self.triggered:
            target, direction = self.trigger
            if direction*(target-before) >= 0 and direction*(after-target) >= 0 and after != before:
                position = round(target)
                level = self.triggered = True
                self.event = {'position_mm': position/scale, 'raw': position & 0xffffffff,
                              'time_raw': stamp & 0xffffffff}
        # Input pulses, not result PVs, generate the probe's independent latch.
        probe = self.probe.step(commands[2], level, position, stamp)
        return drive, probe

    def publish(self, feedback):
        drive, probe = feedback
        self.io.publish(drive)
        # Publish payload before asserting the stored flag; retain each capture
        # until ECMC disarms it. CA writes are not an atomic PDO transaction.
        for key in ('positive', 'negative', 'positive_time', 'negative_time', 'status'):
            pv = self.pvs[key]
            if not pv.connected or pv.put(getattr(probe, key), wait=True, timeout=self.timeout) != 1:
                raise RuntimeError('probe feedback write failed: ' + pv.pvname)

    def snapshot(self):
        return {'position_mm': self.model.position_counts/self.config['counts_per_mm'],
                'drive_state': self.model.state, 'triggered': self.triggered,
                'event': self.event.copy() if self.event else None}

    def close(self):
        if self.model is not None:
            self.model.trip()
            self.io.withdraw(self.model.feedback())
        self.io.close()
        for pv in self.owned: pv.disconnect()
