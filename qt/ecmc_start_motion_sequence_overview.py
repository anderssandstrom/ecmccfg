#!/usr/bin/env python3
"""Create an overview containing only configured ecmc motion sequences."""

import argparse
import html
import os
import stat
import subprocess
import tempfile


HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <property name="geometry"><rect><x>0</x><y>0</y><width>920</width><height>{height}</height></rect></property>
  <property name="windowTitle"><string>{ioc} ECMC motion sequence overview</string></property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <property name="margin"><number>4</number></property>
   <item>
    <widget class="caLabel" name="headers">
     <property name="minimumSize"><size><width>900</width><height>22</height></size></property>
     <property name="text"><string>Open          ID      State             Running        Step       Count      Error      Step name</string></property>
    </widget>
   </item>
   <item>
    <widget class="QScrollArea" name="scrollArea">
     <property name="frameShape"><enum>QFrame::NoFrame</enum></property>
     <property name="widgetResizable"><bool>true</bool></property>
     <widget class="QWidget" name="scrollAreaWidgetContents">
      <layout class="QVBoxLayout" name="sequenceLayout">
       <property name="margin"><number>0</number></property>
"""

ROW = """
       <item>
        <widget class="caInclude" name="sequence{seq_id}">
         <property name="macro"><string>IOC={ioc},SEQ_ID={seq_id},SEQ_PFX={pv_prefix}</string></property>
         <property name="filename" stdset="0"><string notr="true">ecmcMotionSequenceRow.ui</string></property>
        </widget>
       </item>
"""

FOOTER = """
       <item><spacer name="verticalSpacer"><property name="orientation"><enum>Qt::Vertical</enum></property><property name="sizeHint" stdset="0"><size><width>20</width><height>40</height></size></property></spacer></item>
      </layout>
     </widget>
    </widget>
   </item>
  </layout>
 </widget>
 <customwidgets>
  <customwidget><class>caLabel</class><extends>QLabel</extends><header>caLabel</header></customwidget>
  <customwidget><class>caInclude</class><extends>QWidget</extends><header>caInclude</header></customwidget>
 </customwidgets>
 <resources/>
 <connections/>
</ui>
"""


def get_sequences(ioc):
    import ca  # noqa: F401
    import epicsPV

    sequences = []
    seen = set()
    seq_id = int(epicsPV.epicsPV(f"{ioc}:MCU-Cfg-SEQ-FrstObjId").getw())

    while seq_id >= 0:
        if seq_id in seen:
            raise RuntimeError(f"Cycle in motion sequence configuration at ID {seq_id}")
        seen.add(seq_id)

        pv_prefix = epicsPV.epicsPV(
            f"{ioc}:MCU-Cfg-SEQ{seq_id}-Pfx"
        ).getw()
        sequences.append({"id": seq_id, "pv_prefix": str(pv_prefix)})

        seq_id = int(epicsPV.epicsPV(
            f"{ioc}:MCU-Cfg-SEQ{seq_id}-NxtObjId"
        ).getw())

    return sequences


def create_ui_file(filename, ioc, sequences):
    height = min(620, max(100, 62 + len(sequences) * 32))
    with open(filename, "w", encoding="utf-8") as output:
        output.write(HEADER.format(height=height, ioc=html.escape(ioc)))
        for sequence in sequences:
            output.write(ROW.format(
                ioc=html.escape(ioc),
                seq_id=sequence["id"],
                pv_prefix=html.escape(sequence["pv_prefix"]),
            ))
        output.write(FOOTER)

    os.chmod(
        filename,
        stat.S_IRUSR | stat.S_IWUSR |
        stat.S_IRGRP | stat.S_IWGRP |
        stat.S_IROTH | stat.S_IWOTH,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Create an overview of configured ecmc motion sequences"
    )
    parser.add_argument("ioc", help="IOC prefix without trailing colon")
    args = parser.parse_args()

    sequences = get_sequences(args.ioc)
    if not sequences:
        print("No motion sequences configured")

    filename = os.path.join(
        tempfile.gettempdir(), f"{args.ioc}_motion_sequence_overview.ui"
    )
    create_ui_file(filename, args.ioc, sequences)
    subprocess.run(["caqtdm", "-x", "-noMsg", filename], check=False)


if __name__ == "__main__":
    main()
