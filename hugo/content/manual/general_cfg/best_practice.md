+++
title = "general best practice"
weight = 16
chapter = false
+++

## Scope
Use this page for host-level and startup-level recommendations that apply across
many ecmc systems.

## EtherCAT rate (`EC_RATE`)

The default EtherCAT frame rate in ecmc is `1 kHz`. For many systems this is
higher than necessary and can therefore be reduced.

Reducing the rate lowers controller load. Typical practical ranges are:

- `100 Hz` to `500 Hz` for many motion systems
- up to `1 kHz` when the application really needs it

Rates outside `100 Hz` to `1 kHz` are unusual and should only be used when the
hardware and application have been checked carefully.

Example:

```bash
require ecmccfg "EC_RATE=500"
```

For startup details, see
[startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}}).

As a rough comparison, common TwinCAT defaults are:

- `100 Hz` for PLC
- `500 Hz` for motion

See [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}}) for
more host-side guidance.

{{% notice info %}}
EPICS PVs update at a lower rate than the EtherCAT master rate. See
[PV Processing Rate]({{< relref "/manual/general_cfg/PVProcessingRate.md" >}})
for details.
{{% /notice %}}

## Global motion commands

The core database provides operational commands for all configured axes:

- `$(P)MCU-StopAll`: request a controlled stop while keeping axes enabled.
- `$(P)MCU-DisableAll`: stop and disable every configured axis.
- `$(P)MCU-ErrRst`: reset all ecmc errors.

The records share the existing `ecmc.error.reset` global command parameter.
Its command bits are reset errors (`1`), stop all (`2`), and stop/disable all
(`4`). Stop and disable requests are queued atomically and consumed by the
realtime thread. The `mbbo` command records use `Idle` and their named command
state; writing the command state again retriggers the action.

These PVs are operational controls. They are not safety-rated and do not
replace an emergency stop or hardware STO.

## Host setup

- If possible, make sure the native `igb` EtherCAT driver is used.

For more information, see:

- `https://git.psi.ch/motion/ecmc_server_cfg`
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})
