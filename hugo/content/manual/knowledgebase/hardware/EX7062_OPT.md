+++
title = "EL/ED/MO7062 OPT configurations"
weight = 22
chapter = false
+++

The opt-in descriptors `EL7062_OPT`, `ED7062_OPT` and `MO7062-0100_OPT`
share one two-channel dispatcher. Existing descriptors, substitutions and panels
remain unchanged. The default PDO set matches the existing CSV configuration:
control word, velocity demand, primary position and drive status on each channel;
touch-probe control/status and probe 1 positive/negative latch positions;
digital inputs (EL/ED only); secondary encoder position; and one shared voltage/temperature
pair exposed on channel 1. Existing default PV names and scaling are retained.

## Startup examples

```iocsh
# Default CSV on both channels, same process image as EL7062.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7062_OPT"

# Independent channel modes, with extra diagnostics and TP1 DC timestamps.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=ED7062_OPT, OPT='MODE_1=CSP,MODE_2=CSV,EXT_DIAG=1,TP_DC=1'"

# MO uses a fixed CSV process image without digital inputs.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=MO7062-0100_OPT"
```

Apply motor and encoder components per channel after `addSlave`, as with the
legacy descriptors. `ECMC_EC_COMP_TYPE` remains `EL7062` for all three devices.
For example:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000,I_STDBY_MA=100,U_NOM_MV=24000,L_COIL_UH=3050,R_COIL_MOHM=2630'"
```

## Options

Pass options in `OPT='...'`. A `_1` or `_2` suffix overrides the common option
on that channel, for example `MODE=CSP,MODE_2=CSV,TP_2=0`. Options are resolved
and validated on both channels before resetting or configuring the device.

| Option | Default | EL7062 / ED7062 | MO7062-0100 |
| --- | --- | --- | --- |
| `MODE` | `CSV` | `CSV`, `CSP`, `CST`, independently per channel | `CSV` only |
| `TP` | `1` | Touch-probe control/status and TP1 positive/negative latch positions | Must remain `1` |
| `INPUTS` | `1` (EL/ED), `0` (MO) | Digital-input PDO and records | Must remain `0`; no digital inputs |
| `ENC2` | `1` | Secondary incremental encoder position | Must remain `1` |
| `DIAG` | `1` | Shared voltage and PCB temperature; global option, no channel suffix | Must remain `1` |
| `EXT_DIAG` | `0` | Actual velocity and torque; following error in CSP | Must remain `0` |
| `TP_DC` | `0` | TP1 positive/negative DC timestamps; requires `TP=1` | Must remain `0` |
| `AUTOTUNE` | `1` | Load tuning/readback records and show the tuning link | `0` or `1` |

`0` disables a feature; `1` enables it. Optional records are loaded only when
the matching PDOs are configured. `AUTOTUNE` only controls record loading;
it does not start tuning at startup.

MO support uses a fixed CSV process image without digital-input PDOs or records.
`INPUTS=1`, including per-channel overrides, is rejected before configuring the device. Its PDO mappings are fixed/read-only and may produce
mapping warnings, as noted in that legacy configuration. Alternative modes,
timestamps and additional PDO selections are rejected until the particular MO
process image has been verified; EL/ED mapping flexibility is not assumed.
Disabling tuning records is allowed because that does not change the process
image.

The 7062 family uses dedicated input and diagnostic PDOs, so it has no `INFO2`
selector. The EL72xx `ENC_STAT` mapping is not reused: the documented 7062
standard PDO table does not expose that encoder-status word. The secondary
encoder position is available through `ENC2`.

## Modes and PVs

Mode selection is explicitly written to `0x7010:03` / `0x7110:03` and queued
for replay when the slave reconnects: CSV = 9, CSP = 8, CST = 10.

| Mode | Writable target | Demand readback | Default scaling |
| --- | --- | --- | --- |
| CSV | `Drv01-Spd` | `Drv01-Spd-RB` | Raw drive units, scale 1 |
| CSP | `Drv01-PosCmd` | `Drv01-PosCmd-RB` | Raw drive units, scale 1 |
| CST | `Drv01-Trq` | `Drv01-Trq-RB` | Percent, scale 0.1 |

The PV prefix is `$(IOC):m$(MasterID)s$(SlaveID)-`. Replace `01` with `02`
for channel 2. Primary position is `Enc01-PosAct`; secondary position is
`Enc01-PosAct02`, linked to the existing `positionActual01_2` entry.

Shared supply PVs retain the legacy names `Drv01-VltAct` and `Drv01-TmpAct`
with scales 0.001 V/count and 0.1 C/count. Extra diagnostics use
`Drv01-VelAct` (raw), `Drv01-TrqAct` (percent, scale 0.1), and in CSP
`Drv01-PosDiff` (counts). Both channels have their own extra diagnostic PVs.

Touch-probe records retain the legacy `Tp01-...` names. `TP_DC=1` adds
`Tp01-PosTimestamp01` and `Tp01-NegTimestamp01`. These are raw 32-bit DC
nanosecond timestamps displayed through signed EPICS `longin` records; handle
wraparound when calculating time differences. The underlying EtherCAT entries
are `touchProbeTimestampPos01_1` / `touchProbeTimestampNeg01_1`, compatible
with the existing ED7062 TPDC axis configuration.

## Panels and DS402

`ecmcEX7062_OPT.ui` is the standard 128 × 500 two-channel overview with mode,
position, decoded DS402 state, fault/warning LEDs, and links to each channel.
The compact channel panel opens only configured feature panels.

The CSV/CSP/CST control panels and DS402 state guide are shared with Ex72xx OPT.
Targets are writable; demand readbacks have a small **>** trend button.
DS402 enable/disable is available without an axis object using the existing
`Drv01-TrgDS402Ena` / `Drv01-TrgDS402Dis` sequences. Enable writes
128, 6, 7, 15 with fixed delays; disable writes 0. The decoded state indicates
whether the drive accepted the command. Use the axis panel for motion commands
when an axis controls the drive.

Input and touch-probe panels use LEDs. Trend buttons are provided for primary
and secondary position, TP1 latched positions, shared voltage and temperature,
actual velocity/torque, and CSP following error. CST actual torque is shown
when `EXT_DIAG=1`; otherwise the control panel displays “Not mapped”.
The tuning panel provides parameter readback and an explicit tuning command,
with the same requirements as the legacy tuning controls: OP, motor power,
and a disabled drive. Tuning can move the motor.

## Timing and existing operating notes

The legacy DC schedule is retained: Sync 0 at 62500 ns, Sync 1 at the application
period minus 62500 ns, and the same cycle-time SDOs. `SYNC_0_SHIFT` (default 0)
is applied to both DC setup and the existing input timing metadata.
`WATCHDOG_DIVIDER` and `WATCHDOG_INTERVALS` override the existing sample-rate
based defaults. There is no EtherCAT port-wiring check in these descriptors.

The existing [EL7062 operating notes]({{< relref "/manual/knowledgebase/hardware/EL7062.md" >}})
also apply, including the CSV open-loop counter issue and guidance on CSP,
tuning, homing and DC timing. OPT does not change those drive behaviours.

## Mapping references and validation

EL/ED extensions follow Beckhoff’s standard-object tables:
[EL7062](https://infosys.beckhoff.com/content/1033/el7062/16882969995.html)
and [ED7062](https://infosys.beckhoff.com/content/1033/ed7062/16882969995.html).
The channel 2 PDO indices have a 0x80 offset; channel object indices have a
0x100 offset. Supply mapping preserves the explicit voltage/temperature
subindices used by the existing repository configuration.

Static integration checks compare the default mappings to the legacy CSV
process image, expand the selected databases, follow visible panel/trend links,
check per-channel options and startup SDOs, and compile the Qt panels. These
checks do not connect to a drive; the added EL/ED modes and optional PDO
combinations still require commissioning on the target hardware.

## Hardware profile discovery

After setup, `ecmcListHwProfiles` lists the installed YAML profiles and
`ecmcListCompatibleProfiles(master, slave, channel)` compares them with this
channel's resolved `_OPT` options. This initial catalogue declares EL7062_OPT
compatibility only; ED/MO descriptors are recorded but have no supported profile
match yet. Checks use startup metadata, not a live bus scan, and do not verify
touch-probe trigger/source configuration. See [hardware profiles](/manual/motion_cfg/hardware_profiles/).
