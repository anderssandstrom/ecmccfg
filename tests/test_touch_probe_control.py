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

    def test_power_hold_is_per_encoder_and_shares_control_with_probe(self):
        source = (ROOT/'db/core/ecmcEnc.db').read_text()
        records = dict(re.findall(r'record\(\w+,"[^"\n]*-Enc0\$\(ENC_NO\)-(ForceOn(?:-RB)?)"\)\{(.*?)\n\}', source, re.S))
        self.assertEqual(set(records), {'ForceOn', 'ForceOn-RB'})
        for body in records.values():
            self.assertIn('field(DTYP, "asynUInt32Digital")', body)
            self.assertIn('$(ADDR),0x8,$(TIMEOUT)', body)
            self.assertIn('/ax$(AXIS_NO).enc.control$(ENC_NO)?', body)
        self.assertIn('field(SCAN, "I/O Intr")', records['ForceOn-RB'])
        self.assertNotIn('-EncForceOn', (ROOT/'db/core/ecmcAxis.db').read_text())

    def test_encoder_details_panels_expose_their_own_power_hold(self):
        for filename in ('ecmcAxisEncExpert.ui', 'ecmcAxisEncExpert_v1.ui'):
            document = ET.parse(ROOT/'qt'/filename)
            channels = {p.findtext('string') for p in document.findall('.//property[@name="channel"]')}
            for suffix in ('ForceOn', 'ForceOn-RB'):
                self.assertIn('$(DEV):$(Axis)-Enc$(ENC_ID)-'+suffix, channels)
            widgets = document.findall('.//widget')
            self.assertEqual(len(widgets), len({w.get('name') for w in widgets}))
            # The added row and existing bottom group stay inside their parents.
            for parent in widgets:
                rect = parent.find('property[@name="geometry"]/rect')
                if rect is None: continue
                for child in parent.findall('widget'):
                    if child.get('name') not in ('encoderPowerHold', 'encoderPowerHoldLabel',
                                                  'encoderPowerHoldAccepted', 'groupBox_4'): continue
                    box = child.find('property[@name="geometry"]/rect')
                    self.assertLessEqual(int(box.findtext('y'))+int(box.findtext('height')), int(rect.findtext('height')))
        for filename in ('ecmcAxisExpert.ui', 'ecmcAxisCntrlStatWd.ui'):
            self.assertNotIn('-EncForceOn', (ROOT/'qt'/filename).read_text())

    def test_fixture_does_not_arm_the_probe_at_startup(self):
        source = (ROOT/'tests/integration/slit/ioc/startup.cmd').read_text()
        self.assertNotIn('AxisTouchProbeArm(', source)


if __name__ == '__main__': unittest.main()
