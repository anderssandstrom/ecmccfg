"""Opt-in expansion of hardware profiles into the legacy axis/encoder schema.

Keep semantics in sync with src/ecmcHardwareProfilesInternal.h. The shared JSON catalogue is
installed beside this module and ecbSchema.json; no hardware settings are written.
"""
from copy import deepcopy
import json
import math
from pathlib import Path

CATALOGUE = Path(__file__).with_name('hardwareProfiles.json')


def _merge(defaults, explicit):
    result = deepcopy(defaults)
    for key, value in explicit.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _expand(value, prefix, channel):
    if isinstance(value, dict):
        return {k: _expand(v, prefix, channel) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v, prefix, channel) for v in value]
    if isinstance(value, str):
        return value.replace('{channel}', channel).replace('{prefix}', prefix)
    return value


def _positive(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be a finite positive number (expand macros first)')
    return value



def _resolve_inputs(inputs, digital_inputs):
    """Resolve explicit selectors only; ordinary links and polarity stay intact."""
    result = deepcopy(inputs)
    if not isinstance(result, dict):
        raise ValueError('input must be a mapping')
    targets = [(result, 'home'), (result, 'interlock')]
    if 'limit' in result:
        if not isinstance(result['limit'], dict):
            raise ValueError('input.limit must be a mapping')
        targets += [(result['limit'], 'forward'), (result['limit'], 'backward')]
    for parent, key in targets:
        value = parent.get(key)
        if isinstance(value, dict):
            number = value.get('driveInput')
            if (set(value) != {'driveInput'} or isinstance(number, bool)
                    or not isinstance(number, int) or str(number) not in digital_inputs):
                raise ValueError(f'Unsupported driveInput selector: {value}')
            parent[key] = digital_inputs[str(number)]
    return result


def resolve_profiles(document, catalogue=None):
    """Return a copy; documents without profile selectors pass through unchanged."""
    result = deepcopy(document)
    roles = [r for r in ('drive', 'encoder')
             if isinstance(result.get(r), dict) and 'profile' in result[r]]
    if not roles:
        return result
    if catalogue is None:
        with CATALOGUE.open() as stream:
            catalogue = json.load(stream)
    if catalogue.get('version') != 1:
        raise ValueError('Unsupported hardware profile catalogue version')
    for role in roles:
        explicit = result[role]
        name = explicit.pop('profile')
        if not isinstance(name, str) or name not in catalogue[role]:
            raise ValueError(f'Unknown {role} profile: {name}')
        profile = catalogue[role][name]
        slave = explicit.pop('slave', None)
        master = explicit.pop('master', 0)
        channel = explicit.pop('channel', 1)
        for value, key in ((slave, 'slave'), (master, 'master')):
            if isinstance(value, bool) or not isinstance(value, (int, str)) or str(value) == '' or (isinstance(value, int) and value < 0):
                raise ValueError(f'{role}.{key} must be a non-negative integer or macro string')
        if isinstance(channel, bool) or not isinstance(channel, int) or channel not in profile['channels']:
            raise ValueError(f'Unsupported channel for {name}: {channel}')
        defaults = _expand(profile['defaults'], f'ec{master}.s{slave}', f'{channel:02d}')
        if role == 'drive':
            axis = result.setdefault('axis', {})
            if str(axis.get('mode', profile['mode'])).upper() != profile['mode']:
                raise ValueError(f'{name} requires axis.mode={profile["mode"]}')
            axis.setdefault('mode', profile['mode'])
            input_defaults = profile.get('inputDefaults', {})
            digital_inputs = _expand(profile.get('digitalInputs', {}), f'ec{master}.s{slave}', f'{channel:02d}')
            if input_defaults or 'input' in result:
                if not isinstance(result.get('input', {}), dict):
                    raise ValueError('input must be a mapping')
                result['input'] = _resolve_inputs(_merge(input_defaults, result.get('input', {})), digital_inputs)
            if 'maxVelocity' in explicit:
                defaults['numerator'] = _positive(explicit.pop('maxVelocity'), 'drive.maxVelocity')
        else:
            if 'countsPerMotorRev' in explicit:
                defaults['denominator'] = _positive(explicit.pop('countsPerMotorRev'), 'encoder.countsPerMotorRev')
                defaults['numerator'] = _positive(explicit.pop('unitsPerMotorRev', 1), 'encoder.unitsPerMotorRev')
            elif 'unitsPerMotorRev' in explicit:
                raise ValueError('encoder.unitsPerMotorRev requires countsPerMotorRev')
            homing = explicit.get('homing', {})
            if isinstance(homing, dict) and 'method' in homing:
                method = homing.pop('method')
                if not isinstance(method, str) or method not in profile.get('homing', {}):
                    raise ValueError(f'Unsupported homing method for {name}: {method}')
                seq = profile['homing'][method]
                if 'type' in homing and homing['type'] != seq:
                    raise ValueError('encoder.homing.type conflicts with method')
                defaults = _merge(defaults, _expand(profile['index'], f'ec{master}.s{slave}', f'{channel:02d}'))
                defaults['homing'] = {'type': seq, 'latchCount': 1}
        result[role] = _merge(defaults, explicit)
        for key in ('numerator', 'denominator'):
            if key not in result[role]:
                raise ValueError(f'{role}.{key} is required: provide explicit scaling or profile scaling inputs')
    return result


if __name__ == '__main__':
    import argparse
    import sys
    import yaml

    parser = argparse.ArgumentParser(description='Expand hardware profiles into legacy YAML (before schema defaults).')
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    with args.file.open() as stream:
        yaml.safe_dump(resolve_profiles(yaml.safe_load(stream)), sys.stdout, sort_keys=False)
