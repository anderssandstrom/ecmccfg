#!/usr/bin/env python3
"""Check status-reader type and actual database forward-link calculations; no IOC."""
from pathlib import Path
import re

import unittest

def check_status_chain():
    ROOT = Path(__file__).resolve().parents[1]
    text = (ROOT / 'db/core/ecmcAxis.db').read_text()
    text = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))
    records = {}
    for kind, name, body in re.findall(r'record\((\w+),\s*"([^"]+)"\)\s*\{(.*?)\n\}', text, re.S):
        fields = dict(re.findall(r'field\(\s*(\w+)\s*,\s*"([^"]*)"\s*\)', body))
        records[name] = kind, fields
    prefix = '${P}${AXIS_NAME}'

    # EPICS may initialize records in name order, not database declaration order.
    # Every client of status must use the same asyn publication interface. The
    # mode indicator must not win first binding with asynUInt32Digital.
    readers = [(name, fields) for name, (_, fields) in records.items()
               if '/ax$(AXIS_NO).status?' in fields.get('INP', '')]
    assert len(readers) == 1 and readers[0][0] == prefix+'-Stat'
    assert readers[0][1]['DTYP'] == 'asynInt32'
    mode = records[prefix+'-AutoExecuteOnTargetPos-RB'][1]
    assert 'asyn' not in mode.get('DTYP', '').lower()
    assert mode['ZNAM'] == 'Execute required' and mode['ONAM'] == 'Write starts move'

    # Evaluate the actual record input/forward-link graph, starting with the raw
    # values that reproduced stuck Busy/InStartup in the live report.
    values = {}
    def read(link):
        name, dot, field = link.partition('.')
        value = values.get(name, 0)
        if dot and field.startswith('B'):
            return (int(value) >> int(field[1:], 16)) & 1
        return value

    def process(name, visited=None):
        visited = set() if visited is None else visited
        assert name not in visited, 'record forward-link cycle: '+name
        visited.add(name)
        kind, fields = records[name]
        if kind == 'calc':
            expression = fields['CALC']
            assert re.fullmatch(r'[A0-9a-fA-FxX\s()&|<>+*/.=-]+', expression), expression
            values[name] = eval(expression, {'__builtins__': {}}, {'A': read(fields['INPA'])})
        elif kind in ('bi', 'mbbi', 'mbbiDirect'):
            values[name] = read(fields['INP'])
        link = fields.get('FLNK')
        if link:
            child = link.removesuffix('.PROC')
            if child in records:
                process(child, visited)

    def publish(suffix, raw):
        name = prefix+suffix
        values[name] = raw
        process(name)

    control = records[prefix+'-EncMode'][1]
    assert control['DTYP'] == 'asynUInt32Digital'
    assert '0x3c000' in control['OUT'] and control['SHFT'] == '14'
    assert control['ZRST'] == 'Auto power' and control['EIST'] == 'Encoder 8'
    assert prefix+'-EncForceOn' not in records
    for selection in range(9):
        for hold in (0, 1):
            publish('-Stat', (selection<<25)|(hold<<29))
            assert values[prefix+'-EncMode-RB'] == selection
            # Retired axis status bit 29 must not affect selection or Busy.
            assert values[prefix+'-Busy'] == 0
            assert values[prefix+'-AutoExecuteOnTargetPos-RB'] == 0

    publish('-Stat', 0x61e6c8)
    assert values[prefix+'-Busy'] == 1
    assert values[prefix+'-InStartup'] == 1
    assert values[prefix+'-AutoExecuteOnTargetPos-RB'] == 0
    idle = 0x61e6c8 & ~((1<<3)|(1<<16)|(1<<21)|(1<<22))
    for selected in (0, 1, 0):
        publish('-Stat', idle | (selected<<24))
        assert values[prefix+'-Busy'] == 0
        assert values[prefix+'-InStartup'] == 0
        assert values[prefix+'-AutoExecuteOnTargetPos-RB'] == selected
        publish('-StatExt', (31<<8)|(1003&255))
        assert values[prefix+'-SeqState'] == 235
        assert values[prefix+'-LastIlock'] == 31
        assert values[prefix+'-Busy'] == 0
        assert values[prefix+'-AutoExecuteOnTargetPos-RB'] == selected


def check_encoder_status_chain():
    root = Path(__file__).resolve().parents[1]
    text = (root/'db/core/ecmcEnc.db').read_text()
    records = {name: (kind, dict(re.findall(r'field\(\s*(\w+)\s*,\s*"([^"]*)"\s*\)', body)))
               for kind, name, body in re.findall(r'record\((\w+),\s*"([^"]+)"\)\s*\{(.*?)\n\}', text, re.S)}
    prefix = '${P}${AXIS_NAME}-Enc0$(ENC_NO)'
    readers = [(name, fields) for name, (_, fields) in records.items()
               if '.enc.status$(ENC_NO)?' in fields.get('INP', '')]
    assert len(readers) == 1 and readers[0][0] == prefix+'-Stat'
    assert readers[0][1]['DTYP'] == 'asynInt32'
    assert '.enc.powerstate' not in text
    values = {}
    def read(link):
        name, _, field = link.partition('.')
        value = values.get(name, 0)
        return (int(value) >> int(field[1:], 16)) & 1 if field.startswith('B') else value
    def process(name, visited):
        assert name not in visited, 'encoder forward-link cycle'
        visited.add(name)
        kind, fields = records[name]
        if kind == 'calc':
            assert fields['CALC'] == '(A>>8)&7'
            values[name] = (read(fields['INPA']) >> 8) & 7
        elif kind in ('mbbi', 'mbbiDirect', 'bi'):
            values[name] = read(fields['INP'])
        if fields.get('FLNK'):
            process(fields['FLNK'].removesuffix('.PROC'), visited)
    for state in range(5):
        for flags in range(32):
            values[prefix+'-Stat'] = (state<<8)|flags
            process(prefix+'-Stat', set())
            assert values[prefix+'-PwrState'] == state
            for bit, suffix in enumerate(('PwrEnable-RB','PwrOn','Ready','Homed','Absolute')):
                assert values[prefix+'-'+suffix] == ((flags>>bit)&1)
    assert records[prefix+'-PwrState'][1]['FRSV'] == 'MAJOR'


class AxisStatusRecordChainTests(unittest.TestCase):
    def test_encoder_status_decodes_power_and_flags(self):
        check_encoder_status_chain()

    def test_status_and_mode_updates_share_one_asyn_reader(self):
        check_status_chain()


if __name__ == '__main__':
    unittest.main()
