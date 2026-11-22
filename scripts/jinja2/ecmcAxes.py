import pathlib
import os
import yaml

import ecmcYamlHandler
import ecmcJinja2
import ecmcConfigValidator
import ecmcPlc


class EcmcAxis:
    axisTemplates = {
        0: 'debug.jinja2',
        1: 'axis_main.jinja2',
        2: 'axis_main.jinja2',
    }

    def __init__(self, config_file, jinja_template_dir):
        if not pathlib.Path(jinja_template_dir).is_dir():
            raise FileNotFoundError(f'template directory >> {jinja_template_dir} << not found!')
        if not pathlib.Path(config_file).is_file():
            raise FileNotFoundError(f'axis configuration >> {config_file} << not found!')

        self.config_file = config_file
        self.axisType = 1
        self.hasSyncPLC = False
        self.yamlHandler = ecmcYamlHandler.YamlHandler()
        self.axisTemplate = ecmcJinja2.JinjaTemplate(jinja_template_dir)
        # Installed Jinja family templates are flattened alongside this renderer.
        profile_root = str(pathlib.Path(__file__).resolve().parent)
        if profile_root not in self.axisTemplate.env.loader.searchpath:
            self.axisTemplate.env.loader.searchpath.append(profile_root)
        self.v = ecmcConfigValidator.ConfigValidator()
        self.plc = ecmcPlc.EcmcPlc(config_file, jinja_template_dir)
        self.data = ecmcConfigValidator.DictContainer()

    def create(self):
        """
        axis object
        """
        self.yamlHandler.loadYamlData(self.config_file, lint=True)
        self.v.document = self.yamlHandler.yamlData
        self.axisType = self.v.get_axis_type()  # obtain axis type from data, this pre-validates the 'axis' key

    def make(self):
        """
        wrapper around all steps needed to render an axis-script from a yaml-config
        """
        # Render family/variant defaults with Jinja BEFORE schema validation.
        # Python is only the existing Jinja runner and YAML parser; it does
        # not select hardware families, PDO variants or merge overrides.
        raw = self.yamlHandler.yamlData
        has_selectors = any(
            isinstance(raw.get(section), dict) and "slave" in raw[section]
            for section in ("drive", "encoder", "input")
        )
        if has_selectors:
            template = self.axisTemplate.env.get_template(
                "hwProfileResolve.jinja2")
            rendered = template.render(axis_config=raw, hardware_env=os.environ)
            resolved = yaml.safe_load(rendered)
            if "__hardware_profile_error__" in resolved:
                raise ValueError(resolved["__hardware_profile_error__"])
            self.v.document = resolved
        self.yamlHandler.yamlData = self.v.validate_axis()
        self.yamlHandler.checkForVariables()
        self.setAxisTemplate()
        if self.yamlHandler.hasVariables:
            self.axisTemplate.setTemplate(self.axisTemplate.render(self.yamlHandler.yamlData))
        self.axisTemplate.render(self.yamlHandler.yamlData)
        self.syncPLC()

    def setAxisTemplate(self, axis_type=None):
        if axis_type is None:
            axis_type = self.axisType
        self.axisTemplate.read(self.axisTemplates[axis_type])

    def syncPLC(self):
        if self.yamlHandler.checkForKey('plc', data_=self.v.document, optional=True):
            self.hasSyncPLC = True
            self.plc.create()
            self.plc.make()
            self.axisTemplate.product += self.plc.plcTemplate.product


def main():
    # axis = EcmcAxis('pytest/yaml_files/joint.yaml', './templates/')
    # axis = EcmcAxis('pytest/yaml_files/joint_all.yaml', './templates/')
    # axis = EcmcAxis('pytest/yaml_files/endEffector.yaml', './templates/')
    # axis = EcmcAxis('./test/testEndEffector.yaml', './templates/')
    # axis = EcmcAxis('./test/testJoint.yaml', './templates/')
    # axis = EcmcAxis('pytest/yaml_files/joint_benchmark.yaml', './templates/')
    axis = EcmcAxis('pytest/yaml_files/joint_sandbox.yaml', './templates/')
    axis.create()
    axis.make()

    axis.axisTemplate.showProduct()


if __name__ == '__main__':
    main()
