+++
title = "EL1xxx"
weight = 17
chapter = false
+++

## EL1252, EL1252-0050
EL1252-xxxx is a 2-channel digital input terminal with timestamps (low-to-high, high-to-low):
* EL1252: **24V signals**
* EL1252-0050: **5V signals**

Both terminals have the same product ID and process data and can therefore be configured as EL1252:
```
# One channel:
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL1252"
```

These terminals are very powerful since they can latch the time of the positive edge and/or negative edge of the input signal (independent of the EtherCAT bus rate). These timestamps can then be used to correlate other data, like encoders or analog inputs with timestamps.

**IMPORTANT**
Since the EL1252-0050 is a 5V terminal, it needs to be powered with **5V**. If the terminal is powered with 24V, it will burn. The simplest way to achieve correct power supply is by adding an EL9505 (or similar) before the EL1252-0050.
See [ELxxxx](../elxxxx/) for more information about terminal power levels.

{{% notice warning %}}
**Make sure the EL1252-0050 has a 5V power supply from an EL9505 (or similar) before powering the system. If the terminal is powered with the normal 24V it will most likely break.**
{{% /notice %}}

{{% notice note %}}
A 5V signal will not be detected with the 24V version (EL1252), however the terminal will not be damaged. Furthermore, it is not a good idea to power the 24V version with 5V (EL9505, or similar).
{{% /notice %}}
