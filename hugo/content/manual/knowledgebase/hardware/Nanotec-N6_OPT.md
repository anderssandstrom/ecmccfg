+++
title = "Nanotec N6 optional PDOs, position output and homing"
weight = 26
chapter = false
+++

The N6 optional configuration combines fine open-loop axis feedback with a
periodic digital output generated inside the drive. Optional homing PDOs
prepare the interface for referencing the output's position source using
homing method 35.

The working bench setup was an `N6-1-1-1-S`, firmware
`FIR-v2542-B1080909`, with a 200-full-step motor in cyclic synchronous
velocity mode (CSV). Fine counter feedback and an output every 100 full
steps were demonstrated together. Subsequent method-35 testing returned
scaled position to zero and produced a repeatable first-edge shift,
documented below. Full homing/error handling still needs commissioning. Homing is commanded through the normal axis interface
and does not execute automatically at IOC startup.

## Configure the hardware and components

Build/install both updated modules: ecmccfg supplies the hardware, records
and panels; ecmccomp supplies `Drive-Generic-PositionOutput`.

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1,HOMING=1'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PositionOutput,CH_ID=1,MACROS='FULL_STEPS=100,OUTPUT=1,ARM=1,N6_IO_24V=0'"
```

Apply the motor first, then the position-output component, before applying
EtherCAT configuration. The output component checks the raw mapping, motor
configuration and supported interval. Motor `INV_DIR=0` is required. Applying
the motor again after the output component is rejected because it would
restore position units and change the output period.

The complete example is
`examples/PSI/lab_setup/N6/startup_position_output_100_steps.cmd`, with
`cfg/axis_position_output.yaml` for the axis. The ordinary `startup.cmd`
remains available for the base configuration. Restart the IOC after changing
PDO options. The former `N6-1-1-1-S_POS_OUT` hardware wrapper has been removed;
use `_OPT` instead.

## Hardware options and PDO names

| Option | Default | Effect when set to `1` |
| --- | --- | --- |
| `RAW_POS` | `0` | Map fine `6063:00` as `positionActual01`; name existing `6064:00` entry `positionActualScaled01` |
| `HOMING` | `0` | Add method, offset, drive homing speeds/acceleration and the sequence-26 trigger alias |
| `CAPTURE` | `0` | Map `3241:01–0C` capture control readbacks, counts and latched positions |
| `ANALOG_IN` | `0` | Map both signed `3320:01–02` analog input values |

All options are independent and accept only `0` or `1`. With all disabled,
the PDO mapping matches the base `N6-1-1-1-S` configuration. The motor
component type remains `N6`.

`RAW_POS=1` appends the S32 `6063` entry to existing TxPDO `1A03`, increasing
that PDO from 16 to 20 bytes. The four TxPDO assignment slots are retained.
`HOMING=1` appends 17 bytes to existing RxPDO `1603`, increasing it from
4 to 21 bytes without adding an RxPDO assignment slot. These options map
entries; they do not change position units, route outputs or execute homing.
The trigger alias is process-image data over existing controlword bit 4;
it adds no EtherCAT PDO bytes.

### Capture and analog input options

The runnable all-options example is
`examples/PSI/lab_setup/N6/startup_opt_all.cmd`. It reuses the 100-step
startup and M1 axis with `N6_CAPTURE=1,N6_ANALOG_IN=1`.

To enable all optional mappings directly:

```text
HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1,HOMING=1,CAPTURE=1,ANALOG_IN=1'
```

`CAPTURE=1` exposes all twelve `3241` payload subindices as U32 readbacks:

| Group | Source | Subindices | PDO | Entry suffix |
| --- | --- | --- | --- | --- |
| 01 | Home-switch capture | `01–04` | `1A00` | `01` |
| 02 | Input 3 capture | `05–08` | `1A01` | `02` |
| 03 | Input 4 capture | `09–0C` | `1A02` | `03` |

Each group has `captureControlNN`, `captureCountNN`, `capturePositionNN`
and `captureRawPositionNN`. Corresponding PVs are `CaptureNN-Control-RB`,
`CaptureNN-Count`, `CaptureNN-PosAct` and `CaptureNN-PosRaw`. Position is in
configured drive position units; raw position is in sensor increments.
The EPICS records preserve the entire unsigned 32-bit range. For negative
positions, interpret the appropriate 32-bit two's-complement value in the
application rather than treating the unsigned display as a distance.

The object dictionary marks these subindices **TxPDO-only**, including the
control fields. Mapping them does not arm capture or change input routing.
Configure the desired edge by SDO: `3241:01` for the home-switch source,
`:05` for input 3, `:09` for input 4. Values are `0` disabled, `1` rising,
`2` falling and `3` both edges. Re-arming can reset the capture count.
For example, enable both-edge capture of input 3 on master 1/slave 0:

```bash
ethercat download -m1 -p0 --type uint32 0x3241 0x05 3
```

Check capture/input-routing behavior with the actual wiring and firmware;
in particular, its raw sensor value needs verification with our generated
open-loop counter. No automatic capture SDO writes are added by `_OPT`.

`ANALOG_IN=1` maps `analogInput01` and `analogInput02` (S32, `3320:01–02`)
in `1A03`, with PVs `AI01` and `AI02`. Values use the drive's existing input
scaling and offsets. The records label them `user`, not volts; no voltage
conversion or analog-input configuration is applied by this option.

The groups are deliberately spread across existing PDOs because each PDO
has at most eight mapping entries. With all options enabled, TxPDO entry
counts are `1A00:6`, `1A01:5`, `1A02:5`, `1A03:8`; the four assignment slots
are retained. `1A03` is 28 bytes with raw position and both analog inputs.

### Fine feedback and scaled output position

| Configuration | `positionActual01` | `positionActualScaled01` |
| --- | --- | --- |
| Base descriptor or `RAW_POS=0` | `6064`, position in configured units | Not mapped |
| `_OPT`, `RAW_POS=1` | `6063`, fine open-loop counter | `6064`, position in configured units |

For the tested 200-full-step motor, the fine counter has nominally
3,276,800 counts/revolution, or 16,384 counts/full step. The example uses
full-step engineering units:

```yaml
epics:
  unit: steps

drive:
  numerator: 200
  denominator: 3276800

encoder:
  unit: steps
  numerator: 200
  denominator: 3276800
  bits: 32
  position: ec0.s$(ENC_SID).positionActual01
```

These are excerpts from the full YAML; use the complete example when
configuring an IOC and keep EtherCAT paths consistent with its axis
configuration. For degrees, use numerator 360 for both drive and encoder
and set both unit labels to `deg`. Check the corresponding scaling when
using another motor step count. Velocity remains in native increments per
second, so the drive and encoder scales remain matched.

The position-output component makes `6064` deliberately coarse: with
`FULL_STEPS=100`, one count is 100 full steps, or half a revolution on this
motor. Use `6063` for fine axis feedback. Both entries are available
simultaneously, but only one is the fine counter after changing `60A8`.
The counter represents generated open-loop motion; it does not measure
rotor position or detect lost steps. Additional `60E4` position values also
use the configured position units; check external feedback channels if used.
Its 32-bit rollover and the output's
behavior across rollover require application checks.

## Configure periodic output triggering

The output is generated inside the drive from scaled position `6064` and
its digital-output divider. It requires no cyclic PLC pulse generation or
NanoJ program. This configuration provides periodic position-related
triggering; it does not program arbitrary absolute compare positions or a
pulse width.

| Component macro | Default | Meaning |
| --- | --- | --- |
| `FULL_STEPS` | `100` | Full motor steps per output pulse |
| `OUTPUT` | `1` | Physical digital output 1, 2 or 3 |
| `ARM` | `0` | Initial output gate: `0` disabled, `1` enabled |
| `N6_IO_24V` | `0` for the first output | `0` = 5 V; `1` = nominal 24 V/+UB_Logic |
| `N6_INPUT_PULLUP` | Inherit motor; normally `0` | Shared input bias: `0` pull-down, `1` pull-up |

Supported intervals are `10^n * d`, where `n=0..6` and `d` is one of
`1,2,4,8,16,32,64`. Other intervals, such as 50 or 125 full steps, are
rejected. The component selects a canonical full-step unit `10^n` and a
power-of-two divider.

All outputs on one drive share `60A8`. For example, 100 and 200 steps use
the same unit of 100 with dividers 1 and 2, so they can coexist. Intervals
100 and 10 select different unit exponents and are rejected together.
Electrical settings are shared too: later output components inherit the
first output's voltage and reject conflicting explicit voltage/bias choices.
Intervals are startup settings, not live scan parameters. Nothing is saved
to drive flash by this component.

For output 1 every 100 full steps, the important settings are:

| Object | Value | Purpose |
| --- | --- | --- |
| `60E6:01` | `0` | Keep sensorless interface disabled |
| `60A8:00` | `0x02AC0000` | Position unit = 100 full steps |
| `3252:02` | `0x0910` | Route position divider 1 to output 1, gated by bit 16 |
| `323A:01` | `0` by default | Select 5 V I/O |
| `60FE:01`, bit 16 | `ARM` | Output 1 gate |

With 200 full steps/revolution, subsequent edges were observed 180 degrees
apart: two output transitions per revolution. The expected steady time
between edges is `100 / abs(velocity in full steps/second)` seconds
(or `180 / abs(velocity in degrees/second)` when using degrees). An edge
is not a complete pulse: alternating rising/falling edges 100 steps apart
give a 200-step full cycle. See the observed first-edge shift after homing
below; verify waveform, pulse width, stop/restart and reversal on the bench.
The direct position-routing limit is 500 Hz.

### Wiring and I/O voltage

Output 1 is on **X4 pin 5**, with **GNDD on X4 pin 8**.
The position-output component defaults to **5 V output levels**. Select
`N6_IO_24V=1` for nominal 24 V/+UB_Logic instead.

`323A:01` selects both the output level and the digital input thresholds.
Selecting 5 V outputs therefore also selects 5 V input thresholds. It does
not configure the motor power supply; a motor supply such as 48 V is a
separate matter. The base hardware and motor component retain their
existing 24 V I/O default; the position-output component applies its own
selection afterwards. `323A:02` selects the shared input pull-up/pull-down.

### Arm and disarm an output

The runtime gate controls are:

| PV suffix | Output-word bit | Function |
| --- | --- | --- |
| `PosOut01-Ena` | 16 | Output 1 gate |
| `PosOut02-Ena` | 17 | Output 2 gate |
| `PosOut03-Ena` | 18 | Output 3 gate |

Each has a corresponding `-RB` readback. For example, substituting the
actual slave prefix:

```bash
caput <prefix>PosOut01-Ena 0
caput <prefix>PosOut01-Ena 1
caget <prefix>PosOut01-Ena-RB
```

These controls gate the configured position-derived signal. Enabling a gate
does not command a single pulse or establish the pulse origin. Gate writes
preserve other output bits, including the brake bit 0. The component uses
bit-addressed `WriteEcEntryEcPath`; the records use asyn masks. Writing the
complete `BO01-Arr` word replaces all bits and can change other gates.

The hardware snippet loads all six gate control/readback records directly,
even when default substitutions are disabled. Output records use
`PINI=0`/`NO` so initialization preserves the configured gates.

## Separate software-PWM frequency test

`examples/PSI/lab_setup/N6/startup_software_pwm.cmd` is an isolated bench
candidate for fixed-frequency software PWM. It uses `_OPT` for masked output
gates, loads no motion axis, and keeps the drive disabled with zero velocity.
The test selects 5 V I/O and leaves the output gate disabled until explicitly
armed. The companion `README_software_pwm.md` contains the scope procedure.

The reusable SDO configuration is now in ecmccomp. The startup applies:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PWMOutput,CH_ID=1,MACROS='FREQUENCY_HZ=2000,DUTY_PERCENT=50,OUTPUT=1,PWM_ID=0,ARM=0,N6_IO_24V=0'"
```

| Component macro | Default | Meaning |
| --- | --- | --- |
| `FREQUENCY_HZ` | `2000` | Plain integer 50..2000 Hz |
| `DUTY_PERCENT` | `50` | Plain integer 0..100 percent; 0/100 give constant endpoints |
| `OUTPUT` | `1` | Physical output 1..3 |
| `PWM_ID` | `0` | Generator 0 (`3260`, source `0x12`) or 1 (`3261`, source `0x13`) |
| `ARM` | `0` | Initial selected-output gate |
| `N6_IO_24V` | `0` for first output; then inherit | Shared voltage selection |
| `N6_INPUT_PULLUP` | Inherit motor | Shared input bias |

Apply it after the motor and N6_OPT. Outputs sharing a PWM_ID must use the
same frequency/duty. PositionOutput and PWMOutput may use different physical
outputs on one drive, but cannot claim the same output or disagree on shared
I/O settings. The motor cannot be reapplied after either output component.
Generator 0 / output 1 / 2 kHz / 50% is the bench-reported case; other
choices still require commissioning. No extra frequency/duty PVs are added.

The EtherCAT manual distinguishes a **2 kHz software-PWM** limit from the
**500 Hz** limit for other output sources. PWM is a fixed-frequency signal,
not a faster position-divider mode. A successful PWM measurement does not
prove that the 100-full-step position output can exceed its documented limit.
A PWM carrier gated by position is also not automatically phase-aligned to
position or guaranteed to produce one pulse per compare point.

The candidate uses `3260:01=2000` Hz, `3260:02=50` percent and
`3252:02=0x1210` (PWM 0 to output 1, gated by bit 16). Source `0x12` is
explicitly listed in the newer
[N6 Modbus TCP manual v1.2.1 for FIR-v2542](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_ModbusTCP_Technical-Manual_V1.2.1.pdf),
section 7.1.2.3. The older EtherCAT v1.1.0 table omits that source despite
listing the PWM parameter objects. The user subsequently reported the PWM test working on the EtherCAT drive
on 2026-10-28. Numerical frequency/duty/jitter measurements were not supplied;
this is evidence for that tested setup, not other variants.

Run the dedicated startup instead of the position-output startup, connect
the scope to X4 pin 5 / GNDD pin 8, then arm `PosOut01-Ena`. Expected at
2 kHz/50%: a 500 microsecond full period with 250 microseconds high and low.
Disarm after measurement. The test also accepts 500, 1000 and 1500 Hz by
changing `FREQUENCY_HZ` in its component call and restarting. These are
checkpoints, not the only supported integer frequencies. No extra PDOs, motor
motion or drive-flash writes are needed. Restart the original 100-step
startup to restore position routing. The output was reported working; exact
frequency, duty and jitter still need recorded scope measurements.

No counter-clock input is documented for `3260`; it provides frequency and
duty parameters. Output routing selects PWM or position, and its gate is a
`60FE:01` bit. A PLC may gate PWM over a position window, but this gives
bursts of a time-based carrier rather than one edge per motor-step interval.
It does not bypass the documented 500 Hz position-divider limit.

## Drive homing method 35

Method 35 references the drive's **current position without a homing move**.
With home offset 0 it can establish the zero of logical position `6064`,
the source used for the periodic output. The manual explicitly states that
raw `6063` is not zeroed by drive homing. Referencing the ecmc axis using an
offset also leaves the drive counter unchanged and does not itself
reference the drive-side output source.

The observed first-edge shift after method 35 is described below. Drive
referencing and ecmc axis-coordinate referencing remain separate operations,
coordinated by sequence 26 in the example.

### PDOs and panel records

With `HOMING=1`, the process image initializes `homingMethod01=35` and
`homeOffset01=0`. It also maps the drive homing dynamics, initialized to the
manual's presets: switch-search speed 50, zero-search speed 10 and
acceleration 500. These are drive-defined user-unit values, separate from
the YAML homing parameters used by ecmc. Method 35 makes no search move;
configure and verify these values before using other drive homing methods.
Mode remains CSV (9) until a sequence changes it.

| Entry | Object/type | Purpose |
| --- | --- | --- |
| `homingMethod01` | `6098:00`, S8 | Homing method; optional PDO |
| `homeOffset01` | `607C:00`, S32 | Offset in configured `6064` units; optional PDO |
| `homingVelocitySwitch01` | `6099:01`, U32 | Switch-search speed; initialized to 50 |
| `homingVelocityZero01` | `6099:02`, U32 | Zero/index-search speed; initialized to 10 |
| `homingAcceleration01` | `609A:00`, U32 | Drive homing acceleration; initialized to 500 |
| `modeControl01` | `6060:00`, S8 | Mode command: 6 homing, 9 CSV; already mapped |
| `modeActual01` | `6061:00`, S8 | Mode acknowledgment; already mapped |
| `driveControl01` | `6040:00`, U16 | Axis-owned controlword; already mapped |
| `driveCmdExe01` | B1 alias of `6040` bit 4 | Sequence-26 trigger; present with `HOMING=1` |
| `driveStatus01` | `6041:00`, U16 | Homing completion/error and drive status; already mapped |

With the 100-full-step position unit, a home offset of 1 means 100 full
steps (180 degrees on the tested motor), not one native encoder increment.
Use offset 0 when referencing the current scaled position to zero.

Additional PVs are `Drv01-HomeMethod`, `Drv01-HomeOffset` and
`Drv01-ModeCmd`, each with `-RB`, plus `Drv01-ModeAct`. Their command
readbacks report the process-image command values; `Drv01-ModeAct` is the
drive's actual mode acknowledgment. Command records use `PINI=0` so IOC
initialization does not overwrite the initialized method, offset or mode.
Additional command/readback pairs are `Drv01-HomeVelTo`, `Drv01-HomeVelFrm`
and `Drv01-HomeAcc`, also with `PINI=0`. Edit them while the axis is idle.
The EPICS edits use the nonnegative asynInt32 range; the mapped PDO type is U32.

### Use axis homing sequence 26

The dedicated axis YAML now uses the existing drive-triggered homing sequence
`26` (`ECMC_SEQ_HOME_TRIGG_EXTERN`), also used for SmarAct MCS2. No separate
PLC or C++ homing state machine is required for the example.

```yaml
axis:
  mode: CSV
  autoMode:
    modeSet: ec0.s$(DRV_SID).modeControl01
    modeAct: ec0.s$(DRV_SID).modeActual01
    modeCmdMotion: 9
    modeCmdHome: 6

encoder:
  homing:
    type: 26
    position: 0
    trigg: ec0.s$(DRV_SID).driveCmdExe01.0
    ready: ec0.s$(DRV_SID).driveStatus01.12
    refAtHome: 1
    timeout: 10
    velocity:
      to: 18
      from: 18
    acceleration: 36
    deceleration: 36
    postMoveEnable: true
    postMovePosition: 0
```

This is an excerpt; retain the fine counter mapping and other axis settings
from the complete example. The nonzero homing velocities/accelerations
satisfy generic axis validation; drive method 35 makes no search move.

Sequence 26 switches to mode 6 and waits for the mode acknowledgment, asserts
the trigger, waits for a rising edge on statusword bit 12, clears the trigger
and references the ecmc encoder to `position` (zero here). The raw drive
counter and `Enc01-PosAct` remain unchanged; the axis position gains its
engineering offset. Normal axis enabling applies, so the motor may energize
even though bare drive method 35 itself does not require Operation enabled.

The existing sequence restores mode 9 through its post-home stage. Therefore
`postMoveEnable` is deliberately true, with `postMovePosition` equal to the
home position. This waits for CSV mode acknowledgment and skips the move
because the referenced position already equals the target. If these two
positions are changed, keep them equal unless an actual post-home move is
intended. The example uses a 10-second sequence timeout.

### Trigger from the motor record

After installing/restarting with `RAW_POS=1,HOMING=1` and the dedicated YAML:

1. Stop the axis and disable the output gate using `PosOut01-Ena=0`.
2. Verify the Home tab shows method 35 and offset 0. Leave automatic mode
   switching to the axis; do not manually change mode while it is active.
3. Use the normal M1 motor-record **Home Forward** or **Home Reverse**
   command. For method 35 the direction does not request a search move.
   The axis homing procedure is 26; this is distinct from drive method 35.
4. Verify homing completes, the axis reads its configured home position,
   `Drv01-ModeAct` returns to 9 and `Enc01-PosScaled` shows the expected
   referenced drive position. Re-arm the output after checking the result.

For example, substituting the actual PV prefixes:

```bash
caput <slave-prefix>PosOut01-Ena 0
caput <axis-motor-record>.HOMF 1
# After successful homing and verification:
caput <slave-prefix>PosOut01-Ena 1
```

The example's motor record is named M1 under its configured IOC prefix.
The output gate is not automatically coordinated with axis homing; these
commands are separate. The hardware Home tab provides parameters and
status; use the axis panel/motor record to start sequence 26.

On failure or timeout, stop/reset through the normal axis controls and
verify the trigger is cleared and mode 9 is restored before resuming
motion. Mode restoration after a successful home uses the post-home stage;
do not assume an aborted sequence has completed that stage.

### Why the trigger uses a separate bit alias

The DS402 axis writes its full controlword every cycle. Sequence 26 writes
its trigger earlier in the axis execution, so directly linking
`trigg` to `driveControl01.4` would let the later whole-word write clear it.

With `HOMING=1`, the snippet instead adds:

```text
Cfg.EcAddDataDT(ec<master>.s<slave>.driveControl01,0,4,1,B1,driveCmdExe01)
```

This follows the MCS2 approach. The B1 alias is initialized to zero and
appended after the parent entry. During output-image transfer the parent
controlword is written first; the alias then replaces only bit 4, preserving
the other bits. Sequence 26 owns this alias and clears it when finished or
stopped. The alias is not an additional PDO mapping.

### Alternative PLC/C++ integration

The inspected ecmc RT loop executes in this order:

```text
Axis-local PLC → motion axis → C++ logic → normal global PLCs → EtherCAT send
```

A normal global PLC can override an axis command after the axis executes;
an axis-local PLC cannot reliably override the parent's whole-word writes.
However, with `HOMING=1`, the trigger alias is applied during output-image
transfer after those writes. A custom PLC/C++ homing implementation must
therefore write `driveCmdExe01.0`, not just `driveControl01.4`, and must not
compete with sequence 26 for that alias. Coordinate mode, velocity, axis
commands, timeout and output gates explicitly when replacing the built-in
sequence. Do not run both trigger owners together.

The execution order and writes were checked in `ecmcMainThread.cpp`,
`ecmcDriveBase.cpp`, `ecmcAxisSequencer.cpp`, `ecmcEcSlave.cpp` and
`ecmcEcData.cpp`. Verify the behavior in the deployed ecmc version when
using a custom override.

### Repeatable first-edge shift after homing (2026-10-28)

On the tested 100-full-step setup, a fresh start produced the first output
edge after **100 full steps**. After method-35 homing, the first edge was
observed after **50 full steps**, followed by transitions after another
100 steps: **50, 150, 250, ...** full steps of subsequent motion. This
behavior was repeatable. The scaled position was reported to return to zero
on homing.

The observation is a shift of the first-edge position; the following
edge spacing remains 100 full steps. Here “edge” means an output state
change, not a complete high/low pulse cycle. For the tested 200-step motor,
50 steps are 90 degrees and 100 steps are 180 degrees.

Homing once after startup, before beginning a measurement, is therefore a
proposed way to obtain a consistent first edge after 50 full steps. The
example does **not** automatically home at startup: command the normal M1
home sequence, verify completion and CSV restoration, then begin the
measurement. Coordinate the output gate as described above. This proposal
uses the reported repeatability; it does not establish behavior for other
firmware, intervals, directions or restart conditions.

### Homing checks still needed on the drive

Sequence 26 detects a rising edge on the configured ready bit. Verify first
and repeated method-35 requests: statusword bit 12 may already be high from
a previous home, and a fast operation must still produce an observable
completion transition. The sequence has no separate configured input for
homing-error bit 13; monitor it in the Home tab and verify timeout/error
behavior. Also check statusword bit 10, trigger clearing, mode restoration
and first-edge behavior under other motion/restart conditions. The
repeatable 100-step/50-step first-edge observation above does not establish
all these cases. These are hardware commissioning checks, not outcomes
established by the configuration tests.

## Records and panels

| PV suffix | Meaning |
| --- | --- |
| `Enc01-PosAct` | Fine `6063` counter with `RAW_POS=1`; otherwise legacy `6064` |
| `Enc01-PosScaled` | Scaled `6064`; present with `RAW_POS=1` |
| `PosOut01-Ena` through `PosOut03-Ena` | Individual output gates, each with `-RB` |
| `CfgRawPosition` | Resolved raw-position option, read-only |
| `CfgHoming` | Resolved homing option, read-only |
| `CfgCapture` | Resolved capture option, read-only |
| `CfgAnalogIn` | Resolved analog input option, read-only |
| `BO01-Arr` | Complete output word, including the brake and output gates |

The hardware selects `ecmcN6-1-1-1-S_OPT.ui` and
`ecmcN6-1-1-1-S_OPT_expert.ui`. The usual position field shows fine feedback
with `RAW_POS=1`; the additional scaled field is visible with
`CfgRawPosition=1`. Counter readouts use integer precision.

Both displays have a Home tab. `CfgHoming=1` reveals its homing fields;
otherwise it reports that the PDOs are not mapped. The compact tab shows
method, offset and actual mode readbacks. The expert tab adds editable
parameters/mode, command readbacks and statusword bits 10, 12 and 13.
The expert display also retains the output gate controls and readbacks.
The Home tab separates Mode and Speed fields; Speed shows the new drive
homing dynamics (editable in Expert, read-only in the compact display).
Capture and Analog tabs expose their optional readbacks only when
`CfgCapture=1` / `CfgAnalogIn=1`. Capture has Home, In 3 and In 4 sub-tabs;
its control fields are readbacks, not writable arming controls.
The original panels remain available for the base descriptor.

After installing updated files, restart the IOC to load new records and
reopen the panel to load its new layout. Changing the panel alone does not
add missing IOC records.

## Commissioning evidence and troubleshooting

The bench measurements support using raw `6063` as the fine open-loop
counter on FIR-v2542-B1080909 with `60E6:01=0`. One approximate revolution
changed `6063` by 3,270,300 counts (about 359.29 degrees at the nominal scale)
and `6064` by two counts. The fine-counter axis and the 100-step output were
then reported working together.

The manual warns that `6063` values are invalid when the interface
resolution is zero. The observed open-loop behavior is therefore specific
evidence for this firmware/setup, not a guarantee for other firmware,
motor modes or sensors. Hardware-free checks cover mapping, component
validation, record links, gate masks and panel compilation/visibility;
they do not establish the drive's waveform or homing behavior.

### Earlier pulse-generator attempts

The initial `205C` pulse-generator approach tried to retain native `6064`
units. At 16,384 increments/full step, 100 full steps require a divider of
1,638,400, which does not fit the documented 16-bit ratio. A trial with one
pulse per full step still failed when selecting the pulse-generator source:
`3203:01=8` repeatedly aborted with `0x06040047` (internal incompatibility).

Enabling nominal sensorless resolution with `60E6:01=3276800` subsequently
produced drive error `7305h` (sensor 1 faulty). The working configuration
keeps `60E6:01=0`, leaves feedback selection unchanged and writes neither
`3203` nor `205C`. The earlier pulse-generator example files are failed
prototypes, not the recommended configuration.

### Useful readbacks

For the lab master 1, slave 0; adjust these addresses for another setup:

```bash
ethercat upload -m1 -p0 --type string 0x100A 0
ethercat upload -m1 -p0 --type uint16 0x6041 0
ethercat upload -m1 -p0 --type uint16 0x603F 0
ethercat upload -m1 -p0 --type uint32 0x60E6 1
ethercat upload -m1 -p0 --type uint32 0x60A8 0
ethercat upload -m1 -p0 --type uint16 0x3252 2
ethercat upload -m1 -p0 --type int32 0x6063 0
ethercat upload -m1 -p0 --type int32 0x6064 0
```

For the 100-step/output-1 setup, expect `60E6:01=0`,
`60A8=0x02AC0000` and `3252:02=0x0910`. Sequential SDO uploads are not a
simultaneous position sample; stop motion when comparing paired readings.

`6041` bit 3 identifies an active drive fault. `603F` reports the last error
and may retain `7305` after its cause has gone. Reset a latched fault using
the normal drive controls once the cause is resolved. An SDO controlword
write while the axis owns the cyclic PDO will be overwritten.

For blank gate or homing fields, check record existence in the IOC shell:

```text
dbgrep *PosOut*
dbgrep *CfgHoming*
dbgrep *HomeMethod*
```

There should be three gate controls and three gate readbacks. Homing
parameter records are present only with `HOMING=1`; capture and analog
records similarly require their options. Missing records require
updating the loaded configuration/database files and restarting the IOC.

## Sources and related configuration

- [Nanotec N6 EtherCAT technical manual, FIR-v2508, version 1.1.0](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.1.0.pdf): method 35 in section 6.4.2.11; object entries `6063`, `607C`, `6098`, `323A` and `3252`.
- [Base N6 configuration]({{< relref "Nanotec-N6.md" >}}).
- [ecmc homing sequences]({{< relref "/manual/motion_cfg/homing.md" >}}).
- `examples/PSI/lab_setup/N6/README_position_output_100_steps.md`: lab setup and commissioning notes.
- ecmccomp `docs/N6_position_output.md`: component interface and constraints.

### Ownership of the N6 configuration snippets

Reusable SDO setup belongs in ecmccomp. Hardware PDOs, records and panels
remain in ecmccfg, and examples choose components and parameter values.

| N6 lab file | Status |
| --- | --- |
| `cfg/position_output_100_steps.cmd` | Compatibility wrapper for existing `Drive-Generic-PositionOutput` |
| `cfg/software_pwm_2khz.cmd` | Compatibility wrapper for new `Drive-Generic-PWMOutput` |
| `cfg/pulse_per_fullstep.cmd` | Failed pulse-generator reproducer; not a supported component |
| `cfg/disable_pulse_source.cmd` | Lab-specific recovery for that failed trial; resets whole output word and feedback selections |
| Axis YAML files | Axis configuration: scaling, motion settings and sequence-26 homing |

Use masked gate PVs to disarm supported outputs normally. The failed trial
and its broad recovery are deliberately not packaged as reusable components.
