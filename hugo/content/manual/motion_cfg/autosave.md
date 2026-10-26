+++
title = "Motor position and soft-limit autosave"
weight = 24
chapter = false
+++

## Scope and required support

Motor position restoration and soft-limit restoration are separate features.
This page describes the ECMC motor-record startup restore implementation and its
startup gate. Use an ECMC build containing that implementation; adding an option
to YAML does not add support to an older binary.

For the complete incremental stepper setup, see
[the stepper_openloop_asr example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_openloop_asr).

## Enable soft-limit restoration in YAML

```yaml
axis:
  parameters: "restoreMotorSoftLims=1;"

epics:
  name: Axis1
  motorRecord:
    syncSoftLimits: true
```

`restoreMotorSoftLims=1` belongs in `axis.parameters`, not in
`epics.motorRecord`. Append it with a semicolon if other driver options already
exist, for example `powerAutoOnOff=2;restoreMotorSoftLims=1;`.

The restore option also enables ongoing motor-record/ECMC soft-limit
synchronization. Omitting, commenting out, or setting
`epics.motorRecord.syncSoftLimits: false` does not disable synchronization while
`restoreMotorSoftLims=1` remains in the driver options. The generated option
string can contain `syncSoftLims=0;restoreMotorSoftLims=1;`: the restore option
turns synchronization on. Restore-once with synchronization disabled afterward
is not a separate mode of this option.

Without the restore option, ECMC seeds the motor's limits from its configured
limits at startup. Saving the motor limit fields alone does not make restored
values authoritative in that mode.

## Which values are used?

The standard YAML generator initializes the motor record's `.DLLM` and `.DHLM`
from the YAML soft-limit configuration. Autosave can overwrite those fields
while the IOC initializes. ECMC then snapshots the initialized motor fields and
uses that pair when `restoreMotorSoftLims=1` is selected.

| Configuration | Startup source of the restored limit pair |
| --- | --- |
| Restore option, with autosave restoring `.DLLM` and `.DHLM` | Autosave-restored motor fields |
| Restore option, with no autosave restore of those fields | Motor fields initialized by the standard YAML generator |
| No restore option | Configured ECMC limits seed the motor at startup |

The driver does not detect whether autosave supplied a field. It uses the motor
record values after initialization. For example, YAML limits `-100, 100` and
saved dial limits `-123, 123` result in `-123, 123`; without a saved pair the
standard generated motor record retains the YAML-derived values. A custom
motor template must initialize its dial fields consistently with the desired
ECMC limits.

## Autosave request and restore passes

For an IOC named `MTEST04-MTN-ASM`, use `cfg/MTEST04-MTN-ASM_pos.req`:

```text
# Position restoration is controlled separately by the motor's RSTM field.
MTEST04-MTN-ASM:Axis1.DVAL
# Soft limits are dial coordinates, in engineering units.
MTEST04-MTN-ASM:Axis1.DLLM
MTEST04-MTN-ASM:Axis1.DHLM
```

Do not also restore the writable `-CfgDLLM` and `-CfgDHLM` records for the same
axis. That creates competing restore paths. Do not save `-RB` readback records
as configuration. Independent limit enable flags are not encoded by the two
dial limits and require separate ordering if they must also be restored.

With the PSI `ioc install` workflow, a filename ending in `_pos.req` selects the
two-pass restore setup. For a differently named request, the PSI directive
`#ENABLE-PASS=2` requests that setup. Verify that the generated restore script
contains both actual autosave pass registrations before `iocInit`:

```iocsh
set_pass0_restoreFile "MTEST04-MTN-ASM_pos.sav"
set_pass1_restoreFile "MTEST04-MTN-ASM_pos.sav"
```

Autosave calls these passes **0 and 1**; the PSI directive's value `2` denotes the
two-pass setup. A `.req` lists fields to save. The `.sav` contains the values
which will actually be restored, so inspect it when troubleshooting.

## Position restoration and MRES

The restore option above concerns soft limits only. Position uses the saved
`.DVAL` and the motor's `RSTM` policy. In the ESS motor implementation, the
`NearZero` default restores a nonzero saved position when the initial readback
is near zero, according to the motor deadband. It does not request restoration
of a saved zero. `Always` is a different, explicit position-restoration policy;
do not change it merely to troubleshoot soft limits.

This example uses an incremental encoder (`encoder.type: 0`), whose counter
position can be restored through the motor. Soft-limit restoration can be used
independently of position restoration.

ECMC uses engineering units. An ECMC-specific motor template should establish
`MF_DRIVER_USES_EGU` from database loading, for example:

```epics
field(MFLG, "$(MFLG=8)")
```

Mask `8` (`1 << 3`) selects the driver's engineering-unit convention. It does not select a
position-restore policy or request zeroing. Keep the real MRES scaling; do not
set MRES to 1 to conceal a limit conversion problem. The ECMC compatibility init
hook also sets the EGU flag before motor-record initialization.

## Complete startup before motion

Set the gate explicitly before ecmccfg enters runtime:

```iocsh
epicsEnvSet("ECMC_STARTUP_GATE", "1")
```

With the gate enabled, native axis initialization proceeds with drives disabled.
Ordinary PLC/plugin cyclic execution, motion sequences, PVT, master/slave state
machines, C++ logic and position compare remain held until every native axis
and every **loaded motor record** has completed startup. This includes restored
limits, the position-load handshake when requested, and a subsequent RT sample
acknowledging the loaded coordinate. Axes without a loaded motor record do not
wait for one. Early motion/enable requests are rejected, not replayed later;
STOP, disable, coordinate loading and status polling remain available.

Configuration and plugin/logic enter-RT initialization hooks still run to prepare
runtime; supported motion/enable commands from those hooks are held too. The
dedicated safety plugin and bus/disabled-axis I/O continue operating. Gate `0`
selects legacy startup and does not provide this guarantee. `START_EPICS_FIRST`
changes startup order; its fixed delay is not a substitute for the gate.

The ECMC motor-record compatibility workaround clears only a stale startup
`COMM_ALARM`, once a healthy sample and live axis state have been verified. It
uses EPICS alarm handling under the record lock before delivering the asyn
callback, allowing a deferred position load to be queued. It preserves other
alarms and does not repeatedly clear runtime communication faults. This is a
narrow exception to normal motor-record alarm ownership; it does not change
motorECMC or bypass asyn command delivery.

See [startup configuration]({{< relref "/manual/general_cfg/startup/_index.md" >}})
for startup ordering. Verify a known nonzero saved position and limits different
from YAML defaults before the log announcing release of PLCs and motion command
producers. Repeat with no loaded motor record and with a stalled restore or bus
fault; incomplete startup must leave motion held.
