+++
title = "RT SDO Objects"
weight = 15
chapter = false
+++

## Scope
Use RT SDO objects when you need on-demand access to one EtherCAT SDO while the
IOC is already running in realtime.

This is useful for:
- reading one diagnostic or configuration register during operation
- writing one non-cyclic setting without rebuilding the full slave setup
- exposing one SDO as a small EPICS control object with read/write commands

This page documents the `addEcSdoRT.cmd` wrapper around
`Cfg.EcAddSdoAsync(...)`.

## What It Creates

`addEcSdoRT.cmd` creates one named asynchronous SDO object in ecmc and then
loads EPICS records for it.

For a name like `HW_ENABLE`, the underlying asyn object path becomes:

```text
ec<master>.s<slave>.sdo.HW_ENABLE
```

The script then creates these PVs:
- `...SDO-HW_ENABLE-Val`
- `...SDO-HW_ENABLE-RdCmd`
- `...SDO-HW_ENABLE-WrtCmd`
- `...SDO-HW_ENABLE-Bsy`
- `...SDO-HW_ENABLE-ErrId`

In practice:
- `Val` holds the current value to write and the most recent readback value
- `RdCmd` triggers an SDO read
- `WrtCmd` triggers an SDO write
- `Bsy` indicates that the SDO object is currently busy
- `ErrId` exposes the most recent SDO error code

## Startup Syntax

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addEcSdoRT.cmd \
  "SLAVE_ID=<slave>,INDEX=0x<index>,SUBINDEX=0x<sub>,DT=<type>,NAME=<name>"
```

Supported parameters:
- `SLAVE_ID`:
  EtherCAT slave position. Optional, defaults to `0`.
- `INDEX`:
  SDO index, for example `0x8010`.
- `SUBINDEX`:
  SDO subindex, for example `0x07`.
- `DT`:
  Data type string. Use the normal ecmc data types:
  `U8`, `S8`, `U16`, `S16`, `U32`, `S32`, `U64`, `S64`, `F32`, `F64`.
- `NAME`:
  Logical object name. This becomes part of both the asyn path and the EPICS PV
  names.
- `P_SCRIPT`:
  Optional naming-prefix script. Defaults to `${ECMC_P_SCRIPT}`.

## Example

Example: expose one writable unsigned 16-bit SDO on slave `7`:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addEcSdoRT.cmd \
  "SLAVE_ID=7,INDEX=0x8010,SUBINDEX=0x07,DT=U16,NAME=DRV_PARAM"
```

Typical usage from EPICS:
1. Put the desired value to `...SDO-DRV_PARAM-Val`
2. Process `...SDO-DRV_PARAM-WrtCmd` to write it
3. Or process `...SDO-DRV_PARAM-RdCmd` to refresh the readback
4. Watch `...SDO-DRV_PARAM-Bsy` and `...SDO-DRV_PARAM-ErrId`

## Datatype Behavior

The script chooses the value record template from `DT`:
- `F32` and `F64` use the floating-point template and `asynFloat64`
- all other supported types use the integer template and `asynInt32`

That means:
- integer-like SDOs are exposed through one EPICS `ao`
- float SDOs are also exposed through one EPICS `ao`
- `Val` is always the central EPICS value record, while `RdCmd` and `WrtCmd`
  control when the actual SDO transfer happens

## When To Use This

Prefer RT SDO objects when:
- you only need one or a few specific SDOs
- the access should be available after IOC startup
- operator or service staff should be able to read/write the SDO from EPICS

Do not use RT SDO objects when:
- the setting belongs to normal startup configuration and should always be
  applied deterministically at boot
- the value should instead be mapped into the process image as a cyclic PDO
- you need a large structured device interface rather than a few individual SDOs

For startup-time writes, prefer normal SDO configuration with
`Cfg.EcAddSdo(...)`, `Cfg.EcAddSdoDT(...)`, or the higher-level slave/component
setup.

## Practical Notes

- `NAME` should be stable and readable, since it becomes both an asyn object id
  and a PV suffix.
- The wrapper is intended for asynchronous access during runtime, not for
  high-rate cyclic control.
- `ErrId` is the first PV to check if `RdCmd` or `WrtCmd` fails.
- `Bsy` can be used to avoid issuing overlapping read/write commands.

## Related Pages

- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
