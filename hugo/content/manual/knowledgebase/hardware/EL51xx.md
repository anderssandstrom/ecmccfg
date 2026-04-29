+++
title = "EL51xx"
weight = 19
chapter = false
+++

## Scope
Use this page for EL51xx incremental-encoder terminals, especially slave
selection, channel mode, oversampling, and trigger/cam-capable variants.

## Overview
The EL51xx series covers incremental encoder interfaces:
1. EL5101: 1 ch, diff rs422, ttl, 1MHz
2. EL5101-0010: 1 ch, diff rs422, 5MHz
3. EL5101-0011: 1 ch, diff rs422, 5MHz, oversampling 100kHz
4. EL5102: 2ch diff rs422, 5MHz, **PSI standard**
5. EL5112: 2 ch ABC or 1 ch AB, rs422, 5MHz
6. EL5131: 1 ch, diff rs422, 5MHz, 2 digital outputs for cam/trigger
7. [Diagnostics](#diagnostics)

## General
Normally, incremental encoder interfaces do not require any SDO configuration.
Therefore, `ecmccomp/applyComponent.cmd`, which is often needed after
`ecmccfg/addSlave.cmd`, is usually not required.

## Adding the slave
Make sure you use the correct slave type when adding the slave. Some slaves have the same product ID but totally different process data, which can result in the slave not going into OP mode and ecmc failing to start with a timeout.

For example, EL5101-**0010** and EL5101-**0011** have the same product ID but very different process data.
So if an EL5101-**0011** is added to the configuration but the actual slave connected is an EL5101-**0010**, the initial product ID verification will not catch the mismatch. Later, the slave will not go online since the process data is wrong.

The issue can be diagnosed by checking the `dmesg` logs:
```bash
# first login to host (ecmc server)
sudo dmesg
```
Configuring the wrong process data leads to an error such as
`* EtherCAT * Invalid input configuration`.

The solution is to use the correct configuration script.

## EL5101-0010
This terminal is commonly used at PSI, although the EL5112 should normally be
the standard choice. For configuration, use the EL5101-0010 startup script:
```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5101-0010"
```

## EL5101-0011
This is an oversampling terminal. Use the EL5101-0011 startup script with the
optional `NELM` macro, which defines the oversampling depth.

Example: add an EL5101-0011 with `100` oversamples:
```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5101-0011, NELM=100"
```
In this example, each EtherCAT frame transfers an array of 100 elements. If the
EtherCAT rate is `1 kHz`, the incremental data is therefore sampled at
`100 kHz`, which is also the maximum rate for this terminal.

{{% notice note %}}
`NELM` cannot be freely defined; depending on the EtherCAT rate, different `NELM` values will be accepted. Consult the EL5101-0011 manual for more information.
Normally, `NELM` needs to be an integer value, like 10, 20, 50, 100.
{{% /notice %}}

## EL5102
EL5102 is PSI standard.
Issues with Firmware version Rev 1 has been identified. If the card is freshly power cycled it does not accept writing to SDOs. After bringing it to OP mode and then back to PREOP it works:
``` 
ethercat -m1 -p1 download 0x8001 0x1D 5 --type uint8
SDO transfer aborted with code 0x08000021: Data cannot be transferred or stored to the application because of local control
ethercat -m1 -p1 state OP
ethercat -m1 -p1 state PREOP
ethercat -m1 -p1 download 0x8001 0x1D 5 --type uint8
# Works
```
Upgrading firmware, (currently to Rev 4), fixes the issue.

In most situations, no SDO writes are needed when using EL5102.

## EL5112
This is the PSI standard incremental encoder terminal. It can be used in
single-channel mode if an index pulse is needed, or in two-channel mode if only
the A and B pulse trains are needed.

For one-channel operation with index pulse, use `EL5112_ABC`. For two-channel
operation, use `EL5112_AB`:
```bash
# One channel:
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5112_ABC"

# Two channel:
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5112_AB"
```

## EL5131
This terminal supports cam/trigger outputs at selected counter values for a
defined time and direction.

Eight predefined threshold values can be configured to switch outputs on or
off. These thresholds can also be accessed and updated at runtime.

Depending on the intended use, the following startup scripts are available:
* `EL5131`: normal incremental encoder operation
* `EL5131_DC`: incremental encoder operation with DC-clock timestamp access
* `EL5131_DC_TRG`: incremental encoder operation with timestamp access and
  configurable output thresholds for triggering

```bash
# EL5131: Normal incremental encoder operation:
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5131"

# EL5131_DC: Normal incremental encoder and DC clock (access to timestamps)
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5131_DC"

# EL5131_DC_TRG: Incremental encoder with timestamps and trigger-threshold configuration.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=16, HW_DESC=EL5131_DC"
```

## Diagnostics

See the hardware diagnostics page for terminal-level diagnostic data.

## Related Pages
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
- [Diagnostics]({{< relref "/manual/knowledgebase/hardware/Diag.md" >}})
- [homing]({{< relref "/manual/motion_cfg/homing.md" >}})
