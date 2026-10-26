#!/usr/bin/env python3
"""Run hardware-free configuration regressions from any working directory."""
import argparse
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--strict', action='store_true',
                        help='fail if any test is skipped (used by CI)')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    suite = unittest.TestSuite()
    for directory in (ROOT / 'tests', ROOT / 'scripts/startup_validator/tests'):
        discovered = unittest.TestLoader().discover(str(directory), pattern='test_*.py')
        if not discovered.countTestCases():
            parser.error(f'No tests found in {directory}')
        suite.addTests(discovered)
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1).run(suite)
    if args.strict and result.skipped:
        print('Strict mode: skipped checks count as a failure. Install EPICS Base '
              '(msi, softIoc, libCom) and Qt uic; see tests/README.md.', file=sys.stderr)
    return int(not result.wasSuccessful() or (args.strict and bool(result.skipped)))


if __name__ == '__main__':
    sys.exit(main())
