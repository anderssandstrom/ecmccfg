from .base import SlitCase
from slit_recovery import StallCases, stall_alarm, stop_blade_during_virtual


class StallTests(StallCases, SlitCase):
    def exercise_stall(self, axis, trigger):
        def validate(name, target): self.assertLess(abs(target), .7)
        stall_alarm(self.rig, axis, trigger, .2, .4, validate)
