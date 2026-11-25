#!/usr/bin/env python3
"""Static YAML/template contract for soft-limit restore and synchronization."""
from pathlib import Path
import ast
import json
from jinja2 import Environment

root = Path(__file__).resolve().parents[1]
source = (root / 'scripts/jinja2/templates/epicsMotorRecord.jinja2').read_text()
start = source.index('#-  Default to sync softlimits')
end = source.index('epicsEnvUnset(ECMC_AXIS_FLAGS)', start)
template = Environment().from_string(source[start:end])

for restore, sync, mode in (
        (False, False, 0), (False, True, 0),
        (True, False, 2), (True, True, 1)):
    rendered = template.render(
        epics={'motorRecord': {'restoreSoftLimits': restore,
                               'syncSoftLimits': sync}},
        axis={'parameters': ''}, axisFlags=0)
    assert f'syncSoftLims={int(sync)};' in rendered
    assert f'restoreMotorSoftLims={mode};' in rendered

# Advanced legacy parameters occur last and can deliberately override YAML.
rendered = template.render(
    epics={'motorRecord': {'restoreSoftLimits': True, 'syncSoftLimits': False}},
    axis={'parameters': 'restoreMotorSoftLims=1;'}, axisFlags=0)
assert rendered.index('restoreMotorSoftLims=2;') < rendered.index('restoreMotorSoftLims=1;')

schema = (root / 'scripts/jinja2/ecmcYamlSchema.py').read_text()
restore_rules = [node for node in ast.walk(ast.parse(schema))
                 if isinstance(node, ast.Dict)
                 for key, value in zip(node.keys, node.values)
                 if isinstance(key, ast.Constant) and key.value == 'restoreSoftLimits'
                 and isinstance(value, ast.Dict)
                 for node in [value]]
assert len(restore_rules) == 1
rules = {key.value: value for key, value in zip(restore_rules[0].keys, restore_rules[0].values)
         if isinstance(key, ast.Constant)}
assert ast.literal_eval(rules['type']) == 'boolean'
assert ast.literal_eval(rules['default']) is False
assert isinstance(rules['coerce'], ast.Name) and rules['coerce'].id == 'normalize_boolean'
ecb_schema = json.loads((root / 'scripts/jinja2/ecbSchema.json').read_text())
ecb_rules = [group['schema']['epics.motorRecord.restoreSoftLimits']
             for group in ecb_schema.values() if isinstance(group, dict)
             and 'epics.motorRecord.restoreSoftLimits' in group.get('schema', {})]
assert len(ecb_rules) == 1
assert ecb_rules[0]['type'] == 'boolean' and ecb_rules[0]['default'] is False
print('Motor soft-limit restore modes: all four YAML combinations and legacy override passed.')
