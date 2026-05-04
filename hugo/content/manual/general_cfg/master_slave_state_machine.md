+++
title = "Master/Slave State Machine"
weight = 19
chapter = false
+++

## Scope
The native master/slave state machine is the preferred way to coordinate synchronized virtual/physical systems.

Use it when:

- one axis group should act as the master set
- another axis group should follow as the slave set
- only one side should accept commands at a time
- you want a native ecmc object instead of PLC-side state-machine logic

Typical examples are slit and mirror systems with virtual master axes and physical slave axes.

## Startup Script

Use the wrapper script:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addMasterSlaveSM.cmd \
  "NAME=Slit_SM, MST_GRP_NAME=virtualAxes, SLV_GRP_NAME=realAxes, MST_AT_TARGET_TIMEOUT=10"
```

Arguments:

- `NAME`: object name shown in PVs and overviews
- `MST_GRP_NAME`: master-group name, normally the virtual axes
- `SLV_GRP_NAME`: slave-group name, normally the physical axes
- `MST_DISABLE` (optional): auto-disable master axes when not busy
- `SLV_DISABLE` (optional): auto-disable slave axes when not busy
- `MST_AT_TARGET_TIMEOUT` (optional): timeout in seconds after all master axes have reached target before the state machine forces disable and returns to `IDLE`; default `10`, set negative to disable

If you want full control from each axis YAML instead, leave `MST_DISABLE` and `SLV_DISABLE` at `0` and configure `axis.autoEnable` per axis.

## Master AtTarget Timeout

When the state machine is in `MASTER`, all master axes must first reach `atTarget` after the last master-group motion. Once this has happened, the state machine keeps master auto-disable allowed even if an axis later drops out of `atTarget` during the disable sequence.

The `MST_AT_TARGET_TIMEOUT` setting limits how long master axes may remain enabled after that first all-master `atTarget` condition. If the timeout expires, the state machine sets an error on all master axes, disables the master and slave groups, restores the slave trajectory source to internal, and returns to `IDLE`.

The raw commands are:

```bash
Cfg.SetMstSlvAtTgtTimeout(<smIndex>,<seconds>)
GetMstSlvAtTgtTimeout(<smIndex>)
```

The default is `10` seconds. Use a negative value to disable this timeout.

## Runtime PVs

For state machine `0`, the main PVs are:

- `$(IOC):SM00-EnaCmd`
- `$(IOC):SM00-StateCmd`
- `$(IOC):SM00-Stat`
- `$(IOC):SM00-MstsAutoDsbleCmd`
- `$(IOC):SM00-SlvsAutoDsbleCmd`
- `$(IOC):SM00-DbgPrntEna`
- `$(IOC):SM00-MstGrpNam`
- `$(IOC):SM00-SlvGrpNam`

`StateCmd` supports these states:

- `IDLE`
- `SLAVE`
- `MASTER`
- `RESET`

The exact transition behavior depends on the object state and the involved axes, but in normal use the state machine decides which group should currently drive the synchronized system.

## Object List And Overview Support

Master/slave objects are also exposed through the standard linked-list summary PVs:

- `$(IOC):MCU-Cfg-SM-FrstObjId`
- `$(IOC):MCU-Cfg-SM<n>-NxtObjId`
- `$(IOC):MCU-Cfg-SM<n>-PrvObjId`

These are primarily used by overview panels and object-browser tooling.

## Recommended Usage Pattern

1. Define the synchronized axes in two axis groups, typically one virtual and one physical group.
2. Create one master/slave state machine with `addMasterSlaveSM.cmd`.
3. Send commands only through the active side of the system.
4. If a slave axis enters limit, interlock, or error, resolve that axis problem first and then reset/recover the state machine.

For most new systems, this is preferable to keeping equivalent switching logic in PLC code.

## Related Pages

- [Axis Groups]({{< relref "/manual/general_cfg/axis_groups.md" >}})
- [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [upgrades]({{< relref "/manual/upgrades.md#native-masterslave-state-machine" >}})
- [knowledgebase: tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
