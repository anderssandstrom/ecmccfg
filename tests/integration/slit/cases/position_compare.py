"""Native position compare waits safely without a SIM sample-clock provider."""
from .probe_axis import ProbeCase


class PositionCompareTests(ProbeCase):
    def test_missing_sample_clock_waits_without_writing_outputs_and_cancels(self):
        if self.rig.profile['probe_axis']['sample_clock']:
            self.skipTest('negative control applies to SIM without a sample clock')
        base = self.rig.prefix + 'SIM:ec0:s21:'
        fields = ('binaryOutput01', 'activate', 'startTime')
        before = {key: self.rig.client.get(base+key) for key in fields}
        sequence = self.rig.get(self.axis, '-PC-Seq')
        for suffix, value in (('-PC-TargetCmd', .1), ('-PC-DirCmd', 1),
                              ('-PC-OutputCmd', 1), ('-PC-ArmCmd', 1)):
            self.rig.put(self.axis, suffix, value)
        self.rig.wait(lambda: self.rig.get(self.axis, '-PC-State') == 1,
                      'compare armed while waiting for timing', 3)
        self.start(.25)
        self.rig.assert_stays(lambda: self.healthy() and self.rig.get(self.axis, '-PC-State') == 1
                              and all(self.rig.client.get(base+key) == before[key] for key in fields)
                              and self.rig.get(self.axis, '-PC-Seq') == sequence,
                              'missing clock must not schedule an output or claim a fired event', 1)
        self.rig.put(self.axis, '-PC-CancelCmd', 1)
        self.rig.wait(lambda: self.rig.get(self.axis, '-PC-State') == 0,
                      'cancel clears a request waiting for timing', 3)
        self.arrived(.25)
        self.rig.assert_stays(lambda: self.healthy()
                              and all(self.rig.client.get(base+key) == before[key] for key in fields),
                              'cancelled compare must not write output after motion completes', .3)
