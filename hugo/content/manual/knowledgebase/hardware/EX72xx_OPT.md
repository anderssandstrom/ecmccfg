+++
title = "Ex72xx option configurations"
weight = 23
chapter = false
+++

The OPT wrappers use a common dispatcher and per-channel record/panel interface,
with separate PDO mappings and timing policies for EL/EP72xx and ELM72xx.
All existing non-OPT hardware configurations, databases and panels are unchanged.

## Devices and defaults

| `HW_DESC` | Channels | PDO family | Default `MODE` | `TP` | `INFO2` | `DIAG` |
| --- | --- | --- | --- | --- | --- | --- |
| `EL7211-9014_OPT` | 1 | EL72XX | CSV | 1 | INPUTS | 1 |
| `EP7211-0034_OPT` | 1 | EL72XX | CSV | 1 | INPUTS | 1 |
| `EL7201_OPT` | 1 | EL72XX | CSV | 0 | ERRORS | 1 |
| `EL7201-0010_OPT` | 1 | EL72XX | CSV | 1 | ERRORS | 1 |
| `ELM7231-0010_OPT` | 1 | ELM72XX | CSV | 0 | NONE | 0 |
| `ELM7222-0010_OPT` | 2 | ELM72XX | CSV | 0 | NONE | 0 |

The defaults retain the corresponding legacy CSV/STD mappings and logical
entry names, with encoder feedback status additionally enabled on every channel.
Set `ENC_STAT=0` to omit that addition. The ELM defaults retain the other minimal
mappings of the existing ELM CSV configs; there are no ELM STD configs in this repository. ELM channels read their
electronic motor nameplates, as in the existing configurations.

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7201-0010_OPT"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7211-9014_OPT,OPT='MODE=CSP,ENC_STAT=1,TP=0,INFO2=TEMP'"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=ELM7231-0010_OPT,OPT='MODE=CST,DIAG=1'"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=ELM7222-0010_OPT,OPT='MODE_1=CSV,MODE_2=CSP,TP_2=1,DIAG_2=1,INFO2_2=TEMP'"
```

## Example: three EL7211-9014 drives

This PSI engineering-startup excerpt configures three consecutive slaves on
master 0: slave 36 in CST, slave 37 in CSV and slave 38 in CSP. `addSlave.cmd`
increments `SLAVE_ID` after each call, so only the first position is specified.
Apply the motor component immediately after each slave: it configures the most
recently added drive.

```iocsh
require ecmccfg sandst_a "ENG_MODE=1,MASTER_ID=0,ECMC_VER=v11.1.0_RC1"

#- ec0.s36: cyclic synchronous torque.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=36,HW_DESC=EL7211-9014_OPT,OPT='MODE=CST'"
#- Limit maximum current to 1355 mA: half the motor nominal current of 2710 mA.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0,MACROS='I_MAX_MA=1355'"

#- ec0.s37: cyclic synchronous velocity.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL7211-9014_OPT,OPT='MODE=CSV'"
#- Limit maximum current to 1355 mA: half the motor nominal current of 2710 mA.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0,MACROS='I_MAX_MA=1355'"

#- ec0.s38: cyclic synchronous position.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL7211-9014_OPT,OPT='MODE=CSP'"
#- Limit maximum current to 1355 mA: half the motor nominal current of 2710 mA.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0,MACROS='I_MAX_MA=1355'"
```

The `sandst_a` module build and `v11.1.0_RC1` version are specific to this
example's environment. `applyComponent.cmd` requires access to `ecmccomp`.
Use the normal IOC startup sequence to apply the completed bus configuration.

The AM8111-XFX0 component defines nominal current as 2710 mA. `I_MAX_MA=1355`
overrides the maximum-current setting; the nominal-current setting remains
2710 mA. All three profiles retain the default
`ENC_STAT=1`, `TP=1`, `INFO2=INPUTS` and `DIAG=1`.

## Options and capabilities

`MODE` accepts `CSV`, `CSP` or `CST` for every wrapper. Each channel explicitly
selects its mode by a one-byte startup SDO: CSV = 9, CSP = 8, CST = 10. Channel 1
uses `0x7010:03`; ELM channel 2 uses `0x7110:03`.

`TP` accepts 0 or 1 and maps touch-probe **status**, including input levels.
EL7201 with resolver feedback does not support this option; `TP=1` is rejected.
Other wrappers support it. Touch-probe control and captured positions are not
part of this option.

`DIAG=1` maps actual velocity, actual torque and DC link voltage, and loads their
records. `DIAG=0` omits them. ELM CSP additionally maps following error when
`DIAG=1`. EL/EP CSP always maps following error, as in CSP_STD. EL/EP CSV and CSP
map torque offset; ELM does not map torque offset. CST uses torque demand.
`ENC_STAT=1` is now the default on every listed wrapper, in CSV, CSP and CST.
It maps encoder feedback status and loads its records. `ENC_STAT=0` omits the
PDO and records; `ENC_STAT_1` / `ENC_STAT_2` can override each channel separately.
`CfgEncoderStatus` and the panel link reflect the resolved selection.

EL/EP use PDO `0x1A0C`; ELM uses `0x1A02` for channel 1 and `0x1A42` for channel 2.
Each carries the same 16-bit layout: padding in bits 0–12, position-invalid in
bit 13, and the input cycle counter in bits 14–15. The shared records retain
`encoderStatus01/02`, `Enc01/02-Stat` and `Enc01/02-NotValid`.

| `INFO2` | Meaning | Supported wrappers |
| --- | --- | --- |
| `INPUTS` | Digital inputs 1/2 and STO, selection 10 | EL7211-9014, EP7211-0034 |
| `TEMP` | PCB temperature, selection 4 | All listed wrappers |
| `ERRORS` | Raw drive error bitmap, selection 5 | EL/EP wrappers |
| `NONE` | Omit Info2 PDO and records | All listed wrappers |

Velocity/position demand records and velocity diagnostics use the EL STD scaling
on EL/EP (`2.3406E-5`, `rad/s`). ELM retains the existing raw demand convention
(`1`, `RAW`), also used for its optional velocity diagnostics. `VEL_ESLO`,
`VEL_EGU`, `POS_ESLO` and `POS_EGU` override record scaling/units when needed for
the drive's configured scaling. They do not change drive SDO scaling. Torque
records use 0.1 percent per count in both families.

The ELM INPUTS selection is deliberately not exposed through the STO-oriented
input template. Use `TP=1` for the two touch-probe input levels. Error bitmap
records expose the raw word; interpreting individual bits requires the matching
drive revision's documentation.

`MODE_1`, `TP_1`, `INFO2_1`, `DIAG_1` and `ENC_STAT_1` override the shared option
for channel 1.
ELM7222 also accepts the corresponding `_2` overrides. A channel-specific value
wins over the shared value, which wins over the wrapper default. Second-channel
options on a single-channel wrapper are rejected. All channels are validated
before resetting or configuring the slave. No `ecmcIf` state is used.

## Timing and startup policy

| Setting | EL7211-9014 / EP7211-0034 / EL7201-0010 | EL7201 resolver | ELM72xx |
| --- | --- | --- | --- |
| Sync0 period | EtherCAT cycle | EtherCAT cycle | 62500 ns |
| Sync0 shift | 0 | Half EtherCAT cycle | `ECMC_SYNC_0_OFFSET_NS`, default 0 |
| Sync1 period | 0 | 0 | EtherCAT cycle |
| Sync1 shift | 0 | 0 | `ECMC_SYNC_1_OFFSET_NS`, default 0 |
| Initial peak-current SDO | 100 mA, motor config overwrites it | Same | Nameplate policy; no EL peak-current override |

EtherCAT port-wiring checks are enabled by the EP wrapper only. EL and ELM
wrappers do not enable this check.

All wrappers accept `SYNC_0_CYCLE`, `SYNC_0_SHIFT`, `SYNC_1_CYCLE` and
`SYNC_1_SHIFT` overrides in ns. ELM timing does not issue EL-specific `0x1C32:02`
and `0x1C33:02` cycle-time SDOs. The watchdog helper retains its sample-rate-based
defaults and accepts `WATCHDOG_DIVIDER` and `WATCHDOG_INTERVALS`. The existing
`ECMC_EC_STARTUP_DELAY_EL72XX` startup-delay setting is retained.

## Extending a family

Device wrappers fix product identity, family, channel count, capabilities and
defaults. `ecmcEX72XX_OPT.cmd` validates channels before slave reset, dispatches
the mappings and applies the family's timing policy.

- `ecmcEX72XX_OPT_EL72XX_pdo.cmd` and `_timing.cmd` implement EL/EP policy.
- `ecmcEX72XX_OPT_ELM72XX_pdo.cmd` and `_timing.cmd` implement ELM policy,
  including the second channel's PDO and object offsets.
- `ecmcEX72XX_OPT_channel.cmd` shares mode SDO selection, feature records and
  configuration readbacks across families.

The mapping preserves common logical entry names such as `driveControl01`,
`velocitySetpoint01` and `positionActual01`. ELM channel 2 uses suffix `02`.
The EL7201-0010 following-error object uses subindex `0x06`; the existing
EL7211-9014/EP7211-0034 STD mapping uses `0x09`.

These wrappers support the MDP742 layout only. DS402-profile device variants
need their own family mapping and are not aliases for these wrappers. Likewise,
adding another ELM or EL variant requires checking its exact ESI/revision and
capabilities; the family name alone does not establish compatibility.

References: [EL OCT PDO mapping](https://infosys.beckhoff.com/content/1033/el72x1-001x/1877565067.html),
[EL resolver mapping](https://infosys.beckhoff.com/content/1033/el72x1/1977008779.html),
[ELM PDO mapping](https://infosys.beckhoff.com/content/1033/elm72xx/12673270795.html),
[ELM input objects](https://infosys.beckhoff.com/content/1033/elm72xx/12672413323.html),
[MDP742 versus DS402](https://infosys.beckhoff.com/content/1033/el72x1-001x/1859307019.html).

## Panels and records

Single-channel wrappers select `ecmcEX72XX_OPT.ui`. ELM7222 selects the dedicated
`ecmcEX72XX_OPT_2ch.ui` top-level overview. Both keep the standard 128 x 500
slave frame and the `IOC`, `MasterID` and `SlaveID` macros.

The two-channel overview shows each channel's mode, encoder position, decoded
DS402 state and Fault/Warning LEDs, with equal links to open channel 1 or channel 2. It does
not embed one channel's detailed controls. Each link opens the shared channel
panel with its own explicit `ChID`, `CfgSuffix` and `ChannelTitle` macros.
The single-channel overview passes an empty title; two-channel subpanels show
`Channel 1` or `Channel 2`.

The channel panel's **Drive** tab groups motion mode, encoder position, drive
state, Fault/Warning LEDs and configured drive-detail links. The **Setup** tab groups touch-probe
and Info2 configuration readbacks and their detail links.
```sh
caQtDM -macro 'IOC=IOC_PREFIX,MasterID=0,SlaveID=1' ecmcEX72XX_OPT.ui
caQtDM -macro 'IOC=IOC_PREFIX,MasterID=0,SlaveID=1' ecmcEX72XX_OPT_2ch.ui
```

Configuration PVs use the slave's `ECMC_P`, normally
`$(IOC):m$(MasterID)s$(SlaveID)-`:

| Suffix | Values |
| --- | --- |
| `CfgChannels` | 1 or 2 |
| `CfgMode` | 0 = CSV, 1 = CSP, 2 = CST |
| `CfgTouchProbe` | 0 = Not mapped, 1 = Mapped |
| `CfgInfo2` | 0 = INPUTS, 1 = TEMP, 2 = ERRORS, 3 = NONE |
| `CfgDiagnostics` | 0 = Not mapped, 1 = Mapped |
| `CfgTorqueOffset` | 0 = Not mapped, 1 = Mapped |
| `CfgFollowingError` | 0 = Not mapped, 1 = Mapped |
| `CfgEncoderStatus` | 0 = Not mapped, 1 = Mapped |

Channel 2 adds `02` to each per-channel configuration suffix (for example
`CfgMode02` and `CfgInfo202`). These are startup readbacks; changing options
requires restarting the IOC. Feature links appear only when the relevant PDOs
and records are configured. Hidden links subscribe to configuration PVs only;
feature records are subscribed when their detail panel is opened. A connection
failure remains a connection failure, rather than implying a disabled feature.
CSV, CSP and CST detail panels expose **DS402 enable** and **Disable** buttons.
From the overview, open the desired channel and select its mode's detail link.
The buttons process that channel's `Drv01-TrgDS402Ena.PROC` and
`Drv01-TrgDS402Dis.PROC` records (channel 2 uses `Drv02`). The enable sequence
writes control words 128, 6, 7 and 15 with fixed 10 ms delays; disable writes 0.
These are direct PDO controls and require no axis object. The sequence uses
fixed delays rather than waiting for status transitions; the panel displays the
status word, warning and error readbacks alongside the controls.

All mode detail panels use a compact 350 x 260 layout with writable target and
separate PDO demand readback:

| Mode | Writable PV suffix | Demand readback |
| --- | --- | --- |
| CSV | `Drv01-Spd` | `Drv01-Spd-RB` |
| CSP | `Drv01-PosCmd` | `Drv01-PosCmd-RB` |
| CST | `Drv01-Trq` | `Drv01-Trq-RB` |

The torque-offset detail panel also has a writable target, `Drv01-TrqOff`,
and a separate `Drv01-TrqOff-RB` readback with a trend button. Enter the offset
in percent and press Enter to write. This link is available for the EL72XX
PDO family (EL/EP) in CSV and CSP, where the offset is mapped. The current
ELM72XX and 7062 OPT configurations do not map a torque offset.

The CST panel also shows actual torque (`Drv01-TrqAct` / `Drv02-TrqAct`), in
percent, alongside the demand readback. It uses the existing `DIAG=1` telemetry;
with `DIAG=0` the panel says **Not mapped** and does not subscribe to that absent
record. Both readbacks fit on one row, retaining the 350 x 260 panel size.

Channel 2 uses `Drv02`. Enter the target in the record's configured units and
press Enter to write. Torque is in percent; velocity and position use the
scaling described above. These records do not require an axis object. When an
axis controls the drive, use the axis panel for motion commands.

Small **>** buttons beside readbacks open the existing `ecmcGraph_v1.ui` trend
panel, using the same `IOC`, `TITLE` and `PV` macros as the MO7221 panels.
They are available for actual position in the channel/two-channel overviews,
actual torque, velocity and DC link voltage in Diagnostics, CST torque demand
readback and actual torque, CSP position demand readback, CSV velocity demand
readback, following error, PCB temperature, and torque offset readback.
Each graph targets the selected channel's exact readback PV. Links are available
only for mapped features; `DIAG=0` does not offer trends for absent diagnostic
records. Panel dimensions are unchanged.

### DS402 state and LEDs

The detail panels show `Drv01-DS402State` (channel 2: `Drv02-DS402State`), decoded
from the existing status PDO. Ready, On, Enabled, Fault and Warning use LEDs
instead of long binary readback strings. Hover over an LED for its bit meaning;
open **State guide** for a compact reference to all states. Warning is a separate
bit and can coexist with Operation enabled.

| Decoded state | Meaning |
| --- | --- |
| Not ready to switch on | Drive is initializing. |
| Switch on disabled | Output stage is disabled. |
| Ready to switch on | Shutdown command accepted. |
| Switched on | Ready for operation enable. |
| Operation enabled | Accepts the selected mode's setpoint. |
| Quick stop active | Handling a quick-stop request. |
| Fault reaction active | Executing its fault response. |
| Fault | Fault response complete; resolve cause. |
| Unknown | Status bits do not match a defined state. |

The decoder uses the DS402 state-bit patterns, ignoring voltage, warning and
mode/manufacturer-specific bits. See the manufacturer reference for
[state coding](https://doc-legacy.synapticon.com/software/42/documentation_html/object_htmls/6041/index.html).

The new OPT-only derived records refresh locally at 10 Hz and propagate invalid
source alarms. They add no PDOs or SDOs. Reload the IOC database/restart the IOC
to load them before using the new state readback. The existing enable sequence
still uses fixed delays rather than waiting for decoded state transitions.

The encoder-status panel uses a 180 x 126 layout with a **Position valid** LED:
green when status bit 13 is 0, red when it is 1. The two blue/grey **Cycle [1:0]**
LEDs show the counter MSB on the left (bit 15) and LSB on the right (bit 14).
The counter advances each process-data cycle and wraps from 3 to 0; it may
look static at GUI sampling rates and is not a standstill/communication-health indicator.
Bits 0–12 are padding, with no additional encoder diagnostics in this PDO.
The raw word remains available below the LEDs, and tooltips explain each field.
See the [feedback-status layout](https://infosys.beckhoff.com/content/1033/elm72xx/12673270795.html)
and [feedback validity/counter meanings](https://infosys.beckhoff.com/content/1033/elm72xx/12672413323.html).

Input/STO and touch-probe panels use compact 180 x 126 layouts. Input LEDs are
green for high and grey for low. The **STO OK** LED is green for feedback OK (1)
and red for STO active (0). Tooltips explain the colors. The touch-probe panel
retains the raw status word below its two input LEDs.

Temperature records now consistently use the drive channel, for example
`Drv01-TmpAct` or `Drv02-TmpAct`, backed by `temperatureActual01/02`.
The earlier EP-specific panels and substitutions remain intact, but the EP OPT
wrapper selects the shared resources.

## Validation

Run `python3 tests/test_ex72xx_opt.py`. The tests cover default PDO compatibility
with legacy scripts plus the enabled encoder-status PDO, supported option combinations, independent ELM channels,
mode-selection SDOs, native EPICS decoding of every 16-bit statusword, writable
target PVs, timing/watchdog defaults and overrides, invalid-option
rejection before reset, database expansion, record sources and visible panel
channels. Database expansion needs EPICS `msi`; UI compilation needs Qt `uic`.
Those checks are skipped individually if the respective tool is unavailable.

Before deployment, check EtherCAT OP, live Channel Access readbacks and panel
behaviour on the actual device/revision. Static checks do not establish hardware
PDO acceptance, drive mode transitions or live panel behaviour.

## Related Pages

- [EL72xx diagnostics and troubleshooting]({{< relref "/manual/knowledgebase/hardware/EL72xx.md" >}})
- [Hardware knowledge base]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
