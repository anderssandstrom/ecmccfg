import pytest
import yaml
import cerberus

import ecmcYamlSchema
import ecmcConfigValidator

base_path = 'scripts/jinja2/'
templates_path = f'{base_path}templates/'
yaml_path = f'{base_path}pytest/yaml_files/'


@pytest.fixture
def myValidator():
    file = f'{yaml_path}joint_all.yaml'
    with open(file) as f:
        doc = yaml.load(f, Loader=yaml.FullLoader)
    validator = ecmcConfigValidator.ConfigValidator()
    validator.document = doc
    return validator


def test_config_validator_init(myValidator):
    assert type(myValidator) == ecmcConfigValidator.ConfigValidator


def test_config_validator_validate(myValidator):
    with pytest.raises(cerberus.SchemaError):   # schema wasn't specified
        myValidator.validate()
    with pytest.raises(SyntaxError):            # type(3.14) != int
        myValidator.validate(document={'test': 3.14}, schema={'test': {'type': 'integer'}}, strict=True)
    assert type(myValidator.validate(document={'test': 314}, schema={'test': {'type': 'integer'}})) == dict
    myValidator.v.schema = {'test': {'type': 'integer'}}
    assert myValidator.validate(document={'test': 314})['test'] == 314


def test_get_axis_type(myValidator):
    myValidator.document['axis']['type'] = 'joint'
    assert myValidator.get_axis_type() == 1
    myValidator.document['axis']['type'] = 'endeffector'
    assert myValidator.get_axis_type() == 2
    myValidator.document['axis']['type'] = 'debug'
    assert myValidator.get_axis_type() == 0
    myValidator.document['axis']['type'] = 'D e B u G'
    assert myValidator.get_axis_type() == 0
    myValidator.document['axis']['type'] = 'NotImplementedError'
    with pytest.raises(NotImplementedError):
        myValidator.get_axis_type()


def test_slave_control_deadband_belongs_to_target(myValidator):
    monitoring_schema = myValidator.Schema.monitoringSchema['schema']
    target_schema = monitoring_schema['target']['schema']
    lag_schema = monitoring_schema['lag']['schema']

    assert 'slaveControlDeadband' in target_schema
    assert 'slaveControlDeadband' not in lag_schema

    validator = cerberus.Validator({'monitoring': myValidator.Schema.monitoringSchema})
    valid = {
        'monitoring': {
            'target': {
                'enable': True,
                'tolerance': 0.1,
                'time': 10,
                'slaveControlDeadband': {
                    'tolerance': 0.2,
                    'time': 20,
                },
            },
        },
    }
    assert validator.validate(valid), validator.errors
