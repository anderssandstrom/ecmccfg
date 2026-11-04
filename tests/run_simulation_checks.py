#!/usr/bin/env python3
"""Run isolated Python simulator/harness checks; never connect to or start an IOC."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', default='test_*.py', help='test filename glob')
    args = parser.parse_args()
    tests = sorted((ROOT/'tests/simulation').glob(args.pattern))
    if not tests: parser.error('No simulation checks match '+args.pattern)
    failed = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for test in tests:
        print('RUN '+test.name, flush=True)
        if subprocess.run([sys.executable, str(test)], cwd=ROOT, env=env).returncode:
            failed.append(test.name)
    print(f'{len(tests)} simulation checks; {len(failed)} failed.', flush=True)
    if failed: print('Failed: '+', '.join(failed), file=sys.stderr)
    return int(bool(failed))
if __name__ == '__main__':
    raise SystemExit(main())
