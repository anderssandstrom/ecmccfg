"""Offline PVT geometry and IOC configuration checks; never access an IOC."""
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests/integration'))
from slit_pvt import check_profile_support, profile_geometry, run_profile


class PVTChecks(unittest.TestCase):
    def test_cubic_extrema_and_speed_match_independent_hermite_sampling(self):
        for origin, amplitude, speed in ((0., .15, .2), (35., 2.5, 1.)):
            plan = profile_geometry(origin, amplitude, speed, 1.)
            pts, dt = plan['positions'], plan['interval']
            slopes = [(pts[i+1]-pts[i])/dt for i in range(len(pts)-1)]
            tangent = [slopes[0]]+[(slopes[i-1]+slopes[i])/2 for i in range(1,len(pts)-1)]+[slopes[-1]]
            samples, velocities = [], []
            for i in range(len(pts)-1):
                for step in range(1001):
                    u = step/1000
                    p, q, v, w = pts[i], pts[i+1], tangent[i], tangent[i+1]
                    samples.append((2*u**3-3*u*u+1)*p+(u**3-2*u*u+u)*dt*v
                                   +(-2*u**3+3*u*u)*q+(u**3-u*u)*dt*w)
                    velocities.append(((6*u*u-6*u)*p+(-6*u*u+6*u)*q)/dt
                                      +(3*u*u-4*u+1)*v+(3*u*u-2*u)*w)
            self.assertGreater(max(plan['extrema']), origin+amplitude)
            self.assertLess(min(plan['extrema']), origin-amplitude)
            self.assertGreaterEqual(max(plan['extrema'])+1e-10, max(samples))
            self.assertLessEqual(min(plan['extrema'])-1e-10, min(samples))
            self.assertLessEqual(max(map(abs,velocities)), speed*(1+1e-9))
            self.assertLessEqual(plan['peak_acceleration'], 1.)
            self.assertEqual(pts[:2], [origin, origin])
            self.assertEqual(pts[-2:], [origin, origin])

    def test_overshoot_is_rejected_before_profile_writes(self):
        writes = []
        rig = SimpleNamespace(profile={'axes': {'TR_LO': 5}}, prefix='HW:',
            get=lambda axis, field: 1. if field == '.ACCS' else 0.,
            client=SimpleNamespace(put=lambda *args, **kwargs: writes.append(args)))
        def validate(axis, value):
            if abs(value) > 1.001: raise AssertionError('cubic overshoot outside envelope')
        with self.assertRaisesRegex(AssertionError, 'overshoot'):
            run_profile(rig, 'TR_LO', 1., 1., validate)
        self.assertEqual(writes, [])

    def test_bad_geometry_is_rejected(self):
        for values in ((0,0,1,1), (0,1,-1,1), (math.inf,1,1,1), (0,1,1,0)):
            with self.assertRaises(ValueError): profile_geometry(*values)

    def test_missing_profile_support_is_actionable_and_read_only(self):
        reads = []
        def get(name):
            reads.append(name)
            raise RuntimeError('PV missing')
        with self.assertRaisesRegex(RuntimeError, 'restart the IOC'):
            check_profile_support(SimpleNamespace(get=get), 'SIM:', ['TR_LO'])
        self.assertEqual(reads, ['SIM:PVT-MaxSize'])

    def test_trigger_record_has_forward_link_and_only_one_timestamp_field(self):
        source = (ROOT/'db/core/ecmcPVTTrigger.template').read_text()
        self.assertIn('field(FLNK, "$(FLNK=)")', source)
        self.assertEqual(source.count('field(TSE,'), 1)

    def test_both_iocs_reserve_spare_el2008_trigger_channel(self):
        for fixture in ('ioc', 'ioc_hardware'):
            source = (ROOT/'tests/integration/slit'/fixture/'startup.cmd').read_text()
            self.assertIn('epicsEnvSet(TRG_EC_ENTRY,"ec0.s5.binaryOutput05.0")', source)
            self.assertIn('epicsEnvSet(TRG_DUR_S,"0.4")', source)

    def test_both_iocs_use_yaml_pvt_buffers_for_all_axes(self):
        import yaml
        for fixture in ('ioc','ioc_hardware'):
            files = list((ROOT/'tests/integration/slit'/fixture/'cfg').glob('axis_*.yaml'))
            documents = [yaml.safe_load(source.read_text()) for source in files]
            motors = [doc['epics']['motorRecord'] for doc in documents
                      if doc['epics']['motorRecord'].get('enable', True)]
            self.assertEqual(len(motors), 4)
            for motor in motors:
                self.assertEqual(motor['pvt'], {'npoints':64,'nreadback':256})


if __name__ == '__main__': unittest.main()
