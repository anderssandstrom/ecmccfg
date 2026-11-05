"""Probe input edges feed EL7062 PDOs; ECMC computes all TP result records."""
from .probe_axis import ProbeCase


class TouchProbeTests(ProbeCase):
    def sequence(self): return self.rig.get(self.axis, '-Enc01-TP-Seq')

    def capture(self, target, endpoint):
        before = self.sequence()
        self.arm()
        self.rig.plant.configure_probe(target, 1 if endpoint > target else -1)
        self.start(endpoint)
        self.rig.wait(lambda: self.healthy() and self.sequence() == before+1,
                      'one native touch-probe result after the physical input edge', 8)
        event = self.rig.plant.probe_snapshot()['event']
        self.assertIsNotNone(event, 'capture must follow an independently generated input')
        self.assertEqual(self.rig.get(self.axis, '-Enc01-TP-Valid'), 1)
        self.assertEqual(self.rig.get(self.axis, '-Enc01-TP-TimeValid'), 1)
        self.assertEqual(int(self.rig.get(self.axis, '-Enc01-TP-TimeRaw')), event['time_raw'])
        self.assertAlmostEqual(self.rig.get(self.axis, '-Enc01-TP-Pos'), target, delta=.0001)
        self.arrived(endpoint)
        self.rig.assert_stays(lambda: self.healthy() and self.sequence() == before+1
                              and abs(self.rig.get(self.axis, '-Enc01-TP-Pos')-target) < .0001,
                              'latched result retained while the encoder continues moving', .3)

    def test_positive_and_negative_positions_with_rearm(self):
        # These are positive electrical input edges at both motion directions.
        self.capture(.1, .25)
        self.capture(-.1, -.25)

    def test_disarmed_input_does_not_capture(self):
        before = self.sequence()
        self.rig.put(self.axis, '-Enc01-TP-ArmCmd', 0)
        self.rig.plant.configure_probe(.08)
        self.move(.2)
        self.assertTrue(self.rig.plant.probe_snapshot()['triggered'])
        self.assertEqual(self.sequence(), before)
        self.capture(.1, -.1)

    def test_enabled_flag_without_input_is_not_a_capture(self):
        before = self.sequence()
        self.arm()
        self.rig.plant.configure_probe()  # No physical probe edge.
        self.move(.15)
        self.rig.assert_stays(lambda: self.healthy() and self.sequence() == before,
                              'enabled status bit is not a position-stored flag', .3)

    def test_control_enable_is_independent_of_arm(self):
        self.arm()
        before = self.sequence()
        self.rig.put(self.axis, '-Enc01-TP-EnableCmd', 0)
        config = self.rig.profile['probe_axis']
        control = self.rig.prefix + f'SIM:ec0:s{config["slave"]}:touchProbeControl01'
        self.rig.wait(lambda: self.healthy()
                      and self.rig.get(self.axis, '-Enc01-TP-Enable-RB') == 0
                      and self.rig.get(self.axis, '-Enc01-TP-Armed') == 0
                      and self.rig.client.get(control) == 0,
                      'clearing control enable disarms and transmits idle', 3)
        self.rig.put(self.axis, '-Enc01-TP-ArmCmd', 1)
        self.rig.assert_stays(lambda: self.healthy()
                              and self.rig.get(self.axis, '-Enc01-TP-Enable-RB') == 0
                              and self.rig.get(self.axis, '-Enc01-TP-Armed') == 0
                              and self.rig.client.get(control) == 0
                              and self.sequence() == before,
                              'arm cannot bypass disabled probe control', .3)
        self.rig.put(self.axis, '-Enc01-TP-EnableCmd', 1)
        self.rig.wait(lambda: self.rig.get(self.axis, '-Enc01-TP-Enable-RB') == 1
                      and self.rig.get(self.axis, '-Enc01-TP-Armed') == 0,
                      're-enable preserves disarmed state', 3)
        self.capture(.1, .25)
