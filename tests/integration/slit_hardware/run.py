#!/usr/bin/env python3
"""Plan or run bounded normal-operation tests on the dedicated real slit IOC."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import signal
import sys
import time
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tests/integration'))
from slit_hardware.cases import GROUPS, make_suite
from slit_hardware.rig import Client, Rig, validate_profile

DEFAULT_PROFILE = Path(__file__).with_name('profile.json')
DEFAULT_REPORT = ROOT/'test-results/slit-hardware/slit-hardware-report.json'


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def record(self, test, status, detail=''):
        if status in ('failed', 'error'): test.rig.stop_all()
        self.records.append({'test': test.id(), 'status': status, 'detail': detail,
                             'seconds': time.monotonic()-self.started, 'snapshot': test.rig.snapshot()})

    def addSuccess(self, test):
        self.record(test, 'passed')
        super().addSuccess(test)

    def addFailure(self, test, error):
        self.record(test, 'failed', self._exc_info_to_string(error, test))
        super().addFailure(test, error)

    def addError(self, test, error):
        self.record(test, 'error', self._exc_info_to_string(error, test))
        super().addError(test, error)


def write_reports(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2)+'\n')
    suite = ET.Element('testsuite', name='ECMC slit hardware', tests=str(len(document['tests'])))
    for item in document['tests']:
        case = ET.SubElement(suite, 'testcase', name=item['test'], time=str(item['seconds']))
        if item['status'] != 'passed':
            ET.SubElement(case, 'failure' if item['status'] == 'failed' else 'error').text = item['detail']
    # Preflight and cleanup failures must also be visible to JUnit consumers.
    for name, detail in [('runner', document.get('error')),
                         ('cleanup', '\n'.join(document['cleanup_errors']))]:
        if detail:
            case = ET.SubElement(suite, 'testcase', name=name, time='0')
            ET.SubElement(case, 'error').text = detail
    suite.set('tests', str(len(suite)))
    suite.set('failures', str(sum(c.find('failure') is not None for c in suite)))
    suite.set('errors', str(sum(c.find('error') is not None for c in suite)))
    ET.ElementTree(suite).write(path.with_suffix('.xml'), encoding='utf-8', xml_declaration=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', help='hardware IOC prefix, normally HWSLIT:')
    parser.add_argument('--profile', type=Path, default=DEFAULT_PROFILE)
    parser.add_argument('--case', choices=GROUPS, action='append', help='repeat to select groups; default: all except homing and limit reconfiguration')
    parser.add_argument('--test', action='append', default=[], help='test-name substring, repeatable')
    parser.add_argument('--run', action='store_true', help='connect and execute selected hardware tests')
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    profile = json.loads(args.profile.read_text())
    validate_profile(profile)
    groups = list(dict.fromkeys(args.case or [g for g in GROUPS if g not in ('homing', 'softlimits')]))
    if 'homing' in groups and len(groups) != 1:
        parser.error('full-stroke homing must run alone with --case homing')
    suite = make_suite(None, groups, args.test)
    if not suite.countTestCases(): parser.error('no matching hardware tests')
    if not args.run:
        for test in suite: print('[hardware] ' + test.id())
        print(json.dumps(profile, indent=2))
        print('Plan only; no EPICS connection or writes. Review physical bounds/scaling before --run.')
        return 0
    if not args.prefix or not args.prefix.endswith(':'):
        parser.error('--prefix ending in : is required with --run')
    from epics import PV
    client = Client(PV)
    rig = Rig(profile, args.prefix, client)
    document = {'utc': datetime.now(timezone.utc).isoformat(), 'prefix': args.prefix,
                'profile': profile, 'tests': [], 'cleanup_errors': []}
    result = None
    def interrupted(_signal, _frame): raise KeyboardInterrupt
    old_handler = signal.signal(signal.SIGTERM, interrupted)
    code = 1
    try:
        rig.homing_session = groups == ['homing']
        rig.guard()
        if groups == ['homing']:
            from slit_hardware.homing import check_homing_support
            check_homing_support(rig)
            rig.homing_session = True
        suite = make_suite(rig, groups, args.test)
        if any('pvt_' in test.id() for test in suite):
            from slit_pvt import check_profile_support
            check_profile_support(client, args.prefix, profile['axes'])
        if any('brake_' in test.id() for test in suite): rig.check_brake_support()
        moving_axes = {axis for test in suite for axis in test.motion_axes}
        # A sleeping absolute encoder may disagree with the unreferenced startup
        # counter. Capture fresh coordinates before calculating any move target.
        if moving_axes: rig.initialize_origins()
        document['origins'] = dict(rig.origins)
        # Validate planned travel before the first motion command. Preparation
        # above may wake/re-reference feedback but never enables a drive.
        rig.preflight_moves(moving_axes)
        # TextTestRunner supplies the wrapped stream required by TextTestResult.
        def factory(*arguments):
            nonlocal result
            result = Result(*arguments)
            return result
        result = unittest.TextTestRunner(verbosity=2, resultclass=factory, failfast=True).run(suite)
        code = 0 if result.wasSuccessful() else 1
    except KeyboardInterrupt:
        document['error'] = 'Interrupted; hardware stop requested'
        code = 130
    except Exception as error:
        document['error'] = str(error)
        print('Hardware tests stopped: ' + str(error), file=sys.stderr)
    finally:
        try:
            document['cleanup_errors'] = rig.cleanup()
            document['final_snapshot'] = rig.snapshot()
            document['trace'] = rig.trace
            if result is not None: document['tests'] = result.records
            write_reports(args.report, document)
        finally:
            client.close()
            signal.signal(signal.SIGTERM, old_handler)
    return 1 if document['cleanup_errors'] else code


if __name__ == '__main__':
    raise SystemExit(main())
