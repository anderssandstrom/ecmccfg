"""Repeat physical-axis acceptance cases with slit state management disabled."""
import importlib
import unittest


class IndependentMode:
    def setUp(self):
        super().setUp()
        rig = self.rig
        saved = rig.client.get(rig.prefix + 'SM00-EnaCmd')

        def restore():
            errors = rig.stop_all()
            rig.client.put(rig.prefix + 'SM00-EnaCmd', saved)
            self.assertFalse(errors, 'STOP before restoring state machine: ' + str(errors))

        self.addCleanup(restore)
        # Existing case cleanups must also execute in independent mode.
        # unittest runs cleanups in reverse registration order.
        self._cleanups.insert(0, self._cleanups.pop())
        self.assertEqual(rig.stop_all(), [])
        for axis in rig.profile['physical']:
            rig.wait_drive_disabled(axis)
        rig.client.put(rig.prefix + 'SM00-EnaCmd', 0)
        for axis in rig.profile['physical']:
            rig.put(axis, '-TrjSrcTyp-Cmd', 0)
        rig.wait(lambda: rig.client.get(rig.prefix + 'SM00-EnaCmd') == 0
                 and rig.client.get(rig.prefix + 'SM00-StateCmd') == 0
                 and all(rig.get(a, '-TrjSrcTyp-RB') == 0 for a in rig.profile['physical']),
                 'independent physical axes with state machine disabled', 5)

    def tearDown(self):
        try:
            self.assertEqual(self.rig.client.get(self.rig.prefix + 'SM00-EnaCmd'), 0)
            for axis in self.rig.profile['physical']:
                self.assertEqual(self.rig.get(axis, '-TrjSrcTyp-RB'), 0)
        finally:
            super().tearDown()


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    excluded = {'test_native_center_and_gap_commands',
                'test_both_brakes_release_for_coordinated_motion'}
    for module, name in (('enable', 'EnableTests'), ('feedback', 'FeedbackTests'),
                         ('motor', 'MotorTests'), ('native', 'NativeTests'),
                         ('brake', 'BrakeTests'), ('target_write', 'TargetWriteTests'),
                         ('stall', 'StallTests')):
        original = getattr(importlib.import_module('slit.cases.' + module), name)
        independent = type('Independent' + name, (IndependentMode, original),
                           {'__module__': __name__})
        for method in loader.getTestCaseNames(original):
            if method not in excluded:
                suite.addTest(independent(method))
    return unittest.TestSuite([suite])
