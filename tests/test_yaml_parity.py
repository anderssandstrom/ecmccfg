"""Compare standalone ECB and Python/Jinja configuration generation."""
import copy
from decimal import Decimal
import difflib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts/jinja2'
FIXTURES = ROOT / 'tests/fixtures/yaml_parity'


def commands(text):
    """Keep command order, quoted strings and macros; normalize numeric args."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Only complete numeric arguments, not numbers inside PV names/macros.
        if line.startswith('ecmcConfigOrDie "Cfg.') or re.fullmatch(
                r'epicsEnvSet\(\w+,\s*[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?\s*\)', line):
            line = re.sub(r'(?<=[,(])\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*(?=[,)])',
                          lambda m: format(Decimal(m[1]).normalize(), 'f'), line)
        result.append(line)
    return result


class YamlParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ecb = shutil.which(os.environ.get('ECB', 'ecb'))
        if not cls.ecb:
            raise unittest.SkipTest('ECB is not installed; set ECB to the standalone executable')
        for dependency in ['yaml', 'jinja2', 'cerberus', 'yamllint']:
            if importlib.util.find_spec(dependency) is None:
                raise unittest.SkipTest(f'Missing Python dependency: {dependency}')
        import yaml
        cls.yaml = yaml

    def render(self, source, directory, schema='axis'):
        script, template = {'axis': ('axisYamlJinja2.py', 'axis_main.jinja2'),
                            'encoder': ('encYamlJinja2.py', 'add_encoder.jinja2')}[schema]
        outputs = []
        for name, argv in [
            ('python', [sys.executable, str(SCRIPTS / script), '-D', str(source),
                        '-T', str(SCRIPTS / 'templates'), '-o']),
            ('ecb', [self.ecb, '--yaml', str(source), '--schemafile',
                     str(SCRIPTS / 'ecbSchema.json'), '--schema', schema,
                     '--template', str(SCRIPTS / 'templates' / template),
                     '--templatedir', str(SCRIPTS / 'templates'), '--output']),
        ]:
            output = directory / (name + '.cmd')
            process = subprocess.run(argv + [str(output)], cwd=directory,
                                     capture_output=True, text=True, timeout=30)
            outputs.append((name, process, output.read_text() if output.exists() else ''))
        return outputs

    def compare(self, source, schema='axis'):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = self.render(source, Path(tmp), schema)
            for name, process, output in outputs:
                self.assertEqual(process.returncode, 0, f'{name}: {process.stdout}\n{process.stderr}')
                self.assertTrue(commands(output), f'{name} generated no commands')
            python, ecb = (commands(item[2]) for item in outputs)
            self.assertEqual(python, ecb, '\n'.join(difflib.unified_diff(
                python, ecb, fromfile='Python/Jinja', tofile='ECB', lineterm='')))
            return python

    def test_axis_fixtures(self):
        for source in sorted(FIXTURES.glob('*.yaml')):
            with self.subTest(fixture=source.name):
                self.compare(source)

    def test_psi_csp_example(self):
        self.compare(ROOT / 'examples/PSI/best_practice/motion/stepper_incremental/ex7062_CSP/cfg/axis.yaml')

    def test_defaults_and_explicit_homing(self):
        base = self.yaml.safe_load((FIXTURES / 'virtual_monitoring.yaml').read_text())
        minimal = {key: base[key] for key in ['axis', 'encoder', 'trajectory', 'input']}
        homing = copy.deepcopy(minimal)
        homing['homing'] = dict(type=1, position=0.0, velocity=dict(to=2.0, **{'from': 1.0}),
                                acceleration=5.0, deceleration=6.0, timeout=30)
        for name, document in [('defaults', minimal), ('homing', homing)]:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / 'axis.yaml'
                source.write_text(self.yaml.safe_dump(document))
                generated = self.compare(source)
                self.assertIn('epicsEnvSet(V_DRVL,0)', generated)
                self.assertIn('epicsEnvSet(V_DRVH,0)', generated)

    def test_additional_encoder(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'encoder.yaml'
            source.write_text(self.yaml.safe_dump(dict(encoder=dict(
                type=1, bits=32, absBits=24, numerator=360, denominator=16777216,
                position='ec$(MASTER_ID).s$(ENC_SID).positionActual01'))))
            self.compare(source, 'encoder')

    def test_axis_plc_file_and_inline_code(self):
        document = self.yaml.safe_load((FIXTURES / 'virtual_monitoring.yaml').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            plc = directory / 'axis.plc'
            plc.write_text('\nax$(AX_ID).enc.actpos:=ax1.enc.actpos;\n')
            document['plc'] = dict(enable=True, file=str(plc),
                                   code=['ax$(AX_ID).traj.setpos:=ax1.traj.setpos;'])
            source = directory / 'axis.yaml'
            source.write_text(self.yaml.safe_dump(document))
            generated = self.compare(source)
            expressions = [line for line in generated if 'Cfg.AppendAxisPLCExpr(' in line]
            self.assertEqual(len(expressions), 2)
            self.assertIn('enc.actpos:=ax1.enc.actpos|', expressions[0])
            self.assertIn('traj.setpos:=ax1.traj.setpos|', expressions[1])

    def test_plc_file_comment_policy_difference(self):
        # ECB 1.6.0 retains file comments; Python's readPlcFile strips them.
        document = self.yaml.safe_load((FIXTURES / 'virtual_monitoring.yaml').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            plc = directory / 'comment.plc'
            plc.write_text('# parity comment\nax1.enc.actpos:=0;\n')
            document['plc'] = dict(enable=True, file=str(plc))
            source = directory / 'axis.yaml'
            source.write_text(self.yaml.safe_dump(document))
            outputs = self.render(source, directory)
            for name, process, _ in outputs:
                self.assertEqual(process.returncode, 0, f'{name}: {process.stderr}')
            python, ecb = (commands(item[2]) for item in outputs)
            comment = 'ecmcConfigOrDie "Cfg.AppendAxisPLCExpr(${ECMC_AXIS_NO})=# parity comment"'
            self.assertNotIn(comment, python)
            self.assertEqual(ecb.count(comment), 1)
            self.assertEqual(python, [line for line in ecb if line != comment])

    def test_invalid_configs_rejected_by_both(self):
        base = self.yaml.safe_load((FIXTURES / 'virtual_monitoring.yaml').read_text())
        missing = copy.deepcopy(base)
        del missing['trajectory']
        wrong_type = copy.deepcopy(base)
        wrong_type['trajectory']['axis']['velocity'] = ['not', 'a', 'number']
        for name, document, diagnostic in [('missing-trajectory', missing, 'trajectory'),
                                           ('wrong-type', wrong_type, 'velocity')]:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                source = directory / 'invalid.yaml'
                source.write_text(self.yaml.safe_dump(document))
                for generator, process, _ in self.render(source, directory):
                    self.assertNotEqual(process.returncode, 0, f'{generator} accepted {name}')
                    # An unrelated startup crash must not count as validation.
                    self.assertIn(diagnostic, process.stdout + process.stderr,
                                  f'{generator} failed without identifying the invalid field')

    def test_unknown_key_policy_difference(self):
        # Python deliberately uses purge_unknown=True; ECB rejects typos.
        # Keep this difference visible rather than claiming full validation parity.
        document = self.yaml.safe_load((FIXTURES / 'virtual_monitoring.yaml').read_text())
        document['axis']['misspelledOption'] = True
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / 'unknown.yaml'
            source.write_text(self.yaml.safe_dump(document))
            python, ecb = self.render(source, directory)
            self.assertEqual(python[1].returncode, 0, python[1].stderr)
            self.assertNotEqual(ecb[1].returncode, 0, 'ECB unexpectedly accepted an unknown key')
            self.assertIn('misspelledOption', ecb[1].stdout + ecb[1].stderr)


class CommandComparisonTests(unittest.TestCase):
    def test_equivalent_number_formatting(self):
        self.assertEqual(commands('# comment\n ec mc\n'), ['ec mc'])
        self.assertEqual(commands('ecmcConfigOrDie "Cfg.SetAxisHomeAcc(${AX},20)"'),
                         commands('ecmcConfigOrDie "Cfg.SetAxisHomeAcc(${AX}, 2e1)"'))
        self.assertEqual(commands('epicsEnvSet(ACC,20.0)'), commands('epicsEnvSet(ACC,20)'))

    def test_meaningful_changes_are_not_hidden(self):
        for before, after in [
            ('epicsEnvSet(ACC,20)', 'epicsEnvSet(ACC,21)'),
            ('epicsEnvSet(NAME,"motor (20.0)")', 'epicsEnvSet(NAME,"motor (20)")'),
            ('ecmcConfigOrDie "Cfg.SetAxisHomeAcc(${AX=1},20)"',
             'ecmcConfigOrDie "Cfg.SetAxisHomeAcc(${AX=2},20)"'),
            ('first\nsecond', 'second\nfirst'),
        ]:
            with self.subTest(before=before):
                self.assertNotEqual(commands(before), commands(after))


if __name__ == '__main__':
    unittest.main()
