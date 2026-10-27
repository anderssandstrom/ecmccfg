"""N6 OPT mapping, database and option-aware panel checks; no hardware access."""
from pathlib import Path
from itertools import product
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from n6_support import ROOT, hardware_commands
from test_ex72xx_opt import InvalidConfiguration, expand

DB = ROOT / 'db/Nanotec'


def expanded_database(startup):
    msi = shutil.which('msi')
    if not msi:
        raise unittest.SkipTest('EPICS msi is not installed')
    common = dict(ECMC_P='TEST:', PORT='ECMC', ADDR='0', TIMEOUT='1', MASTER_ID='0',
                  SLAVE_POS='3', HWTYPE=startup.env['ECMC_EC_HWTYPE'], T_SMP_MS='1000', TSE='-2')
    include = [msi, '-I', str(DB), '-I', str(ROOT / 'db/generic'),
               '-I', str(ROOT / 'db/Beckhoff_7XXX')]
    outputs = []
    jobs = [('subs', f"ecmc{startup.env['ECMC_SUBST_TYPE']}.substitutions", {})]
    jobs += [('template', name, macros) for name, macros in startup.templates]
    for kind, name, macros in jobs:
        args = include + ['-M', ','.join(f'{key}={value}' for key, value in (common | macros).items())]
        path = next(path for path in [DB / name, ROOT / 'db/generic' / name] if path.exists())
        args += ['-S', str(path)] if kind == 'subs' else [str(path)]
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        if result.stderr:
            raise AssertionError(result.stderr)
        outputs.append(result.stdout)
    return '\n'.join(outputs)


class N6OptTests(unittest.TestCase):
    def test_default_process_image_matches_legacy(self):
        baseline = hardware_commands('N6-1-1-1-S')
        optional = hardware_commands()
        self.assertEqual(optional.entries(), baseline.entries())
        self.assertEqual(optional.env['ECMC_EC_COMP_TYPE'], 'N6')
        self.assertEqual(optional.env['ECMC_N6_M0_S3_RAW_POS'], '0')
        self.assertEqual(optional.env['ECMC_HW_PANEL'], 'N6-1-1-1-S_OPT')

    def test_raw_option_is_independent_and_does_not_leak(self):
        enabled = hardware_commands(options={'RAW_POS': '1'})
        self.assertIn('positionActualScaled01', enabled.entries())
        self.assertEqual(enabled.entries()['positionActual01'][0][3], 0x6063)
        self.assertEqual(enabled.env['ECMC_N6_M0_S3_RAW_POS'], '1')
        disabled = hardware_commands(slave=7, master=1)
        self.assertNotIn('positionActualScaled01', disabled.entries())
        self.assertEqual(disabled.env['ECMC_N6_M1_S7_RAW_POS'], '0')
        self.assertFalse(any(key.startswith('N6_OPT_') for key in enabled.env))
        for value in ['2', '-1', 'yes', '1.0', '']:
            with self.subTest(value=value), self.assertRaises(InvalidConfiguration):
                hardware_commands(options={'RAW_POS': value})

    def test_homing_pdos_are_optional_and_preserve_csv(self):
        for raw in ['0', '1']:
            baseline = hardware_commands(options={'RAW_POS': raw})
            enabled = hardware_commands(options={'RAW_POS': raw, 'HOMING': '1'})
            entries = enabled.entries()
            self.assertEqual(set(entries) - set(baseline.entries()),
                             {'homingMethod01', 'homeOffset01'})
            for name, mapping in baseline.entries().items():
                self.assertEqual(entries[name], mapping)
            self.assertEqual(entries['homingMethod01'], ((1, 2, 0x1603, 0x6098, 0), 'S8'))
            self.assertEqual(entries['homeOffset01'], ((1, 2, 0x1603, 0x607c, 0), 'S32'))
            self.assertEqual({m[0][2] for m in entries.values() if m[0][0] == 1},
                             {0x1600, 0x1602, 0x1603})
            alias = 'Cfg.EcAddDataDT(ec0.s3.driveControl01,0,4,1,B1,driveCmdExe01)'
            self.assertIn(alias, enabled.commands)
            parent = next(c for c in enabled.commands if c.startswith('Cfg.EcAddEntryDT(')
                          and c.endswith(',driveControl01)'))
            self.assertLess(enabled.commands.index(parent), enabled.commands.index(alias))
            self.assertIn('Cfg.WriteEcEntryIDString(3,driveCmdExe01,0)', enabled.commands)
            self.assertFalse(any('driveCmdExe01' in c for c in baseline.commands))
            self.assertIn('Cfg.WriteEcEntryIDString(3,homingMethod01,35)', enabled.commands)
            self.assertIn('Cfg.WriteEcEntryIDString(3,homeOffset01,0)', enabled.commands)
            mode_writes = [c for c in enabled.commands if ',modeControl01,' in c]
            self.assertEqual(mode_writes, ['Cfg.WriteEcEntryIDString(3,modeControl01,9)'])
            self.assertFalse(any(',driveControl01,' in c for c in enabled.commands))
            database = expanded_database(enabled)
            sources = set(re.findall(r'/ec0\.s3\.(\w+)[?=]', database))
            self.assertLessEqual(sources, entries.keys())
            names = re.findall(r'record\(\w+,\s*"([^"]+)"', database)
            self.assertEqual(len(names), len(set(names)))
            for suffix in ['HomeMethod', 'HomeOffset', 'ModeCmd']:
                name = 'TEST:Drv01-' + suffix
                body = re.search(r'record\(ao,\s*"' + name + r'"\)\s*\{(.*?)\n\}', database, re.S)[1]
                self.assertRegex(body, r'field\(PINI,\s*"0"\)')
                self.assertIn(name + '-RB', names)
            self.assertIn('TEST:Drv01-ModeAct', names)
            self.assertEqual(enabled.env['ECMC_N6_M0_S3_HOMING'], '1')
            self.assertFalse(any(key.startswith('N6_OPT_') for key in enabled.env))
        for value in ['2', '-1', 'yes', '1.0', '']:
            with self.subTest(value=value), self.assertRaises(InvalidConfiguration):
                hardware_commands(options={'HOMING': value})

    def test_hardware_loads_all_gate_records_directly(self):
        for raw in ['0', '1']:
            startup = hardware_commands(options={'RAW_POS': raw})
            gates = [(name, macros) for name, macros in startup.templates
                     if name == 'ecmcN6_outputEnable.template']
            self.assertEqual([(m['CH_ID'], int(m['MASK'], 0)) for _, m in gates],
                             [('01', 0x10000), ('02', 0x20000), ('03', 0x40000)])

    def test_records_have_valid_links_and_optional_scaled_record(self):
        for raw in ['0', '1']:
            with self.subTest(raw=raw):
                startup = hardware_commands(options={'RAW_POS': raw})
                database = expanded_database(startup)
                names = re.findall(r'record\(\w+,\s*"([^"]+)"', database)
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual('TEST:Enc01-PosScaled' in names, raw == '1')
                self.assertIn('TEST:Enc01-PosAct', names)
                enc = re.search(r'record\(ai,\s*"TEST:Enc01-PosAct"\)\s*\{(.*?)\n\}', database, re.S)[1]
                self.assertIn('/ec0.s3.positionActual01?', enc)
                self.assertRegex(enc, r'field\(PREC,\s*"0"\)')
                if raw == '1':
                    scaled = re.search(r'record\(ai,\s*"TEST:Enc01-PosScaled"\)\s*\{(.*?)\n\}', database, re.S)[1]
                    self.assertIn('/ec0.s3.positionActualScaled01?', scaled)
                self.assertIn('TEST:CfgRawPosition', names)
                sources = set(re.findall(r'/ec0\.s3\.(\w+)[?=]', database))
                self.assertLessEqual(sources, startup.entries().keys())
                for output, mask in [(1, 0x10000), (2, 0x20000), (3, 0x40000)]:
                    name = f'TEST:PosOut{output:02d}-Ena'
                    body = re.search(r'record\(bo,\s*"' + name + r'"\)\s*\{(.*?)\n\}', database, re.S)[1]
                    self.assertIn(f'0x{mask:08x}', body)
                    self.assertRegex(body, r'field\(PINI,\s*"NO"\)')
                    self.assertIn(name + '-RB', names)
                # The whole-word record must not overwrite ARM at initialization.
                body = re.search(r'record\(mbboDirect,\s*"TEST:BO01-Arr"\)\s*\{(.*?)\n\}', database, re.S)[1]
                self.assertRegex(body, r'field\(PINI,\s*"0"\)')

    def test_optional_panels_only_show_mapped_channels(self):
        for raw, homing in product(['0', '1'], repeat=2):
            startup = hardware_commands(options={'RAW_POS': raw, 'HOMING': homing})
            names = set(re.findall(r'record\(\w+,\s*"([^"]+)"', expanded_database(startup)))
            visited = []
            for filename in ['ecmcN6-1-1-1-S_OPT.ui', 'ecmcN6-1-1-1-S_OPT_expert.ui']:
                root = ET.parse(ROOT / 'qt' / filename).getroot()
                def check(widget):
                    props = {p.get('name'): p[0].text or '' for p in widget.findall('property')}
                    if 'channel' in props:
                        pv = expand(props['channel'], dict(IOC='TEST', MasterID='0', SlaveID='3'))
                        pv = pv.replace('TEST:m0s3-', 'TEST:')
                        self.assertIn(pv.split('.', 1)[0], names, (filename, pv))
                        visited.append(pv)
                    if 'visibilityCalc' in props:
                        self.assertEqual(props['visibilityCalc'], 'A==1')
                        flag = homing if props['channel'].endswith('CfgHoming') else raw
                        if flag == '0':
                            return
                    for child in widget.findall('widget'):
                        check(child)
                check(root.find('widget'))
                if filename.endswith('_OPT.ui'):
                    related = root.find(".//widget[@name='expertPanel']/property[@name='files']/string")
                    self.assertEqual(related.text, 'ecmcN6-1-1-1-S_OPT_expert.ui')
            self.assertEqual('TEST:Enc01-PosScaled' in visited, raw == '1')
            self.assertEqual('TEST:Drv01-HomeMethod' in visited, homing == '1')
            self.assertEqual('TEST:Drv01-Stat.BC' in visited, homing == '1')
            for output in [1, 2, 3]:
                self.assertIn(f'TEST:PosOut{output:02d}-Ena', visited)

    def test_panels_compile_with_qt(self):
        uic = shutil.which('uic') or shutil.which('uic-qt5')
        if not uic:
            self.skipTest('Qt uic is not installed')
        with tempfile.TemporaryDirectory() as directory:
            for name in ['ecmcN6-1-1-1-S_OPT.ui', 'ecmcN6-1-1-1-S_OPT_expert.ui']:
                subprocess.run([uic, str(ROOT / 'qt' / name), '-o', str(Path(directory) / (name + '.h'))],
                               check=True, capture_output=True, text=True)

    def test_config_records_load_in_softioc(self):
        softioc = shutil.which('softIoc')
        msi = shutil.which('msi')
        if not softioc or not msi:
            self.skipTest('EPICS softIoc/msi is not installed')
        with tempfile.TemporaryDirectory() as directory:
            for raw in ['0', '1']:
                rendered = subprocess.run([msi, '-M', f'ECMC_P=TEST:,RAW_POS={raw}',
                                           str(DB / 'ecmcN6_OPT_config.template')],
                                          check=True, capture_output=True, text=True).stdout
                path = Path(directory) / 'config.db'
                path.write_text(rendered)
                result = subprocess.run([softioc], input=f'dbLoadRecords("{path}")\ndbpr("TEST:CfgRawPosition",1)\nexit\n',
                                        capture_output=True, text=True, check=True, timeout=15)
                self.assertNotIn('ERROR', result.stdout + result.stderr)
                self.assertRegex(result.stdout, r'INP\s*:\s*LINK ' + raw)


if __name__ == '__main__':
    unittest.main()
