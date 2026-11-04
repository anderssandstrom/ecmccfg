"""Normal-operation hardware checks; no error injection or limit overruns."""
import time
import unittest


class StatusTests(unittest.TestCase):
    def test_idle_status_and_kinematics(self):
        self.assertTrue(self.rig.healthy())
        self.assertTrue(self.rig.idle())
        self.rig.kinematics()


class MotionTests(unittest.TestCase):
    def round_trip(self, axis):
        origin, step = self.rig.origins[axis], self.rig.profile['step']
        for target in (origin+step, origin-step, origin):
            self.rig.move(axis, target)

    def test_physical_lo_both_directions(self): self.round_trip('TR_LO')
    def test_physical_hi_both_directions(self): self.round_trip('TR_HI')

    def test_repeated_motor_targets(self):
        axis = 'TR_LO'
        origin, step = self.rig.origins[axis], self.rig.profile['step']
        complete = self.rig.start(axis, origin+step)
        for _ in range(3): complete = self.rig.put(axis, '.VAL', origin+step)
        self.rig.finish(axis, origin+step, complete)
        self.rig.move(axis, origin)

    def test_motor_stop_during_move(self):
        axis = 'TR_LO'
        origin, step = self.rig.origins[axis], self.rig.profile['step']
        self.rig.start(axis, origin+step)
        self.rig.wait(lambda: self.rig.get(axis, '-EnaAct') == 1
                      and abs(self.rig.get(axis, '-VelAct')) > min(.005, self.rig.profile['velocity']/10)
                      and abs(self.rig.get(axis, '-PosAct')-origin) > self.rig.profile['tolerance']/2,
                      'physical movement before STOP')
        self.rig.put(axis, '.STOP', 1)
        self.rig.wait(self.rig.idle, 'STOP completes')
        stopped = self.rig.get(axis, '-PosAct')
        self.assertGreater(abs(stopped-origin-step), self.rig.profile['tolerance'],
                           'STOP must halt the move before its destination')
        deadline = time.monotonic()+.5
        while time.monotonic() < deadline:
            self.rig.healthy()
            self.assertTrue(self.rig.idle())
            self.assertAlmostEqual(self.rig.get(axis, '-PosAct'), stopped,
                                   delta=self.rig.profile['tolerance'])
            time.sleep(.02)
        self.rig.move(axis, origin)


class VirtualTests(MotionTests):
    # Load only the two virtual cases through the explicit runner group below.
    def test_center_both_directions(self): self.round_trip('CENTERY')
    def test_gap_both_directions(self): self.round_trip('GAPY')


class EncoderPowerTests(unittest.TestCase):
    def test_real_encoder_sleep_wake_and_backup(self):
        rig = self.rig
        cfg = rig.profile['encoder_power']
        axis, enc = cfg['axis'], cfg['encoder']
        stem = f'-Enc0{enc}'
        self.assertEqual(rig.get(axis, '-EncMode-RB'), 0, 'select Auto power before this group')
        self.assertEqual(rig.get(axis, '-EncForceOn-RB'), 0, 'release Force ON before this group')
        self.assertEqual(rig.get(axis, stem+'-PwrEnable-RB'), 1)
        self.assertEqual(rig.get(axis, stem+'-Absolute'), 1)
        self.assertEqual(rig.get(axis, '-Enc01-Absolute'), 0)
        origin, step = rig.origins[axis], rig.profile['step']
        rig.move(axis, origin+step)
        rig.wait(lambda: rig.get(axis, stem+'-PwrState') == 1
                 and rig.get(axis, '-SetEncIdCmd-RB') == cfg['backup']
                 and rig.get(axis, '-Enc01-Ready') == 1
                 and rig.get(axis, stem+'-PwrOn') == 0,
                 'settled move powers down BiSS and selects tracking encoder', cfg['timeout'])
        complete = rig.start(axis, origin)
        rig.wait(lambda: rig.get(axis, stem+'-PwrState') == 3
                 and rig.get(axis, stem+'-Ready') == 1
                 and rig.get(axis, '-SetEncIdCmd-RB') == enc,
                 'real encoder powers up, becomes ready and is selected', cfg['timeout'])
        rig.finish(axis, origin, complete)


GROUPS = {
    'status': (StatusTests, ('test_idle_status_and_kinematics',)),
    'motion': (MotionTests, ('test_physical_lo_both_directions', 'test_physical_hi_both_directions',
                            'test_repeated_motor_targets', 'test_motor_stop_during_move')),
    'virtual': (VirtualTests, ('test_center_both_directions', 'test_gap_both_directions')),
    'encoder_power': (EncoderPowerTests, ('test_real_encoder_sleep_wake_and_backup',)),
}


def make_suite(rig, groups, patterns=()):
    tests = []
    for group in groups:
        cls, names = GROUPS[group]
        for name in names:
            test = cls(name)
            if patterns and not any(pattern in test.id() for pattern in patterns): continue
            test.motion_axes = {
                'test_physical_lo_both_directions': ('TR_LO',),
                'test_physical_hi_both_directions': ('TR_HI',),
                'test_repeated_motor_targets': ('TR_LO',),
                'test_motor_stop_during_move': ('TR_LO',),
                'test_center_both_directions': ('CENTERY',),
                'test_gap_both_directions': ('GAPY',),
                'test_real_encoder_sleep_wake_and_backup': ('TR_HI',),
            }.get(name, ())
            test.rig = rig
            tests.append(test)
    return unittest.TestSuite(tests)
