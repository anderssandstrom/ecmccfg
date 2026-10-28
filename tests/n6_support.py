"""Command capture for N6 hardware and cross-repository component checks."""
from pathlib import Path
import re
import subprocess
import tempfile
from unittest.mock import patch

import test_ex72xx_opt as harness

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / 'hardware/Nanotec'
COMP = ROOT.parent / 'ecmccomp'
FIXTURES = ROOT / 'tests/fixtures/n6'


def hardware_commands(model='N6-1-1-1-S_OPT', options=None, slave=3, master=0):
    startup = harness.Startup.__new__(harness.Startup)
    startup.env = dict(SCRIPTEXEC='iocshLoad', ecmccfg_DIR='', ECMC_P='TEST:',
                       ECMC_EC_SLAVE_NUM=str(slave), ECMC_EC_MASTER_ID=str(master), HW_DESC=model)
    startup.commands, startup.templates, startup.substitutions = [], [], []
    read_text = Path.read_text

    def source(path, *args, **kwargs):
        # The shared harness stubs verification. The unchanged file-existence
        # and watchdog operations are not executed against hardware here.
        return '\n'.join(line for line in read_text(path, *args, **kwargs).splitlines()
                         if not line.lstrip().startswith('ecmcFileExist(')
                         and 'ecmcWatchDog.cmd' not in line)

    with patch.object(harness, 'HW', HW), patch.object(Path, 'read_text', source):
        startup.run(HW / f'ecmc{model}.cmd', options or {})
    return startup


class PositionOutput(harness.Startup):
    """Run real N6 SDO scripts and new component validation, capturing commands.

    This deliberately does not emulate the entire generic applyComponent
    loader or the existing motor validator. The new component's macro-name
    validation uses the actual shell validator and its generated IOC script.
    """
    def __init__(self, hardware=None, slave=3, master=0):
        self.env = dict(hardware.env) if hardware else {}
        self.env.update(ECMC_EC_MASTER_ID=str(master))
        self.slave = str(slave)
        self.commands, self.templates, self.substitutions = [], [], []

    def motor(self, invert='0', options=None):
        self.commands = []
        self.env.update(COMP_S_ID=self.slave, CH_ID='1', I_MAX_MA_VALID='400',
                        I_STDBY_MA_VALID='100', MOT_STEPS='200', INV_DIR=str(invert))
        # Only normalize the logging variant of this one existing command so
        # the shared capture parser accepts it. It is never executed.
        read_text = Path.read_text
        def source(path, *args, **kwargs):
            return read_text(path, *args, **kwargs).replace(
                'ecmcConfig "Cfg.EcSetSlaveSDOSettingsDone(',
                'ecmcConfigOrDie "Cfg.EcSetSlaveSDOSettingsDone(')
        with patch.object(Path, 'read_text', source):
            self.run(COMP / 'drive_slaves/hw_sdo_scripts/N6_SDOS_2PH_STEPPER.cmd',
                     {key: str(value) for key, value in (options or {}).items()})
        return list(self.commands)

    def apply(self, options=None, channel='1', comp_type='N6'):
        options = {key: str(value) for key, value in (options or {}).items()}
        self.commands = []
        self.env.update(COMP_S_ID=self.slave, CH_ID=str(channel), EC_COMP_TYPE=comp_type)
        self.run(COMP / 'drive_slaves/Drive-Generic-PositionOutput.cmd', {})
        self.run(COMP / 'drive_slaves/N6_POSITION_OUTPUT.cmd', {})
        self.run(COMP / 'scripts/support/validateGeneric.cmd', {})
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / 'valid.cmd'
            subprocess.run(['bash', str(COMP / 'scripts/support/validateMacros.sh'),
                            ','.join(f'{key}={value}' for key, value in options.items()),
                            self.env['SUPP_MACROS'], str(generated)],
                           capture_output=True, text=True, check=False, timeout=5)
            self.run(generated, {})
        self.run(COMP / 'scripts/support/validatePOSITION_OUTPUT.cmd', options)
        self.run(COMP / 'drive_slaves/hw_sdo_scripts/N6_SDOS_POSITION_OUTPUT.cmd', options)
        self.run(COMP / 'scripts/support/cleanupPOSITION_OUTPUT.cmd', {})
        self.run(COMP / 'scripts/support/cleanupGeneric.cmd', {})
        return list(self.commands)


def settings(commands):
    result = {}
    for command in commands:
        match = re.fullmatch(r'Cfg.EcAddSdo\((.*)\)', command)
        if match:
            slave, index, sub, value, size = (int(value, 0) for value in match[1].split(','))
            result[index, sub] = (value, size)
    return result
