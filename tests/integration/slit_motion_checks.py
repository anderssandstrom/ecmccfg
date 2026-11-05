"""Shared measured-position checks for isolated and coordinated slit motion."""
from contextlib import contextmanager
import math


class MotionExpectation:
    def __init__(self, rig, axis):
        if axis not in ('TR_LO', 'TR_HI', 'CENTERY', 'GAPY'):
            raise ValueError('unknown slit axis: '+axis)
        self.rig, self.axis = rig, axis
        self.tolerance = rig.profile.get('tolerance', .015)
        self.before = self.positions()
        self.center = (self.before['TR_LO']+self.before['TR_HI'])/2
        self.gap = self.before['TR_HI']-self.before['TR_LO']

    def positions(self):
        values = {a: self.rig.get(a, '-PosAct') for a in ('TR_LO', 'TR_HI')}
        if not all(math.isfinite(v) for v in values.values()):
            raise AssertionError('non-finite blade position during isolation check')
        return values

    def check(self):
        positions = self.positions()
        if self.axis in positions:
            other = 'TR_HI' if self.axis == 'TR_LO' else 'TR_LO'
            if abs(positions[other]-self.before[other]) > self.tolerance:
                raise AssertionError(other+': uncommanded physical axis moved during '+self.axis+' motion')
        elif self.axis == 'CENTERY':
            if abs(positions['TR_HI']-positions['TR_LO']-self.gap) > 2*self.tolerance:
                raise AssertionError('center move changed the uncommanded gap')
        else:
            if abs((positions['TR_LO']+positions['TR_HI'])/2-self.center) > self.tolerance:
                raise AssertionError('gap move changed the uncommanded center')
        return positions

    def finish(self, target):
        positions = self.check()
        if self.axis in positions:
            expected = dict(self.before, **{self.axis: target})
        elif self.axis == 'CENTERY':
            expected = {'TR_LO': target-self.gap/2, 'TR_HI': target+self.gap/2}
        else:
            expected = {'TR_LO': self.center-target/2, 'TR_HI': self.center+target/2}
        for axis, value in expected.items():
            if abs(positions[axis]-value) > self.tolerance:
                raise AssertionError(f'{axis}: measured {positions[axis]} differs from expected blade endpoint {value}')
        return expected


@contextmanager
def observe_motion(rig, axis, target=None):
    previous = getattr(rig, 'motion_expectation', None)
    expectation = MotionExpectation(rig, axis)
    rig.motion_expectation = expectation
    try:
        yield expectation
        if target is not None: expectation.finish(target)
    finally:
        rig.motion_expectation = previous
