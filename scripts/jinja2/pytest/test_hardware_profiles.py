"""Profiles are opt-in; rendering must match equivalent explicit configuration.

Set PROFILE_TOOL to the standalone C++ generator and ECB_BIN to an unchanged
ecb binary to run native generation and rendering checks.
"""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'scripts/jinja2'
sys.path.insert(0, str(BASE))
from ecmcHardwareProfiles import resolve_profiles
from ecmcAxes import EcmcAxis
from ecmcEnc import EcmcEnc


def drive(name='EL7041', **extra):
    return {'profile': f'beckhoff/{name}/CSV', 'slave': 3, 'maxVelocity': 10, **extra}


def encoder(**extra):
    return {'profile': 'beckhoff/EL7062/incremental', 'slave': 3,
            'countsPerMotorRev': 4000, 'unitsPerMotorRev': 360, **extra}


def test_no_profile_unchanged_and_independent():
    old = {'drive': {'type': 0, 'error': [3]}, 'encoder': {'position': 'custom'}}
    new = resolve_profiles(old, {})  # no catalogue needed
    assert new == old
    new['drive']['error'].append(7)
    assert old['drive']['error'] == [3]


def test_el7041_defaults_and_overrides():
    document = {'drive': drive(error=[14], enable=5, denominator=123)}
    original = deepcopy(document)
    resolved = resolve_profiles(document)
    assert document == original
    assert resolved['axis']['mode'] == 'CSV'
    assert resolved['drive'] == {
        'type': 0, 'numerator': 10, 'denominator': 123,
        'control': 'ec0.s3.driveControl01', 'status': 'ec0.s3.driveStatus01',
        'setpoint': 'ec0.s3.velocitySetpoint01', 'enable': 5, 'enabled': 1,
        'reset': 1, 'reduceTorque': 2, 'reduceTorqueEnable': True, 'warning': 2, 'error': [14]}


def test_ds402_and_macro_addresses():
    resolved = resolve_profiles({'drive': drive('EL7062', slave='${DRV_SID}', master=1, channel=2)})['drive']
    assert resolved['type'] == 1
    assert resolved['denominator'] == 2147483648
    assert resolved['control'] == 'ec1.s${DRV_SID}.driveControl02'
    assert 'error' not in resolved and 'enable' not in resolved


@pytest.mark.parametrize('method,seq', [('low-limit-index', 11), ('high-limit-index', 12)])
def test_homing(method, seq):
    resolved = resolve_profiles({'encoder': encoder(channel=2, homing={'method': method, 'position': 4})})['encoder']
    assert resolved['type'] == 0 and resolved['bits'] == 32
    assert resolved['numerator'] == 360 and resolved['denominator'] == 4000
    assert resolved['position'] == 'ec0.s3.positionActual02_2'
    assert resolved['control'] == 'ec0.s3.touchProbeControl02'
    assert resolved['status'] == 'ec0.s3.touchProbeStatus02'
    assert resolved['latch'] == {'position': 'ec0.s3.touchProbePositionPos02_1',
                                 'control': 0, 'status': 1, 'armCmd': 17, 'armBits': 5}
    assert resolved['homing'] == {'type': seq, 'latchCount': 1, 'position': 4}


def test_no_implicit_homing_and_explicit_scaling_wins():
    resolved = resolve_profiles({'encoder': encoder(numerator=-1, denominator=100)})['encoder']
    assert resolved['numerator'] == -1 and resolved['denominator'] == 100
    assert 'homing' not in resolved and 'latch' not in resolved


@pytest.mark.parametrize('document,match', [
    ({'drive': drive(profile='unknown')}, 'Unknown drive profile'),
    ({'drive': drive(channel=2)}, 'Unsupported channel'),
    ({'drive': drive(), 'input': {'home': {'driveInput': 3}}}, 'Unsupported driveInput'),
    ({'drive': drive(), 'input': {'home': {'driveInput': True}}}, 'Unsupported driveInput'),
    ({'drive': drive(), 'input': {'limit': 'bad'}}, 'input.limit must be a mapping'),
    ({'drive': drive(channel=True)}, 'Unsupported channel'),
    ({'drive': drive(slave=None)}, 'slave'),
    ({'drive': drive(maxVelocity=0)}, 'positive'),
    ({'drive': drive(maxVelocity=float('nan'))}, 'positive'),
    ({'drive': drive(maxVelocity='${SPEED}')}, 'positive'),
    ({'axis': {'mode': 'CSP'}, 'drive': drive()}, 'requires axis.mode'),
    ({'drive': {'profile': 'beckhoff/EL7041/CSV', 'slave': 3}}, 'numerator'),
    ({'encoder': encoder(homing={'method': 'index'})}, 'Unsupported homing'),
    ({'encoder': encoder(homing={'method': 'low-limit-index', 'type': 12})}, 'conflicts'),
])
@pytest.mark.parametrize('backend', ['python', 'ecb'])
def test_invalid(document, match, backend, tmp_path):
    if backend == 'ecb':
        binary = os.environ.get('PROFILE_TOOL')
        if not binary:
            pytest.skip('Set PROFILE_TOOL to test C++ profile rejection')
        path = tmp_path / 'invalid.yaml'
        path.write_text(yaml.safe_dump(document))
        result = subprocess.run([binary, '--profiles', str(BASE / 'hardwareProfiles.json'),
            str(path), str(tmp_path / 'invalid-expanded.yaml')], capture_output=True, text=True)
        assert result.returncode != 0
        assert match in result.stderr
        return
    with pytest.raises(ValueError, match=match):
        resolve_profiles(document)


def expand_native(path, output):
    binary = os.environ.get('PROFILE_TOOL')
    if not binary:
        pytest.skip('Set PROFILE_TOOL to test native generation')
    subprocess.run([binary, '--profiles', str(BASE / 'hardwareProfiles.json'),
                    str(path), str(output)], check=True, capture_output=True, text=True)
    return output


def render_python(document, schema, path):
    path.write_text(yaml.safe_dump(document))
    obj = (EcmcAxis if schema == 'axis' else EcmcEnc)(path, BASE / 'templates')
    obj.create()
    obj.make()
    return (obj.axisTemplate if schema == 'axis' else obj.encTemplate).product


def commands(text):
    # Ignore metadata, comments and formatting; preserve command ordering/values.
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


@pytest.mark.parametrize('schema', ['axis', 'encoder'])
@pytest.mark.parametrize('backend', ['python', 'ecb'])
@pytest.mark.parametrize('drive_model', ['EL7041', 'EL7062'])
@pytest.mark.parametrize('homing', [{'method': 'low-limit-index'}, {'type': 1}, {'type': 7}])
def test_render_equivalent_to_explicit(schema, backend, drive_model, homing, tmp_path):
    document = {'encoder': encoder(homing={**homing, 'position': 0})}
    if schema == 'axis':
        document.update({'axis': {'id': 1}, 'drive': drive(drive_model),
                         'trajectory': {'axis': {'velocity': 1, 'acceleration': 2}},
                         'monitoring': {'velocity': {'enable': False, 'max': 10,
                                                     'time': {'trajectory': 100, 'drive': 200}}},
                         'input': {'home': {'driveInput': 1}, 'interlock': 'ec0.s3.ONE.0'}})
    explicit = resolve_profiles(document)
    if backend == 'python':
        a = render_python(document, schema, tmp_path / 'profile.yaml')
        b = render_python(explicit, schema, tmp_path / 'explicit.yaml')
    else:
        binary = os.environ.get('ECB_BIN')
        if not binary:
            pytest.skip('Set ECB_BIN to test native ecb rendering')
        def render(data, name):
            path = tmp_path / name
            path.write_text(yaml.safe_dump(data))
            path = expand_native(path, path.with_suffix('.expanded.yaml'))
            template = 'axis_main.jinja2' if schema == 'axis' else 'add_encoder.jinja2'
            return subprocess.check_output([binary, '--yaml', str(path), '--schemafile', str(BASE / 'ecbSchema.json'),
                '--schema', schema, '--template', str(BASE / 'templates' / template),
                '--templatedir', str(BASE / 'templates')], text=True)
        a, b = render(document, 'profile.yaml'), render(explicit, 'explicit.yaml')
    assert commands(a) == commands(b)
    seq = homing.get('type', 11)
    assert any('SetAxisHomeSeqId' in line and f',{seq})' in line for line in commands(a))
    if 'type' in homing:
        assert 'touchProbe' not in a
        assert 'enc.latch' not in a
        assert 'SetAxisEncHomeLatchArmControlWord' not in a


@pytest.mark.parametrize('relative,schema', [
    ('stepper_bissc/el7041_el5042/cfg/axis.yaml', 'axis'),
    ('stepper_incremental/ex7062_CSV/cfg/axis_chx.yaml', 'axis'),
    ('stepper_incremental/ex7062_CSP/cfg/enc_inc.yaml', 'encoder'),
])
@pytest.mark.parametrize('backend', ['python', 'ecb'])
def test_legacy_rendering_unchanged(relative, schema, backend, tmp_path, monkeypatch):
    path = ROOT / 'examples/PSI/best_practice/motion' / relative
    document = yaml.safe_load(path.read_text())
    if backend == 'python':
        current = render_python(document, schema, tmp_path / 'legacy.yaml')
        import ecmcAxes
        import ecmcEnc
        monkeypatch.setattr(ecmcAxes, 'resolve_profiles', lambda data: data)
        monkeypatch.setattr(ecmcEnc, 'resolve_profiles', lambda data: data)
        previous = render_python(document, schema, tmp_path / 'legacy.yaml')
    else:
        binary = os.environ.get('ECB_BIN')
        if not binary:
            pytest.skip('Set ECB_BIN for legacy comparison')
        expanded = expand_native(path, tmp_path / 'legacy-expanded.yaml')
        assert yaml.safe_load(expanded.read_text()) == document
        template = 'axis_main.jinja2' if schema == 'axis' else 'add_encoder.jinja2'
        outputs = [subprocess.run([binary, '--yaml', str(path), '--schemafile',
            str(BASE / 'ecbSchema.json'), '--schema', schema, '--template',
            str(BASE / 'templates' / template), '--templatedir', str(BASE / 'templates')],
            capture_output=True, text=True) for path in (path, expanded)]
        current, previous = [(r.returncode, r.stdout, r.stderr) for r in outputs]
    assert current == previous


@pytest.mark.parametrize('relative,schema', [
    ('el7041_el5042/cfg/axis.yaml', 'axis'),
    ('el7062_csv/cfg/axis.yaml', 'axis'),
    ('el7062_csv/cfg/encoder.yaml', 'encoder'),
    ('el7062_csv/cfg/axis_limit_home.yaml', 'axis'),
    ('el7062_csv/cfg/axis_limits_swapped.yaml', 'axis'),
])
@pytest.mark.parametrize('backend', ['python', 'ecb'])
def test_shipped_examples(relative, schema, backend, tmp_path):
    path = ROOT / 'examples/PSI/hw_profiles' / relative
    if backend == 'python':
        text = render_python(yaml.safe_load(path.read_text()), schema, tmp_path / 'example.yaml')
    else:
        binary = os.environ.get('ECB_BIN')
        if not binary:
            pytest.skip('Set ECB_BIN to test native example rendering')
        path = expand_native(path, tmp_path / 'example-expanded.yaml')
        template = 'axis_main.jinja2' if schema == 'axis' else 'add_encoder.jinja2'
        text = subprocess.check_output([binary, '--yaml', str(path), '--schemafile',
            str(BASE / 'ecbSchema.json'), '--schema', schema, '--template',
            str(BASE / 'templates' / template), '--templatedir', str(BASE / 'templates')], text=True)
    assert 'Cfg.SetAxisEncScaleNum' in text
    if 'axis_limits_swapped' in relative:
        assert 'binaryInputs01.1,"ax${ECMC_AXIS_NO}.mon.lowlim"' in text
        assert 'binaryInputs01.0,"ax${ECMC_AXIS_NO}.mon.highlim"' in text
    if 'axis_limit_home' in relative or 'axis_limits_swapped' in relative:
        assert 'Cfg.SetAxisHomeSeqId(${ECMC_AXIS_NO},1)' in text
        assert 'touchProbe' not in text and 'enc.latch' not in text
    elif 'el7062' in relative:
        assert 'Cfg.SetAxisHomeSeqId(${ECMC_AXIS_NO},11)' in text
        assert 'touchProbePositionPos01_1' in text


def test_nested_overrides_and_empty_alarm_list():
    result = resolve_profiles({'drive': drive(error=[]), 'encoder': encoder(
        homing={'method': 'low-limit-index', 'latchCount': 2},
        latch={'armCmd': 99}, slave='${channel}')})
    assert result['drive']['error'] == []
    assert result['encoder']['homing']['latchCount'] == 2
    assert result['encoder']['latch']['armCmd'] == 99
    assert result['encoder']['latch']['armBits'] == 5
    assert result['encoder']['position'] == 'ec0.s${channel}.positionActual01_2'


@pytest.mark.parametrize('model,word,bits', [('EL7041', 'driveStatus', [11, 12]),
                                           ('EL7062', 'binaryInputs', [0, 1])])
def test_digital_inputs(model, word, bits):
    channel = 1 if model == 'EL7041' else 2
    config = {'drive': drive(model, slave='${DRV_SID}', master=2, channel=channel),
              'input': {'home': {'driveInput': 2}, 'interlock': {'driveInput': 1},
                        'homePolarity': 1, 'limit': {'forwardPolarity': 0}}}
    result = resolve_profiles(config)['input']
    prefix = f'ec2.s${{DRV_SID}}.{word}{channel:02d}'
    assert result['limit']['backward'] == f'{prefix}.{bits[0]}'
    assert result['limit']['forward'] == f'{prefix}.{bits[1]}'
    assert result['home'] == f'{prefix}.{bits[1]}'
    assert result['interlock'] == f'{prefix}.{bits[0]}'
    assert result['homePolarity'] == 1
    assert result['limit']['forwardPolarity'] == 0
    config['input']['limit']['backward'] = 'ec0.s9.binaryInput01'
    config['input']['home'] = 'plcOverride'
    result = resolve_profiles(config)['input']
    assert result['limit']['backward'] == 'ec0.s9.binaryInput01'
    assert result['home'] == 'plcOverride'


def test_torque_reduction_default_and_disable():
    assert resolve_profiles({'drive': drive()})['drive']['reduceTorqueEnable'] is True
    assert resolve_profiles({'drive': drive(reduceTorqueEnable=False)})['drive']['reduceTorqueEnable'] is False


@pytest.mark.parametrize('seq', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 21, 22, 25, 26])
def test_numeric_homing_passes_through_without_latch(seq):
    document = {'encoder': encoder(homing={'type': seq, 'position': 0})}
    result = resolve_profiles(document)['encoder']
    assert result['homing'] == document['encoder']['homing']
    assert 'latch' not in result
    assert 'control' not in result and 'status' not in result


@pytest.mark.parametrize('document', [
    {'drive': drive(), 'input': {'home': {'driveInput': 2}}},
    {'encoder': encoder(homing={'type': 7})},
    {'drive': drive('EL7062', channel=2), 'encoder': encoder(
        homing={'method': 'high-limit-index'}, channel=2)},
    {'drive': drive(reduceTorqueEnable=False, error=[])},
    {'plc': {'file': './logic.plc', 'code': ['x := 1;', 'y := 2;']},
     'var': {'quoted': '001', 'macro': '${AX=1}', 'jinja': '{{ var.x }}',
             'flag': False, 'empty': None, 'value': 0.5}},
])
def test_native_data_matches_python(document, tmp_path):
    path = tmp_path / 'source.yaml'
    path.write_text(yaml.safe_dump(document))
    output = expand_native(path, tmp_path / 'output.yaml')
    assert yaml.safe_load(output.read_text()) == resolve_profiles(document)


def test_native_anchors(tmp_path):
    path = tmp_path / 'anchors.yaml'
    path.write_text('var: &settings {flag: false, number: 42}\ncopy: *settings\n')
    output = expand_native(path, tmp_path / 'expanded.yaml')
    assert yaml.safe_load(output.read_text()) == yaml.safe_load(path.read_text())


def test_native_failure_preserves_files(tmp_path):
    binary = os.environ.get('PROFILE_TOOL')
    if not binary:
        pytest.skip('Set PROFILE_TOOL to test C++ CLI')
    path = tmp_path / 'source.yaml'
    output = tmp_path / 'existing.yaml'
    source = 'drive: {profile: unknown, slave: 1}\n'
    path.write_text(source)
    output.write_text('previous output')
    for dest in (output, path):
        result = subprocess.run([binary, '--profiles', str(BASE / 'hardwareProfiles.json'),
            str(path), str(dest)], capture_output=True, text=True)
        assert result.returncode != 0
        assert path.read_text() == source
        assert output.read_text() == 'previous output'



def test_native_boolean_case_and_quoted_strings(tmp_path):
    path = tmp_path / 'literals.yaml'
    path.write_text('var: {a: True, b: FALSE, c: "True", d: Null, e: "001"}\n')
    output = expand_native(path, tmp_path / 'expanded.yaml')
    assert yaml.safe_load(output.read_text()) == yaml.safe_load(path.read_text())


def test_native_bad_yaml_is_reported_without_abort(tmp_path):
    binary = os.environ.get('PROFILE_TOOL')
    if not binary:
        pytest.skip('Set PROFILE_TOOL to test C++ parser errors')
    path = tmp_path / 'broken.yaml'
    path.write_text('encoder: [unterminated\n')
    output = tmp_path / 'previous.yaml'
    output.write_text('previous output')
    result = subprocess.run([binary, '--profiles', str(BASE / 'hardwareProfiles.json'),
                             str(path), str(output)], capture_output=True, text=True)
    assert result.returncode == 1  # error, not a terminating signal
    assert 'YAML error' in result.stderr
    assert output.read_text() == 'previous output'


def test_native_legacy_text_is_unchanged(tmp_path):
    source = '# retain comments and formatting\nencoder: {position: ec0.s3.positionActual01}\n'
    path = tmp_path / 'legacy.yaml'
    path.write_text(source)
    output = expand_native(path, tmp_path / 'nested' / 'legacy.yaml')
    assert output.read_bytes() == path.read_bytes()
