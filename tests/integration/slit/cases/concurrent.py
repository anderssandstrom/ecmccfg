from .base import SlitCase
from slit_recovery import concurrent_physical_moves


class ConcurrentTests(SlitCase):
    def exercise(self, primary, secondary):
        def validate(name, value): self.assertLess(abs(value), .8)
        concurrent_physical_moves(self.rig, primary, secondary, .6, .4, validate)

    def test_lo_moves_while_hi_is_nudged(self): self.exercise('TR_LO', 'TR_HI')
    def test_hi_moves_while_lo_is_nudged(self): self.exercise('TR_HI', 'TR_LO')
