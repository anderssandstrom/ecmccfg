"""Static OPT integration checks; no IOC connection or hardware writes.

Run: python3 tests/test_ex72xx_opt.py
Database checks use EPICS msi; UI checks use Qt uic (when installed).
"""
import itertools
import ctypes
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / 'hardware/Beckhoff_7XXX'
DB = ROOT / 'db/Beckhoff_7XXX'
MODELS = ['EL7211-9014', 'EP7211-0034', 'EL7201', 'EL7201-0010',
          'ELM7231-0010', 'ELM7222-0010']


class InvalidConfiguration(Exception):
    pass


def expand(text, values):
    """Expand nested EPICS macros, including defaults and empty values."""
    pattern = re.compile(r'\$\{([^{}]*)\}|\$\(([^()]*)\)')
    while pattern.search(text):
        def replace(match):
            expr = match[1] if match[1] is not None else match[2]
            name, sep, default = expr.partition('=')
            if name in values:
                return str(values[name])
            if sep:
                return default
            raise AssertionError(f'Unresolved macro {name}: {text}')
        text = pattern.sub(replace, text)
    return text


def arguments(text):
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace = ', \t'
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)


def expression(text):
    text = re.sub(r'(?<!!)(?<![=])=(?!=)', '==', text)
    return eval(text, {'__builtins__': {}}, {})


class Startup:
    """Evaluate only the IOC-shell subset used by the new OPT snippets.

    Hardware commands are captured, never executed. Unknown commands fail closed.
    Macro scopes are inherited like iocshLoad; environment changes persist.
    """
    def __init__(self, model, options=None, rate=1000):
        self.env = dict(SCRIPTEXEC='iocshLoad', ecmccfg_DIR='', ECMC_P='TEST:',
                        ECMC_EC_SLAVE_NUM='1', ECMC_EC_SAMPLE_RATE=str(rate),
                        ECMC_SYNC_0_OFFSET_NS='0', ECMC_SYNC_1_OFFSET_NS='0',
                        ECMC_PREFIX='TEST:')
        self.commands = []
        self.substitutions = []
        self.templates = []
        family = 'ELM' if model.startswith('ELM') else ('EL' if model.startswith('ED') else model[:2])
        directory = ROOT / 'hardware/Beckhoff_MX' if family == 'MO' else HW / family
        self.run(directory / f'ecmc{model}_OPT.cmd', options or {})

    def run(self, path, scope):
        for raw in path.read_text().splitlines():
            if not raw.strip() or raw.lstrip().startswith('#'):
                continue
            line = expand(raw, self.env | scope).strip()
            if line.startswith('#'):
                continue
            if line.startswith('ecmcExit'):
                # Invalid configuration must fail before reset or any bus operation.
                assert not self.commands, self.commands
                raise InvalidConfiguration(line)
            m = re.fullmatch(r'(epicsEnvSet|epicsEnvUnset|ecmcEpicsEnvSetCalcTernary|ecmcEpicsEnvSetCalc)\((.*)\)', line)
            if m:
                args = arguments(m[2])
                if m[1] == 'epicsEnvSet':
                    self.env[args[0]] = args[1]
                elif m[1] == 'epicsEnvUnset':
                    self.env.pop(args[0], None)
                elif m[1] == 'ecmcEpicsEnvSetCalcTernary':
                    self.env[args[0]] = args[2] if expression(args[1]) else args[3]
                else:
                    result = expression(args[1])
                    self.env[args[0]] = (args[2] % int(result) if len(args) > 2
                                         else format(float(result), '.15g'))
                continue
            words = shlex.split(line)
            if words[0] == 'ecmcConfigOrDie':
                self.commands.append(words[1])
                continue
            if words[0] == 'iocshLoad':
                filename = words[1]
                params = {}
                if len(words) > 2:
                    # Script argument strings contain nested, quoted macro lists.
                    params = dict(item.split('=', 1) for item in arguments(words[2]))
                child = scope | params
                if filename == 'slaveVerify.cmd':
                    self.commands.append('RESET')
                elif filename == 'applySubstitutions.cmd':
                    macros = dict(item.split('=', 1) for item in arguments(child.get('MACROS', '')))
                    self.substitutions.append((child['SUBST_FILE'], macros))
                elif filename == 'applyTemplate.cmd':
                    macros = dict(item.split('=', 1) for item in arguments(child.get('PARAM', '')))
                    self.templates.append((child['TEMPLATE_FILE'], macros))
                else:
                    self.run(HW / filename if (HW / filename).exists() else HW / 'EL' / filename, child)
                continue
            raise AssertionError(f'Unsupported command: {line}')

    def entries(self):
        entries = {}
        for command in self.commands:
            match = re.fullmatch(r'Cfg.EcAddEntryDT\((.*)\)', command)
            if match:
                fields = match[1].split(',')
                name = fields[-1]
                assert name not in entries, f'Duplicate entry {name}'
                entries[name] = (tuple(int(x, 0) for x in fields[3:8]), fields[8])
        assert len(entries) == len({value[0] for value in entries.values()})
        return entries


def legacy_entries(path):
    entries = {}
    for kind, params in re.findall(r'Cfg.EcAddEntry(DT|Complete)\((.*?)\)', path.read_text()):
        fields = params.split(',')
        typ = fields[8] if kind == 'DT' else ('S' if len(fields) == 11 and fields[9] == '1' else 'U') + fields[8]
        entries[fields[-1]] = (tuple(int(x, 0) for x in fields[3:8]), typ)
    return entries


class OptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.msi = shutil.which('msi')
        cls.expansion_cache = {}

    def database(self, startup):
        if not self.msi:
            self.skipTest('EPICS msi is not installed')
        common = dict(ECMC_P='TEST:', PORT='ECMC', ADDR='0', TIMEOUT='1',
                      MASTER_ID='0', SLAVE_POS='1', HWTYPE='EX72XX_OPT')
        result = ''
        for kind, files in [('subs', startup.substitutions), ('template', startup.templates)]:
            for name, macros in files:
                values = common | macros
                key = (kind, name, tuple(sorted(values.items())))
                if key not in self.expansion_cache:
                    args = [self.msi, '-I', str(DB), '-I', str(ROOT / 'db/generic'),
                            '-M', ','.join(f'{k}={v}' for k, v in values.items())]
                    args += ['-S', str(DB / name)] if kind == 'subs' else [str(DB / name)]
                    process = subprocess.run(args, capture_output=True, text=True, check=True)
                    self.assertEqual(process.stderr, '', name)
                    self.expansion_cache[key] = process.stdout
                result += self.expansion_cache[key]
        return result

    def check_records_and_panels(self, startup):
        database = self.database(startup)
        names = re.findall(r'record\(\w+,\s*"([^"]+)"', database)
        self.assertEqual(len(names), len(set(names)), 'duplicate record names')
        sources = set(re.findall(r'/ec0\.s1\.(\w+)[?=]', database))
        self.assertLessEqual(sources, startup.entries().keys(), 'record points to absent PDO')
        config = {}
        for name, body in re.findall(r'record\(\w+,\s*"([^"]+)"\)\s*\{(.*?)\n\}', database, re.S):
            if name.startswith('TEST:Cfg'):
                config[name] = int(re.search(r'field\(INP,\s*"(\d+)"\)', body)[1])

        # Follow includes and only visible related-display links. All selected
        # feature channels must exist; hidden frames subscribe only to config PVs.
        def check_panel(filename, macros):
            root = ET.parse(ROOT / 'qt' / filename).getroot()
            def check_widget(widget):
                props = {p.get('name'): p[0].text or '' for p in widget.findall('property')}
                if 'channel' in props:
                    pv = expand(props['channel'], macros).replace('TEST:m0s1-', 'TEST:')
                    self.assertIn(pv.split('.', 1)[0], names, (filename, pv))
                    if 'visibilityCalc' in props:
                        self.assertIn(pv, config)
                        if not expression(props['visibilityCalc'].replace('A', str(config[pv]))):
                            return
                # Shell-command args are positional CLI arguments, not display macros.
                if widget.get('class') == 'caShellCommand':
                    return
                child_macros = dict(macros)
                for item in expand(props.get('macro', props.get('args', '')), macros).split(','):
                    if item.strip():
                        key, value = item.split('=', 1)
                        child_macros[key.strip()] = value.strip()
                target = props.get('filename', props.get('files'))
                if target and target.startswith(('ecmcEX72XX_OPT', 'ecmcEX7062_OPT')):
                    check_panel(target, child_macros)
                elif target == 'ecmcGraph_v1.ui':
                    self.assertTrue((ROOT / 'qt' / target).exists())
                    self.assertIn(child_macros['PV'].replace('TEST:m0s1-', 'TEST:'), names,
                                  (filename, 'trend PV', child_macros['PV']))
                for child in widget.findall('widget'):
                    check_widget(child)
            check_widget(root.find('widget'))
        check_panel('ecmc'+startup.env['ECMC_HW_PANEL']+'.ui', dict(IOC='TEST', MasterID='0', SlaveID='1'))
        return config

    def test_family_defaults_extend_legacy_pdos(self):
        for model in MODELS:
            with self.subTest(model=model):
                startup = Startup(model)
                if model in ['EL7211-9014', 'EP7211-0034']:
                    path = HW / 'EL/ecmcEX72XX-9014_STD-ch01.cmd'
                elif model == 'EL7201':
                    path = HW / 'EL/ecmcEX72XX_STD-ch01.cmd'
                elif model == 'EL7201-0010':
                    path = HW / 'EL/ecmcEX72XX-0010_STD-ch01.cmd'
                else:
                    path = HW / 'ELM' / f'ecmc{model}.cmd'
                entries = startup.entries()
                # Default ENC_STAT intentionally extends the legacy CSV mapping.
                baseline = {name: value for name, value in entries.items()
                            if not name.startswith('encoderStatus')}
                self.assertEqual(baseline, legacy_entries(path))
                self.assertIn('encoderStatus01', entries)
                if model == 'ELM7222-0010':
                    self.assertIn('encoderStatus02', entries)
                self.check_records_and_panels(startup)

    def test_supported_option_matrix(self):
        for model in MODELS:
            info_options = (['NONE', 'TEMP'] if model.startswith('ELM') else
                            ['NONE', 'TEMP', 'ERRORS'] +
                            (['INPUTS'] if model in MODELS[:2] else []))
            tp_options = [0] if model == 'EL7201' else [0, 1]
            for mode, tp, info, diag in itertools.product(['CSV', 'CSP', 'CST', 'CSTCA'], tp_options, info_options, [0, 1]):
                with self.subTest(model=model, mode=mode, tp=tp, info=info, diag=diag):
                    startup = Startup(model, dict(MODE=mode, TP=str(tp), INFO2=info, DIAG=str(diag)))
                    entries = startup.entries()
                    self.check_records_and_panels(startup)
                    for ch in range(1, 3 if model == 'ELM7222-0010' else 2):
                        suffix = f'{ch:02}'
                        self.assertEqual('touchProbeStatus'+suffix in entries, bool(tp))
                        self.assertEqual('voltageActual'+suffix in entries, bool(diag))
                        demand = dict(CSV='velocitySetpoint', CSP='positionSetpoint', CST='torqueSetpoint', CSTCA='torqueSetpoint')[mode]
                        self.assertIn(demand+suffix, entries)
                        self.assertIn(f'Cfg.EcAddSdo(1,0x{0x7010+(ch-1)*0x100:x},0x03,{dict(CSV=9,CSP=8,CST=10,CSTCA=11)[mode]},1)', startup.commands)
                    self.assertFalse(any(key.startswith('ECMC_EX72XX_OPT_') for key in startup.env))

    def test_cstca_angle_mapping_and_records(self):
        for model in MODELS:
            with self.subTest(model=model):
                startup = Startup(model, dict(MODE='CSTCA'))
                config = self.check_records_and_panels(startup)
                database = self.database(startup)
                for ch in range(1, 3 if model == 'ELM7222-0010' else 2):
                    pdo = 0x1614 + (ch-1)*0x40 if model.startswith('ELM') else 0x1603
                    self.assertEqual(startup.entries()[f'commutationAngle{ch:02}'],
                                     ((1, 2, pdo, 0x7010+(ch-1)*0x100, 0x0e), 'U16'))
                    self.assertEqual(config['TEST:CfgMode'+('02' if ch == 2 else '')], 3)
                    self.assertEqual(config['TEST:CfgTorqueOffset'+('02' if ch == 2 else '')], 0)
                    for record_type, suffix in [('ao', ''), ('ai', '-RB')]:
                        body = re.search(r'record\('+record_type+r',\s*"TEST:Drv'+f'{ch:02}'+
                                         r'-ComAngle'+suffix+r'"\)\s*\{(.*?)\n\}', database, re.S)[1]
                        self.assertIn('field(ESLO, "0.0054931640625")', body)
                        self.assertIn('field(EGU,  "deg")', body)
                        if record_type == 'ao':
                            self.assertIn('field(DRVH, "359.9945068359375")', body)
                for mode in ['CSV', 'CSP', 'CST']:
                    other = Startup(model, dict(MODE=mode))
                    self.assertFalse(any(name.startswith('commutationAngle') for name in other.entries()))
                    self.assertNotIn('-ComAngle', self.database(other))
        panel = ET.parse(ROOT / 'qt/ecmcEX72XX_OPT_cstca.ui').getroot()
        entry = panel.find(".//widget[@name='commutationAngle']")
        self.assertEqual(entry.get('class'), 'caTextEntry')
        self.assertEqual(entry.findtext("property[@name='readOnly']/bool"), 'false')
        self.assertTrue(entry.findtext("property[@name='channel']/string").endswith('-Drv$(ChID)-ComAngle'))

    def test_encoder_status_independent_of_mode(self):
        for model, mode, enabled in itertools.product(MODELS, ['CSV', 'CSP', 'CST', 'CSTCA'], [0, 1]):
            with self.subTest(model=model, mode=mode, enabled=enabled):
                startup = Startup(model, dict(MODE=mode, ENC_STAT=str(enabled)))
                config = self.check_records_and_panels(startup)
                for ch in range(1, 3 if model == 'ELM7222-0010' else 2):
                    name = f'encoderStatus{ch:02}'
                    self.assertEqual(name in startup.entries(), bool(enabled))
                    self.assertEqual(config['TEST:CfgEncoderStatus'+('02' if ch == 2 else '')], enabled)
                    if enabled:
                        pdo = (0x1a02+(ch-1)*0x40) if model.startswith('ELM') else 0x1a0c
                        self.assertEqual(startup.entries()[name],
                                         ((2, 3, pdo, 0x6000+(ch-1)*0x100, 1), 'U16'))
                default = Startup(model, dict(MODE=mode))
                self.assertIn('encoderStatus01', default.entries())
        override = Startup('ELM7222-0010', dict(ENC_STAT='0', ENC_STAT_2='1'))
        self.assertNotIn('encoderStatus01', override.entries())
        self.assertIn('encoderStatus02', override.entries())
        config = self.check_records_and_panels(override)
        self.assertEqual(config['TEST:CfgEncoderStatus'], 0)
        self.assertEqual(config['TEST:CfgEncoderStatus02'], 1)
        override = Startup('ELM7222-0010', dict(ENC_STAT='1', ENC_STAT_1='0'))
        self.assertNotIn('encoderStatus01', override.entries())
        self.assertIn('encoderStatus02', override.entries())
        for model, options in [('EL7211-9014', dict(ENC_STAT='2')),
                               ('ELM7222-0010', dict(ENC_STAT_2='2')),
                               ('EP7211-0034', dict(ENC_STAT_2='0'))]:
            with self.subTest(model=model, options=options):
                with self.assertRaises(InvalidConfiguration):
                    Startup(model, options)

    def test_independent_elm_channels(self):
        for mode1, mode2 in itertools.product(['CSV', 'CSP', 'CST', 'CSTCA'], repeat=2):
            startup = Startup('ELM7222-0010', dict(MODE_1=mode1, MODE_2=mode2,
                              TP_1='0', TP_2='1', DIAG_1='0', DIAG_2='1', INFO2_1='NONE', INFO2_2='TEMP'))
            config = self.check_records_and_panels(startup)
            self.assertEqual(config['TEST:CfgMode'], ['CSV', 'CSP', 'CST', 'CSTCA'].index(mode1))
            self.assertEqual(config['TEST:CfgMode02'], ['CSV', 'CSP', 'CST', 'CSTCA'].index(mode2))
            self.assertIn('temperatureActual02', startup.entries())
            self.assertNotIn('temperatureActual01', startup.entries())

    def test_unsupported_options_fail_before_reset(self):
        for model, options in [('EL7201', dict(TP='1')),
                               ('EL7201-0010', dict(INFO2='INPUTS')),
                               ('ELM7231-0010', dict(INFO2='INPUTS')),
                               ('ELM7231-0010', dict(INFO2='ERRORS')),
                               ('ELM7222-0010', dict(MODE_2='INVALID')),
                               ('ELM7222-0010', dict(DIAG_2='2')),
                               ('EL7211-9014', dict(MODE_2='CSP')),
                               ('EL7211-9014', dict(MODE='INVALID')),
                               ('EP7211-0034', dict(INFO2='INVALID')),
                               ('EP7211-0034', dict(TP='2'))]:
            with self.subTest(model=model, options=options):
                with self.assertRaises(InvalidConfiguration):
                    Startup(model, options)

    def test_family_timing_and_overrides(self):
        for model in MODELS:
            startup = Startup(model, rate=2000)
            self.assertEqual('Cfg.EcSetSlavePortWiringCheckEnable(1,1)' in startup.commands,
                             model.startswith('EP'))
            dc = next(x for x in startup.commands if x.startswith('Cfg.EcSlaveConfigDC'))
            expected = ('62500,0,500000,0' if model.startswith('ELM') else
                        '500000,250000,0,0' if model == 'EL7201' else '500000,0,0,0')
            self.assertEqual(dc, f'Cfg.EcSlaveConfigDC(1,0x700,{expected})')
            self.assertIn('Cfg.EcSlaveConfigWatchDog(1,500,5000)', startup.commands)
            if model.startswith('ELM'):
                self.assertFalse(any('0x8011,0x11' in x for x in startup.commands))
                self.assertIn('Cfg.EcWriteSdo(1,0x8008,0x1,1,1)', startup.commands)
            else:
                self.assertIn('Cfg.EcAddSdo(1,0x8011,0x11,100,4)', startup.commands)
            overridden = Startup(model, dict(SYNC_0_CYCLE='125000', SYNC_0_SHIFT='123',
                                SYNC_1_CYCLE='1000000', SYNC_1_SHIFT='456',
                                WATCHDOG_DIVIDER='200', WATCHDOG_INTERVALS='300'))
            self.assertIn('Cfg.EcSlaveConfigDC(1,0x700,125000,123,1000000,456)', overridden.commands)
            self.assertIn('Cfg.EcSlaveConfigWatchDog(1,200,300)', overridden.commands)

    def test_family_record_scaling(self):
        for model in ['EL7211-9014', 'ELM7231-0010']:
            database = self.database(Startup(model, dict(DIAG='1')))
            for suffix in ['Spd-RB', 'VelAct']:
                body = re.search(r'record\(ai,\s*"TEST:Drv01-'+suffix+r'"\)\s*\{(.*?)\n\}', database, re.S)[1]
                expected_scale = '1' if model.startswith('ELM') else '2.3406E-5'
                expected_unit = 'RAW' if model.startswith('ELM') else 'rad/s'
                self.assertIn('field(ESLO, "'+expected_scale+'")', body)
                self.assertIn('field(EGU,  "'+expected_unit+'")', body)
        database = self.database(Startup('ELM7231-0010', dict(VEL_ESLO='0.001', VEL_EGU='rad/s')))
        self.assertIn('field(ESLO, "0.001")', database)

    def test_elm_channel_two_addresses(self):
        entries = Startup('ELM7222-0010', dict(MODE='CSP', DIAG='1', TP='1', INFO2='TEMP')).entries()
        expected = {'driveControl02': (1, 2, 0x1650, 0x7110, 1),
                    'positionSetpoint02': (1, 2, 0x1651, 0x7110, 5),
                    'driveStatus02': (2, 3, 0x1a50, 0x6110, 1),
                    'touchProbeStatus02': (2, 3, 0x1a43, 0x6101, 1),
                    'followingError02': (2, 3, 0x1a51, 0x6110, 6),
                    'temperatureActual02': (2, 3, 0x1a55, 0x6110, 0x13)}
        for name, address in expected.items():
            self.assertEqual(entries[name][0], address)

    def test_overview_selection_and_ds402_buttons(self):
        for model in MODELS:
            expected = 'EX72XX_OPT_2ch' if model == 'ELM7222-0010' else 'EX72XX_OPT'
            self.assertEqual(Startup(model).env['ECMC_HW_PANEL'], expected)
        root = ET.parse(ROOT / 'qt/ecmcEX72XX_OPT_2ch.ui').getroot()
        rect = root.find("widget/property[@name='geometry']/rect")
        self.assertEqual((rect.findtext('width'), rect.findtext('height')), ('128', '500'))
        for ch in [1, 2]:
            button = root.find(f".//widget[@name='openChannel{ch}']")
            args = button.findtext("property[@name='args']/string")
            self.assertIn(f'ChID={ch:02}', args)
            self.assertIn('CfgSuffix='+('02' if ch == 2 else ''), args)
        for mode in ['csv', 'csp', 'cst', 'cstca']:
            root = ET.parse(ROOT / f'qt/ecmcEX72XX_OPT_{mode}.ui').getroot()
            for name, suffix in [('enableDrive', 'TrgDS402Ena'), ('disableDrive', 'TrgDS402Dis')]:
                button = root.find(f".//widget[@name='{name}']")
                self.assertEqual(button.get('class'), 'caMessageButton')
                self.assertTrue(button.findtext("property[@name='channel']/string").endswith('-Drv$(ChID)-'+suffix+'.PROC'))
                self.assertEqual(button.findtext("property[@name='releaseMessage']/string"), '1')
                self.assertFalse(button.findtext("property[@name='pressMessage']/string"))

    def test_ds402_decoder_all_statuswords(self):
        softioc = shutil.which('softIoc')
        if not softioc:
            self.skipTest('EPICS softIoc/libCom is not installed')
        binary = Path(softioc).resolve()
        library = binary.parents[2] / 'lib' / binary.parent.name / 'libCom.so'
        if not library.exists():
            self.skipTest('EPICS libCom is not installed')
        lib = ctypes.CDLL(str(library))
        lib.postfix.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_short)]
        lib.postfix.restype = ctypes.c_long
        lib.calcPerform.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_char_p]
        lib.calcPerform.restype = ctypes.c_long
        expression_text = re.search(r'field\(CALC,"([^"]+)"\)', (DB / 'ecmcEX72XX_OPT_state.template').read_text())[1]
        bytecode = ctypes.create_string_buffer(4096)
        error = ctypes.c_short()
        self.assertEqual(lib.postfix(expression_text.encode(), bytecode, ctypes.byref(error)), 0, error.value)
        inputs = (ctypes.c_double * 12)()
        result = ctypes.c_double()
        # Independently specified bit patterns from the DS402 state table.
        patterns = ['x0xx0000', 'x1xx0000', 'x01x0001', 'x01x0011', 'x01x0111',
                    'x00x0111', 'x0xx1111', 'x0xx1000']
        for word in range(65536):
            bits = format(word & 255, '08b')
            expected = next((index for index, pattern in enumerate(patterns)
                             if all(a == 'x' or a == b for a, b in zip(pattern, bits))), 8)
            inputs[0] = word
            self.assertEqual(lib.calcPerform(inputs, ctypes.byref(result), bytecode), 0)
            self.assertEqual(result.value, expected, hex(word))

    def test_mode_setpoints_are_writable(self):
        for mode, suffix in [('csv', 'Spd'), ('csp', 'PosCmd'), ('cst', 'Trq'), ('cstca', 'Trq')]:
            root = ET.parse(ROOT / f'qt/ecmcEX72XX_OPT_{mode}.ui').getroot()
            entry = root.find(".//widget[@name='targetSetpoint']")
            self.assertEqual(entry.get('class'), 'caTextEntry')
            self.assertEqual(entry.findtext("property[@name='readOnly']/bool"), 'false')
            self.assertTrue(entry.findtext("property[@name='channel']/string").endswith('-Drv$(ChID)-'+suffix))
            database = self.database(Startup('ELM7222-0010', dict(MODE=mode.upper())))
            for ch in ['01', '02']:
                self.assertRegex(database, r'record\(ao,\s*"TEST:Drv'+ch+'-'+suffix+r'"\)')

    def test_state_database_loads_in_epics(self):
        softioc = shutil.which('softIoc')
        if not softioc or not self.msi:
            self.skipTest('EPICS softIoc/msi is not installed')
        expansion = subprocess.run([self.msi, '-M', 'ECMC_P=OPTTEST:,CH_ID=01',
                                   str(DB / 'ecmcEX72XX_OPT_state.template')],
                                  capture_output=True, text=True, check=True)
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / 'state.db'
            database.write_text('record(longin,"OPTTEST:Drv01-Stat") { field(INP,"39") }\n'+expansion.stdout)
            # Load and validate records without iocInit: no CA server or hardware.
            process = subprocess.run([softioc], input=f'dbLoadRecords("{database}")\nexit\n',
                                     capture_output=True, text=True, timeout=15, check=True)
            self.assertNotIn('ERROR', process.stdout+process.stderr)
            self.assertNotIn('Illegal choice', process.stdout+process.stderr)

    def test_qt_panels_compile(self):
        uic = shutil.which('uic-qt5') or shutil.which('uic')
        if not uic:
            self.skipTest('Qt uic is not installed')
        with tempfile.TemporaryDirectory() as temp:
            for panel in (ROOT / 'qt').glob('ecmcEX72XX_OPT*.ui'):
                subprocess.run([uic, str(panel), '-o', str(Path(temp) / (panel.stem+'.h'))],
                               capture_output=True, text=True, check=True)


if __name__ == '__main__':
    unittest.main()
