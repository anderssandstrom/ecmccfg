import pathlib
import os
import yaml

import ecmcYamlHandler
import ecmcJinja2
import ecmcConfigValidator

class EcmcEnc:
    encTemplates = 'add_encoder.jinja2'

    def __init__(self, config_file, jinja_template_dir):
        if not pathlib.Path(jinja_template_dir).is_dir():
            raise FileNotFoundError(f'template directory >> {jinja_template_dir} << not found!')
        if not pathlib.Path(config_file).is_file():
            raise FileNotFoundError(f'enc configuration >> {config_file} << not found!')

        self.config_file = config_file
        self.yamlHandler = ecmcYamlHandler.YamlHandler()
        self.encTemplate = ecmcJinja2.JinjaTemplate(jinja_template_dir)
        profile_root = str(pathlib.Path(__file__).resolve().parent)
        if profile_root not in self.encTemplate.env.loader.searchpath:
            self.encTemplate.env.loader.searchpath.append(profile_root)
        self.v = ecmcConfigValidator.ConfigValidator()        
        self.data = ecmcConfigValidator.DictContainer()

    def create(self):
        """
        enc object
        """
        self.yamlHandler.loadYamlData(self.config_file, lint=True)
        self.v.document = self.yamlHandler.yamlData

    def make(self):
        """
        wrapper around all steps needed to render an enc-script from a yaml-config
        """
        raw = self.yamlHandler.yamlData
        # Use the shared Jinja selector only for opted-in hardware profiles.
        if isinstance(raw.get("encoder"), dict) and "slave" in raw["encoder"]:
            template = self.encTemplate.env.get_template("hwProfileResolve.jinja2")
            resolved = yaml.safe_load(template.render(axis_config=raw, hardware_env=os.environ))
            if "__hardware_profile_error__" in resolved:
                raise ValueError(resolved["__hardware_profile_error__"])
            self.v.document = resolved
        self.yamlHandler.yamlData = self.v.validate_enc()  # validate the full axis schema        
        self.encTemplate.read(self.encTemplates)
        self.encTemplate.render(self.yamlHandler.yamlData)

    def setEncTemplate(self):
        self.encTemplate.read(self.encTemplates)


def main():
    enc = EcmcEnc('pytest/yaml_files/joint_sandbox.yaml', './templates/')
    enc.create()
    enc.make()
    enc.encTemplate.showProduct()


if __name__ == '__main__':
    main()
