+++
title = "PVT"
weight = 24
chapter = false
+++

## Scope
This page describes profile-move / PVT motion in ecmccfg.

Here, PVT means the asyn motor-controller profile-move workflow where:

- each participating axis provides a position array
- the controller provides the common timing array
- the profile is built, executed, and optionally read back after motion

## When To Use PVT

Use PVT when a single move should follow a precomputed trajectory instead of one
target point at a time.

Typical cases:

- scanning along a fixed point sequence
- synchronized multi-axis trajectories
- trajectories that must be prepared and checked before execution

## Configuration Overview

PVT has two parts:

1. axis-side enablement in the YAML axis config
2. controller-side PVT records created by `pvtControllerConfig.cmd`

### Axis YAML

PVT is enabled per axis in the motor-record block:

```yaml
epics:
  name: Axis1
  precision: 3
  motorRecord:
    enable: true
    pvt:
      npoints: 20
      nreadback: 20
```

Meaning:

- `epics.motorRecord.pvt.npoints`: max number of target points for this axis
- `epics.motorRecord.pvt.nreadback`: max number of readback points for this axis

When this block is present, the axis loader:

- loads axis-specific PVT PVs like `Axis1-PVT-UseAxis` and `Axis1-PVT-Positions`
- enables PVT for the axis in the motor driver
- stores the maximum sizes needed by the controller-level PVT records

## Startup Sequence

Minimal pattern:

```bash
require ecmccfg "ENG_MODE=1,MASTER_ID=0"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230,STEPS=400'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,  "FILE=./cfg/axis.yaml,DEV=${IOC},DRV_SLAVE=${ECMC_EC_SLAVE_NUM}"
${SCRIPTEXEC} ${ecmccfg_DIR}pvtControllerConfig.cmd
```

This pattern is used in:

- `examples/PSI/best_practice/motion/pvt/el7041_0052/`

## `pvtControllerConfig.cmd`

`pvtControllerConfig.cmd` creates the shared controller-side PVT records and
allocates the profile buffers in the asyn motor driver.

Important macros:

- `NPOINTS`: max number of profile points
- `NREADBACK`: max number of readback points
- `NPULSES`: max number of output pulses
- `NAXES`: number of participating axes
- `TRG_EC_ENTRY`: optional EtherCAT entry linked to the PVT trigger output
- `TRG_DUR_S`: optional pulse duration for the trigger output
- `SOFT_TRG_FLNK`: optional forward link from `PVT-SftTrg`

If these sizes are not supplied explicitly, the script uses the largest values
collected from all axes with `epics.motorRecord.pvt`.

### Automatic versus explicit configuration

If PVT is enabled for one or more axes and `pvtControllerConfig.cmd` was not
called manually, `setAppMode.cmd` will run a default `pvtControllerConfig.cmd`
automatically.

Call `pvtControllerConfig.cmd` explicitly when you need to:

- configure trigger output with `TRG_EC_ENTRY`
- override sizes manually
- configure the controller before `setAppMode.cmd`

## Main PVs

### Controller-level PVs

These PVs are created from `ecmcProfileMoveController.template` with prefix
`$(P)PVT-...`.

Important PVs:

- `PVT-NumAxes`: number of axes used in the profile
- `PVT-NumPoints`: number of profile points
- `PVT-NumPulses`: number of output pulses
- `PVT-StartPulses`: point index where trigger pulses start
- `PVT-EndPulses`: point index where trigger pulses stop
- `PVT-TimeMode`: fixed time or array time mode
- `PVT-FixedTime`: fixed time per point
- `PVT-Times`: time array
- `PVT-MoveMode`: absolute or relative move
- `PVT-Build`: build/check the profile
- `PVT-BuildState`, `PVT-BuildStatus`, `PVT-BuildMessage`: build diagnostics
- `PVT-Execute`: execute the built profile
- `PVT-ExecuteState`, `PVT-ExecuteStatus`, `PVT-ExecuteMessage`: execution diagnostics
- `PVT-Abort`: abort profile execution
- `PVT-Readback`: request profile readback arrays
- `PVT-ReadbackState`, `PVT-ReadbackStatus`, `PVT-ReadbackMessage`: readback diagnostics
- `PVT-SftTrg`: software trigger helper record

### Axis-level PVs

These PVs are created for each PVT-enabled axis from
`ecmcProfileMoveAxis.template`.

Important PVs:

- `<Axis>-PVT-UseAxis`: include this axis in the profile
- `<Axis>-PVT-Positions`: target positions for this axis
- `<Axis>-PVT-Readbacks`: actual readback positions after readback
- `<Axis>-PVT-FollowingErrors`: following-error array after readback

## Minimal Workflow

Typical sequence from EPICS:

1. Set `PVT-NumPoints`
2. Set `PVT-NumPulses` and optionally `PVT-StartPulses` / `PVT-EndPulses`
3. Select `PVT-TimeMode`
4. If using array timing, write `PVT-Times`
5. For each participating axis, set `<Axis>-PVT-UseAxis=1`
6. Write `<Axis>-PVT-Positions`
7. Set `PVT-Build=1` and verify `PVT-BuildStatus`
8. Set `PVT-Execute=1`
9. Optionally set `PVT-Readback=1` and inspect `<Axis>-PVT-Readbacks`

Example:

```sh
caput IOC:PVT-NumPoints 7
caput IOC:PVT-NumPulses 5
caput IOC:PVT-MoveMode 0
caput IOC:Axis1-PVT-UseAxis 1
caput -a IOC:Axis1-PVT-Positions "0 360 720 1080 1440 1080 720"
caput -a IOC:PVT-Times "1 2 2 1 5 1 1"
caput IOC:PVT-Build 1
caput IOC:PVT-Execute 1
```

Notes:

- `PVT-MoveMode=0` means absolute mode.
- In fixed-time mode, `PVT-FixedTime` is used instead of the `PVT-Times` array.
- Build and execute are separate steps.

## Trigger Output

If `TRG_EC_ENTRY` is configured in `pvtControllerConfig.cmd`, the PVT controller
can drive an EtherCAT output during the profile.

Use this when the motion profile must emit synchronized trigger pulses to
external hardware.

Relevant settings:

- `TRG_EC_ENTRY`: output bit or entry to link to the PVT trigger object
- `TRG_DUR_S`: trigger pulse duration
- `PVT-StartPulses`, `PVT-EndPulses`, `PVT-NumPulses`: pulse placement/count

## Current Documentation Gaps

PVT support exists in the codebase and templates, but it is still only lightly
covered elsewhere in the manual.

The axis YAML keys `epics.motorRecord.pvt.npoints` and
`epics.motorRecord.pvt.nreadback` are documented in the YAML reference and
should be considered required for YAML-based PVT setup.

The preferred example to start from is:

- `examples/PSI/best_practice/motion/pvt/el7041_0052/`

## Related Pages

- [Motor Record]({{< relref "/manual/motion_cfg/motor.md" >}})
- [Axis YAML]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
