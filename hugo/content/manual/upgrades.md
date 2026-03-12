+++
title = "Upgrades"
weight = 70
chapter = false
aliases = ["/manual/ecmc_versions/"]
+++

## Purpose
Collect upgrade notes and migration checklists for major versions.

## Release Notes
New features are described in ecmc `RELEASE.md`:
https://github.com/epics-modules/ecmc/blob/master/RELEASE.md

## v10 -> v11 Highlights
- CSP-PC mode added (centralized position loop in CSP)
- Position-velocity-time (profile move) support
- Motor record PID fields still limited to `0..1.0`; use values `100x` smaller than native ecmc settings

{{% notice warning %}}
Be careful when using motor record PID fields.  
Example: ecmc `Kp=1.0` corresponds to motor record `PCOF=0.01`.
{{% /notice %}}

## Breaking Changes in v11
- `getAxisStatusStructV2` removed (plugins need rebuild)
- `Event*`, `CommandList*`, `DataRecorder*` removed (replace with PLC logic)
- Motor record `MtnCmd` mbbo indices changed (prefer string writes, or update index-based clients)

## Migration Checklist (v10 -> v11)
- Auto-enable: move from motor record parameters to `axis.autoEnable` in YAML
- Master/slave synchronization: replace PLC state machine logic with native `addMasterSlaveSM.cmd`
- Limit logic: use `plcOverride` and write `ax<id>.mon.lowlim/highlim` in PLC code
- Drive safety: ensure SDO verification is executed for every used drive channel

### Auto-enable (recommended migration)
Remove legacy motor-record auto-enable parameter strings:
```txt
# remove legacy:
# parameters: 'powerAutoOnOff=2;powerOffDelay=-1;'
```

Use native ecmc auto-enable:
```yaml
axis:
  autoEnable:
    enableTimeout: 1.0
    disableTimeout: 5.0
    atStartup: false
```

### Native master/slave state machine
For virtual/physical synchronized systems, replace PLC-side state machine code with `addMasterSlaveSM.cmd`:
```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addMasterSlaveSM.cmd "NAME=Slit_SM, MST_GRP_NAME=virtualAxes, SLV_GRP_NAME=realAxes"
```

If you have multiple systems, use unique `NAME`, `MST_GRP_NAME`, and `SLV_GRP_NAME` per system.

### Limit logic via `plcOverride`
Use `plcOverride` in YAML and compute limits in PLC logic:
```yaml
input:
  limit:
    forward: 'plcOverride'
    backward: 'plcOverride'
```

```txt
plc:
  enable: true
  externalCommands: true
  code:
    - ax${AX_ID=1}.mon.lowlim:=ec_chk_bit(ec0.s$(DRV_SID).binaryInputs01,0) and ec_chk_bit(ec0.s$(DRV_SID).ONE,0);
    - ax${AX_ID=1}.mon.highlim:=ec_chk_bit(ec0.s$(DRV_SID).binaryInputs01,1) and ec_chk_bit(ec0.s$(DRV_SID).ONE,1);
```

### SDO verification for drives
v11 adds SDO verification workflow checks (mainly stepper/servo drives):
1. `addSlave.cmd` marks drive channels that require SDO setup.
2. `applyComponent.cmd` marks channels as configured after component application.
3. Validation before `iocInit` fails if required channels are missing SDO configuration.

If a multi-channel drive has an unused channel, still configure it (for example `Generic-Ch-Not-Used`).
