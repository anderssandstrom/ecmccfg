"""Real asyn profile Build/Execute/Readback through the coupled simulation IOC."""
from .base import SlitCase
from slit_pvt import run_profile, run_interrupted_profile, PVTInterruptions


class PVTTests(PVTInterruptions, SlitCase):
    def exercise(self, axis, triggers=False):
        def validate(name, target):
            self.assertGreater(target, self.rig.get(name, '-CfgDLLM-RB'))
            self.assertLess(target, self.rig.get(name, '-CfgDHLM-RB'))
            self.assertLess(abs(target), .7, 'PVT cubic stays within simulation travel')
        run_profile(self.rig, axis, .15, .2, validate, triggers=triggers)

    def interrupt_profile(self, axis, method, phase):
        def validate(name, target):
            self.assertGreater(target, self.rig.get(name, '-CfgDLLM-RB'))
            self.assertLess(target, self.rig.get(name, '-CfgDHLM-RB'))
            self.assertLess(abs(target), .7, 'PVT recovery stays within simulation travel')
        run_interrupted_profile(self.rig, axis, .15, .2, validate, method, phase)

    def test_pvt_lo_round_trip(self): self.exercise('TR_LO')
    def test_pvt_hi_round_trip(self): self.exercise('TR_HI')

    def test_pvt_lo_triggers(self): self.exercise('TR_LO', triggers=True)
    def test_pvt_hi_triggers(self): self.exercise('TR_HI', triggers=True)
