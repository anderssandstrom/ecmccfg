"""Probe bit PVs share one native asyn interface and preserve public names."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class TouchProbeControlTests(unittest.TestCase):
    def test_command_and_readback_bits_share_one_digital_parameter(self):
        source = (ROOT/'db/core/ecmcEncTouchProbe.db').read_text()
        records = dict(re.findall(r'record\(\w+,"[^"\n]*-TP-([^"\n]+)"\)\{(.*?)\n\}',
                                  source, re.S))
        for names, mask in ((('EnableCmd','Enable-RB'), '0x1'),
                            (('ArmCmd','Armed'), '0x2'),
                            (('AutoRearmCmd','AutoRearm-RB'), '0x4')):
            for name in names:
                record = records[name]
                self.assertIn('field(DTYP, "asynUInt32Digital")', record)
                self.assertIn(f'$(ADDR),{mask},$(TIMEOUT)', record)
                self.assertIn('/ax$(AXIS_NO).enc.control$(ENC_NO)?', record)
        self.assertNotIn('enc.touchprobe.armcmd', source)
        self.assertNotIn('enc.touchprobe.armed', source)

    def test_optional_panel_exposes_enable_arm_and_auto_rearm(self):
        document = ET.parse(ROOT/'qt/ecmcEncTouchProbe.ui')
        channels = {prop.findtext('string') for prop in document.findall('.//property[@name="channel"]')}
        for suffix in ('EnableCmd','Enable-RB','ArmCmd','Armed','AutoRearmCmd','AutoRearm-RB'):
            self.assertIn('$(DEV):$(Axis)-Enc$(ENC_ID)-TP-'+suffix, channels)

    def test_fixture_does_not_arm_the_probe_at_startup(self):
        source = (ROOT/'tests/integration/slit/ioc/startup.cmd').read_text()
        self.assertNotIn('AxisTouchProbeArm(', source)


if __name__ == '__main__': unittest.main()
