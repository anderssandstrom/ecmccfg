from .base import SlitCase
from slit_recovery import CoupledStopCases, stall_alarm, stop_blade_during_virtual


class CoupledStopTests(CoupledStopCases, SlitCase):
    def exercise_coupled_stop(self, master, blade, interface):
        def validate(name, target): self.assertLess(abs(target), .8)
        stop_blade_during_virtual(self.rig, master, blade, interface, .6, validate)
