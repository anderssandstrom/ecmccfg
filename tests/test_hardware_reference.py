"""Catalogue regressions use synthetic scripts, not mutable lab examples."""
import importlib.util
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'hardware_reference', Path(__file__).resolve().parents[1]
    / 'hugo/scripts/generate_hardware_reference.py')
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


class HardwareReferenceTests(unittest.TestCase):
    def test_macros_conditions_and_optional_realtime_argument(self):
        source = '''# Cfg.EcAddEntryDT(ignored)
${ENABLE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${SLAVE},2,3,2,3,0x1a00,${INDEX=0x6064},0,U32,${KEY=positionActual}${CH_ID=01},0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT($(SLAVE),2,3,1,2,0x1600,0x6040,0,U16,driveControl01)"
'''
        first, second = reference.declarations(source)
        self.assertEqual(first['name'], '${KEY=positionActual}${CH_ID=01}')
        self.assertEqual(first['condition'], '${ENABLE}')
        self.assertEqual(first['datatype'], 'U32; update=0')
        self.assertEqual(first['direction'], 'Input (slave → master)')
        self.assertIn('${INDEX=0x6064}:0', first['address'])
        self.assertEqual(second['name'], 'driveControl01')
        self.assertEqual(second['direction'], 'Output (master → slave)')

    def test_legacy_signed_and_update_forms_have_correct_names(self):
        source = '''Cfg.EcAddEntryComplete(0,2,3,2,3,0x1a00,0x6064,0,32,positionActual01)
Cfg.EcAddEntryComplete(0,2,3,2,3,0x1a00,0x6064,0,32,1,signedPosition01)
Cfg.EcAddEntryComplete(0,2,3,2,3,0x1a00,0x6064,0,32,arrayPosition01,0)
'''
        entries = reference.declarations(source)
        self.assertEqual([entry['name'] for entry in entries],
                         ['positionActual01', 'signedPosition01', 'arrayPosition01'])
        self.assertIn('signed=1', entries[1]['datatype'])
        self.assertIn('update=0', entries[2]['datatype'])

    def test_aliases_bit_items_arrays_and_malformed_source(self):
        source = '''Cfg.EcAddEntryAlias(${SLAVE},positionActual01,POS)
Cfg.EcAddDataDT(ec$(MASTER=0).s${SLAVE}.control,0,4,1,B1,trigger01)
Cfg.EcAddMemMapDT(ec0.s1.array,${BYTES=100},2,U8,ec0.s1.mm.data)
Cfg.EcAddEntryDT(0,2,3,2,3,0x1a00,0x6064,0,S32,broken"
'''
        alias, bit, array, warning = reference.declarations(source)
        self.assertEqual(alias['name'], 'POS')
        self.assertEqual(alias['address'], 'Alias of positionActual01')
        self.assertEqual(bit['name'], 'trigger01')
        self.assertEqual(bit['datatype'], 'B1')
        self.assertIn('bit 4', bit['address'])
        self.assertEqual(array['name'], 'ec0.s1.mm.data')
        self.assertEqual(warning['datatype'], 'Parse warning')
        self.assertEqual(warning['line'], 4)

    def test_shared_snippets_are_linked_transitively_and_removal_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hardware = root / 'hardware' / 'Vendor'
            hardware.mkdir(parents=True)
            (hardware / 'ecmcDevice_OPT.cmd').write_text(
                '#-d   \\param RAW_POS Use raw feedback, default 0.\n'
                '${SCRIPTEXEC} ${ecmccfg_DIR}ecmcChannel.cmd "CH_ID=01"\n')
            (hardware / 'ecmcChannel.cmd').write_text(
                '${SCRIPTEXEC} ${ecmccfg_DIR}ecmcPDO.cmd\n')
            pdo = hardware / 'ecmcPDO.cmd'
            pdo.write_text('Cfg.EcAddEntryDT(0,2,3,2,3,0x1a00,0x6064,0,S32,positionActual${CH_ID})\n')
            (hardware / 'ecmcSDO.cmd').write_text('Cfg.EcAddSdo(0,0x6060,0,9,1)\n')
            pages = reference.render(root)
            body = pages['vendor.md']
            self.assertIn('## ecmcDevice_OPT.cmd', body)
            self.assertIn('RAW_POS Use raw feedback', body)
            self.assertIn('vendor.md#snippet-ecmcpdo', body)
            self.assertNotIn('ecmcSDO.cmd', body)
            self.assertIn('`positionActual${CH_ID}`', body)
            output = root / 'output'
            output.mkdir()
            for name, content in pages.items():
                (output / name).write_text(content)
            with patch.object(reference, 'OUTPUT', output), \
                    patch.object(reference, 'render', return_value=pages), \
                    patch('sys.argv', ['generate_hardware_reference.py', '--check']), \
                    redirect_stderr(StringIO()), redirect_stdout(StringIO()):
                reference.main()
                (output / 'vendor.md').write_text(body + '\nStale edit\n')
                with self.assertRaises(SystemExit) as failure:
                    reference.main()
                self.assertEqual(failure.exception.code, 1)
            pdo.unlink()
            self.assertNotIn('vendor.md', reference.render(root))


if __name__ == '__main__':
    unittest.main()
