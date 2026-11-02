"""Post-home enable/target contract through Python/Cerberus/Jinja and ECB."""
import copy
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


class HomingPostMoveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in ('yaml', 'jinja2', 'cerberus', 'yamllint'):
            if importlib.util.find_spec(name) is None:
                raise unittest.SkipTest('missing parser test dependency: ' + name)
        import yaml
        from jinja2 import Environment
        sys.path.insert(0, str(SCRIPTS))
        from ecmcConfigValidator import ConfigValidator
        cls.yaml, cls.Environment, cls.ConfigValidator = yaml, Environment, ConfigValidator
        cls.base = yaml.safe_load((ROOT / 'tests/fixtures/yaml_parity/virtual_monitoring.yaml').read_text())
        cls.ecb = shutil.which(os.environ.get('ECB', 'ecb'))

    def source_template(self, nested):
        if not nested:
            return (SCRIPTS / 'templates/homing.jinja2').read_text()
        source = (SCRIPTS / 'templates/encoder.jinja2').read_text()
        start = source.index('{%- if encoder.homing is defined %}')
        end = source.index('{%- if encoder.lookuptable is defined %}', start)
        return source[start:end]

    def python_render(self, document, template):
        validator = self.ConfigValidator()
        validator.document = document
        normalized = validator.validate_axis(strict=True)
        return self.Environment().from_string(template).render(**normalized)

    def ecb_render(self, document, template):
        with tempfile.TemporaryDirectory(prefix='ecmc-post-home-') as tmp:
            path = Path(tmp)
            source, renderer, result = path/'axis.yaml', path/'home.jinja2', path/'home.cmd'
            source.write_text(self.yaml.safe_dump(document))
            renderer.write_text(template)
            process = subprocess.run([self.ecb, '--yaml', str(source), '--schemafile',
                str(SCRIPTS/'ecbSchema.json'), '--schema', 'axis', '--template', str(renderer),
                '--templatedir', str(path), '--output', str(result)], capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stdout+'\n'+process.stderr)
            return result.read_text()

    def check_cases(self, ecb=False):
        for nested in (False, True):
            for enabled in (False, True):
                for target in (None, 0.0, .125, '$(HOME_POST=0.125)'):
                    with self.subTest(nested=nested, enabled=enabled, target=target):
                        document = copy.deepcopy(self.base)
                        home = {'postMoveEnable': enabled}
                        if target is not None: home['postMovePosition'] = target
                        if nested: document['encoder']['homing'] = home
                        else: document['homing'] = home
                        template = self.source_template(nested)
                        output = self.ecb_render(document, template) if ecb else self.python_render(document, template)
                        if enabled and target is None:
                            self.assertIn('ecmcExit', output)
                            self.assertIn('postMovePosition is required', output)
                            self.assertNotIn('Cfg.SetAxisHomePostMoveEnable(', output)
                            self.assertNotIn('Cfg.SetAxisHomePostMoveTargetPosition(', output)
                        else:
                            self.assertNotIn('ecmcExit', output)
                            self.assertIn(f'Cfg.SetAxisHomePostMoveEnable(${{ECMC_AXIS_NO}},{int(enabled)})', output)
                            self.assertEqual('Cfg.SetAxisHomePostMoveTargetPosition(' in output, target is not None)
                            if isinstance(target, str): self.assertIn(target, output)
                            if ecb:
                                python = self.python_render(copy.deepcopy(document), template)
                                def post_lines(text):
                                    return [re.sub(r'\s+', '', line) for line in text.splitlines()
                                            if 'SetAxisHomePostMove' in line or 'epicsEnvSet(POST_' in line]
                                self.assertEqual(post_lines(output), post_lines(python))

    def test_python_homing_post_move(self):
        self.check_cases()

    def test_ecb_homing_post_move(self):
        if self.ecb is None: self.skipTest('ECB executable not installed; set ECB to test parity')
        self.check_cases(ecb=True)


if __name__ == '__main__':
    unittest.main()
