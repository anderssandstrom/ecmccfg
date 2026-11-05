"""PVT controller/trigger conditionals must preserve the caller's branch macros."""
from pathlib import Path
import re
import shlex
import unittest

from test_ex72xx_opt import arguments, expand, expression

ROOT = Path(__file__).resolve().parents[1]


class PVTScript:
    def __init__(self, configured, axes, trigger):
        self.env = dict(SCRIPTEXEC='iocshLoad', ECMC_CONFIG_ROOT='',
                        ECMC_MOTOR_PORT='MOTOR', ECMC_ASYN_PORT='ECMC',
                        ECMC_PREFIX='TEST:', ECMC_EC_SAMPLE_RATE_MS='1',
                        ECMC_MR_PVT_CONTROLLER_CONFIGURED=str(configured),
                        ECMC_MR_PVT_AXES_COUNT_IN_USE=str(axes),
                        ECMC_MR_PVT_MAX_RB_POINTS_IN_USE='256',
                        ECMC_MR_PVT_MAX_POINTS_IN_USE='64',
                        IF_TRUE='#parent-true', IF_FALSE='#parent-false')
        if trigger:
            self.env.update(TRG_EC_ENTRY='ec0.s5.binaryOutput05.0', TRG_DUR_S='.4')
        self.calls, self.loads = [], 0

    def run(self, source):
        for raw in source.splitlines():
            if not raw.strip() or raw.lstrip().startswith('#'):
                continue
            line = expand(raw, self.env).strip()
            if line.startswith('#'):
                continue
            match = re.fullmatch(r'(\w+)\((.*)\)', line)
            if match:
                command, args = match[1], arguments(match[2])
                if command == 'epicsEnvSet':
                    self.env[args[0]] = args[1]
                elif command == 'epicsEnvUnset':
                    self.env.pop(args[0], None)
                elif command == 'ecmcEpicsEnvSetCalcTernary':
                    self.env[args[0]] = args[2] if expression(args[1]) else args[3]
                elif command == 'ecmcEpicsEnvSetCalc':
                    self.env[args[0]] = format(expression(args[1]), '.15g')
                else:
                    assert command in ('ecmcCreateProfile', 'ecmcFileExist', 'dbLoadRecords'), line
                    self.calls.append((command, args))
                continue
            words = shlex.split(line)
            if words[0] == 'iocshLoad':
                assert words[1] == 'pvtControllerConfig.cmd', line
                self.loads += 1
                self.run((ROOT/'scripts/pvtControllerConfig.cmd').read_text())
            else:
                assert words[0] == 'ecmcConfigOrDie', line
                self.calls.append((words[0], words[1:]))


class PVTStartupTests(unittest.TestCase):
    def test_auto_configuration_and_trigger_branches_preserve_parent_scope(self):
        source = (ROOT/'scripts/setAppMode.cmd').read_text()
        block = source.split('#- Load pvt controller records', 1)[1].split('\n', 1)[1].split(
            '# EtherCAT bus startup delay', 1)[0]
        for configured in (0, 1):
            for axes in (0, 4):
                for trigger in (False, True):
                    with self.subTest(configured=configured, axes=axes, trigger=trigger):
                        script = PVTScript(configured, axes, trigger)
                        script.run(block)
                        automatic = not configured and axes > 0
                        self.assertEqual(script.loads, int(automatic))
                        profiles = [args for command, args in script.calls if command == 'ecmcCreateProfile']
                        self.assertEqual(profiles, [['MOTOR', '256']] if automatic else [])
                        commands = [args[0] for command, args in script.calls if command == 'ecmcConfigOrDie']
                        self.assertEqual(commands, [
                            'Cfg.LinkEcEntryToObject(ec0.s5.binaryOutput05.0,pvtctrl.trigger.output)',
                            'Cfg.SetPVTControllerTrgDurMs(400)'] if automatic and trigger else [])
                        self.assertEqual(script.env['IF_TRUE'], '#parent-true')
                        self.assertEqual(script.env['IF_FALSE'], '#parent-false')
                        self.assertNotIn('ECMC_PVT_AUTO_CFG_CMD', script.env)
                        self.assertNotIn('ECMC_PVT_TRIGGER_CFG_CMD', script.env)
                        self.assertNotIn('ECMC_MR_PVT_CONTROLLER_CONFIGURED', script.env)
                        for name in ('ECMC_MR_PVT_MAX_RB_POINTS_IN_USE',
                                     'ECMC_MR_PVT_MAX_POINTS_IN_USE',
                                     'ECMC_MR_PVT_AXES_COUNT_IN_USE'):
                            self.assertEqual(name not in script.env, bool(automatic))


if __name__ == '__main__': unittest.main()
