"""DS402 probe-1 single-shot latch, independent of ECMC's result records.

Models enable (bit 0), positive-edge capture (bit 4), negative-edge capture
(bit 5), and stored flags (status bits 1/2). Timestamps are raw U32 words.
Continuous capture and probe 2 are deliberately outside this model's scope.
"""
from dataclasses import dataclass
from el7041 import word16


@dataclass(frozen=True)
class Feedback:
    status: int
    positive: int
    negative: int
    positive_time: int
    negative_time: int


class Model:
    def __init__(self):
        self.enabled = False
        self.level = False
        self.positive = self.negative = 0
        self.positive_time = self.negative_time = 0
        self.positive_stored = self.negative_stored = False

    def step(self, control, level, position, timestamp):
        control = word16(control)
        if control & 2:
            raise ValueError('continuous probe capture is not modeled')
        for value in (position, timestamp):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError('probe words must be integers')
        if not 0 <= timestamp < 1 << 64:
            raise ValueError('probe timestamp must be a U64 clock value')
        enabled = bool(control & 1)
        if not enabled or not self.enabled:
            self.positive_stored = self.negative_stored = False
        # Enabling while the physical input is already high is not an edge.
        if enabled and self.enabled:
            if level and not self.level and control & 16 and not self.positive_stored:
                self.positive = position & 0xffffffff
                self.positive_time = timestamp & 0xffffffff
                self.positive_stored = True
            if self.level and not level and control & 32 and not self.negative_stored:
                self.negative = position & 0xffffffff
                self.negative_time = timestamp & 0xffffffff
                self.negative_stored = True
        self.enabled, self.level = enabled, bool(level)
        return Feedback(int(enabled) | (int(self.positive_stored) << 1) |
                        (int(self.negative_stored) << 2), self.positive, self.negative,
                        self.positive_time, self.negative_time)
