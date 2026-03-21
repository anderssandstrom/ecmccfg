+++
title = "Axis Groups"
weight = 18
chapter = false
+++

## Scope
Axis groups are lightweight named collections of axes.

Use them when you want to:

- address several axes as one logical set
- use the PLC `mc_grp_...` helper functions
- build synchronized virtual/physical systems
- feed the native master/slave state machine with one master group and one slave group

## Typical Ways To Create A Group

### Preferred path: YAML

For new configurations, define the group directly in the axis YAML:

```yaml
axis:
  id: 1
  group: realAxes
```

When `axis.group` is set:

- the group is created automatically if it does not already exist
- the axis is added to that group
- the resulting group id is stored in `GRP_<group>_ID`

Example:

```text
GRP_realAxes_ID
GRP_virtualAxes_ID
```

This is the normal path for current YAML-based motion setups.

### Low-level command path

For classic or scripted setups, groups can also be created explicitly:

```text
Cfg.AddAxisGroup(realAxes)
Cfg.AddAxisToGroupByName(1,realAxes,1)
```

That path is mainly useful in lower-level command-parser or classic startup flows.

## What Axis Groups Are Used For

### PLC motion-group functions

The PLC function library contains `mc_grp_...` helpers for group-level control and status, for example:

- `mc_grp_get_busy(...)`
- `mc_grp_set_enable(...)`
- `mc_grp_halt(...)`
- `mc_grp_size(...)`

Use these when your PLC logic should act on a group instead of one axis at a time.

### Native master/slave systems

Master/slave synchronization uses two groups:

- one master group, typically virtual axes
- one slave group, typically physical axes

The master/slave state machine then switches which group is active and which one follows.

See [Master/Slave State Machine]({{< relref "/manual/general_cfg/master_slave_state_machine.md" >}}).

### Summary PVs and overview panels

During the normal finalize flow, ecmccfg also exposes summary information about configured groups.

The main summary PVs are:

- `$(IOC):MCU-Cfg-AXGRP-Cnt`
- `$(IOC):MCU-Cfg-AXGRP<ID>-Nam`
- `$(IOC):MCU-Cfg-AXGRP<ID>-Axes`

These are mainly intended for overview panels, diagnostics, and operator-facing summaries.

## Recommended Usage

For new configurations:

1. Define axis membership with `axis.group` in YAML.
2. Use the generated `GRP_<group>_ID` macro if PLC code needs the numeric group id.
3. Use `mc_grp_...` PLC helpers for group-level logic.
4. If the system is a virtual/physical synchronized pair, connect the two groups with `addMasterSlaveSM.cmd`.

## Related Pages

- [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [Axis YAML settings (heading view)]({{< relref "/manual/motion_cfg/axisYamlSettingsHeadings.md" >}})
- [PLC functions]({{< relref "/manual/PLC_cfg/functions.md" >}})
- [Master/Slave State Machine]({{< relref "/manual/general_cfg/master_slave_state_machine.md" >}})
- [Synchronization examples]({{< relref "/manual/examples.md" >}})
