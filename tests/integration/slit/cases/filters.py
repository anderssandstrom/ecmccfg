"""Native encoder filter configuration, observable smoothing and bypass controls."""
import math
from .settings import SettingsCase


class FilterTests(SettingsCase):
    def setUp(self):
        super().setUp()
        self.encoder(2)
        # Save the flag before a position-window resize implicitly enables it.
        self.saved['EncPosFilterEnable'] = self.query('EncPosFilterEnable')

    def test_velocity_filter_settings(self):
        for size in (1, 25, 100):
            self.config('EncVelFilterSize', size)
            for enabled in (0, 1): self.config('EncVelFilterEnable', enabled)

    def test_position_filter_settings(self):
        for size in (1, 10, 100):
            self.config('EncPosFilterSize', size)
            for enabled in (0, 1): self.config('EncPosFilterEnable', enabled)

    def position(self):
        return self.rig.get(self.axis, '-Enc02-PosAct')

    def test_position_filter_smooths_a_step_then_bypasses(self):
        self.closed()
        origin = self.position()
        mechanics = self.rig.plant.physical_position(self.axis)
        self.config('EncPosFilterSize', 400)
        self.config('EncPosFilterEnable', 1)
        self.rig.assert_stays(lambda: self.healthy() and abs(self.position()-origin) < .001,
                              'position window filled with steady samples', .6)
        self.rig.plant.inject(self.axis, encoder_bias_mm=.012)
        self.rig.wait(lambda: self.healthy() and .001 < self.position()-origin < .010,
                      'filtered position traverses intermediate values after a raw step', 2)
        self.rig.wait(lambda: abs(self.position()-origin-.012) < .001,
                      'filtered position reaches the injected step', 3)
        self.config('EncPosFilterEnable', 0)
        self.rig.plant.inject(self.axis, encoder_bias_mm=-.012)
        self.rig.wait(lambda: abs(self.position()-origin+.012) < .001,
                      'bypass follows negative raw step', 2)
        self.rig.assert_stays(lambda: self.healthy() and abs(self.position()-origin+.012) < .001,
                              'bypass retains the complete step', .2)
        self.assertAlmostEqual(self.rig.plant.physical_position(self.axis), mechanics, delta=.0005)

    def test_velocity_filter_attenuates_noise_and_bypass_restores_it(self):
        self.closed()
        self.config('EncPosFilterEnable', 0)
        self.config('EncVelFilterSize', 400)
        self.config('EncVelFilterEnable', 0)
        mechanics = self.rig.plant.physical_position(self.axis)
        self.rig.plant.inject(self.axis, encoder_noise_mm=.002)
        def rms():
            rows = self.observe({'velocity': lambda: self.rig.get(self.axis, '-Enc02-VelAct'),
                                 'position': self.position}, seconds=1.5, minimum=20)
            self.assertGreater(max(r['position'] for r in rows)-min(r['position'] for r in rows), .001,
                               'model must publish real position noise')
            return math.sqrt(sum(r['velocity']**2 for r in rows)/len(rows))
        unfiltered = rms()
        self.assertGreater(unfiltered, .02, 'noise must excite the unfiltered velocity')
        self.config('EncVelFilterEnable', 1)
        self.rig.assert_stays(lambda: self.healthy(), 'velocity window warm-up', .6)
        filtered = rms()
        self.assertLess(filtered, .65*unfiltered, 'velocity filter must attenuate measured noise')
        self.config('EncVelFilterEnable', 0)
        bypass = rms()
        self.assertGreater(bypass, 1.5*filtered, 'bypass must restore velocity noise')
        self.assertAlmostEqual(self.rig.plant.physical_position(self.axis), mechanics, delta=.0005)
        self.rig.trace.append({'action': 'encoder velocity filter noise comparison',
                              'rms_unfiltered': unfiltered, 'rms_filtered': filtered, 'rms_bypass': bypass})
