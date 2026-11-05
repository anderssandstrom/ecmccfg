"""Common preparation for the auxiliary DS402 axis (no motor record)."""
from .base import SlitCase


class ProbeCase(SlitCase):
    def setUp(self):
        super().setUp()
        config = self.rig.profile.get('probe_axis')
        if not config:
            self.skipTest('requires the schema-4 EL7062 DS402 probe fixture')
        self.axis = config['name']
        self.addCleanup(self.clean_probe)
        self.rig.plant.configure_probe()
        self.rig.put(self.axis, '-RstCmd', 1)
        self.rig.wait(lambda: self.rig.get(self.axis, '-ErrId') == 0
                      and self.rig.get(self.axis, '-InStartup') == 0,
                      'independent DS402 axis ready', 5)
        if abs(self.rig.get(self.axis, '-PosAct')) > .001:
            self.move(0)

    def clean_probe(self):
        self.rig.plant.configure_probe()
        errors = self.rig.stop_all()
        self.assertFalse(errors, 'probe cleanup: ' + str(errors))

    def healthy(self):
        self.rig.check_native_error(self.axis)
        self.assertLess(abs(self.rig.plant.probe_snapshot()['position_mm']), .8)
        for axis in self.rig.names:
            self.rig.check_native_error(axis)
        return True

    def start(self, target, velocity=.1):
        self.rig.stage_native(self.axis, 3, target, velocity)
        self.rig.execute_native(self.axis)

    def arrived(self, target):
        self.rig.wait(lambda: self.healthy() and self.rig.get(self.axis, '-Busy') == 0
                      and abs(self.rig.get(self.axis, '-PosAct')-target) < .003
                      and abs(self.rig.plant.probe_snapshot()['position_mm']-target) < .003,
                      'DS402 reaches independent measured endpoint', 10)

    def move(self, target):
        self.start(target)
        self.arrived(target)

    def arm(self):
        self.rig.put(self.axis, '-Enc01-TP-ArmCmd', 0)
        base = self.rig.prefix + 'SIM:ec0:s20:'
        self.rig.wait(lambda: int(self.rig.client.get(base+'touchProbeStatus01-RB')) == 0,
                      'probe stored flags cleared before rearming', 3)
        self.rig.put(self.axis, '-Enc01-TP-ArmCmd', 1)
        self.rig.wait(lambda: self.rig.get(self.axis, '-Enc01-TP-Armed') == 1
                      and int(self.rig.client.get(base+'touchProbeStatus01-RB')) == 1,
                      'DS402 probe enabled without a stored edge', 3)
