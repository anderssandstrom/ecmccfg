# Dedicated output and fine open-loop counter trial: 100 full steps

Use `startup_position_output_100_steps.cmd` instead of the original startup
or the failed `startup_pulse_per_fullstep.cmd`. Run from this directory and
restart the IOC so the previous configuration is discarded. Build/install
both updated modules: ecmccfg must include N6_OPT and ecmccomp must include
`Drive-Generic-PositionOutput`.

The output was reported working in the drive-only bench test. Subsequent SDO
readings support using `6063` as the fine open-loop counter on the tested
FIR-v2542-B1080909 firmware while `60E6:01=0`. The dedicated startup now maps
that counter and loads its axis YAML. The user confirmed the fine-counter
axis and 100-step output working together with the interface disabled. The
new packaging and masked gate controls still require a bench recheck.

## Dedicated files

| File | Purpose |
| --- | --- |
| `startup_position_output_100_steps.cmd` | Output trial with the M1 axis |
| ecmccomp `Drive-Generic-PositionOutput` | Sensorless interface off; position units and output routing |
| `cfg/axis_position_output.yaml` | Axis feedback from fine `positionActual01` |
| `hardware/Nanotec/ecmcN6-1-1-1-S_OPT.cmd` | `RAW_POS=1` adds `6063:00` in existing PDO `1A03` |

The original `startup.cmd`, `cfg/axis.yaml` and base N6 descriptor are unchanged.
There are still four TxPDO assignments; the extra raw entry is appended to
`1A03`, which becomes 20 bytes.

## Packaged startup

The example now uses the reusable hardware option and component:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1,HOMING=1'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PositionOutput,MACROS='FULL_STEPS=100,OUTPUT=1,ARM=1'"
```

Apply the output component after the motor. It checks the raw mapping,
startup order and supported interval. Its default is `ARM=0`; the example
explicitly arms output 1. Supported intervals are `10^n` times
`1,2,4,8,16,32,64` with `n=0..6`; outputs 1..3 are supported. Different
outputs on the same drive must share the canonical position-unit exponent.
Motor `INV_DIR=0` is required. The local `cfg/position_output_100_steps.cmd`
remains a compatibility wrapper; the dedicated `_POS_OUT` hardware descriptor
has been replaced by `_OPT`.

## Two simultaneous position values

| Value | Units | Use |
| --- | --- | --- |
| `6063`, `positionActual01` | Native counter increments; nominally 3,276,800/revolution | Axis feedback |
| `6064`, `positionActualScaled01` | 100 full motor steps/count; two counts/revolution | Direct drive-side output |

The M1 axis position readback is in degrees and uses `360/3276800` scaling.
With `RAW_POS=1`, `Enc01-PosAct` displays the fine `6063` open-loop counter.
The OPT panels show it alongside `Enc01-PosScaled` for `6064`; the scaled field is visible
only with `RAW_POS=1`. Use the M1 axis readback for position in degrees. Additional `60E4`
positions also use the changed position units. Velocity remains in native
increments/second, with matching `360/3276800` drive scaling and `INV_DIR=0`.

This is the generated open-loop motor counter, not measured rotor position;
it does not detect lost motor steps. Raw `6063` does not reset during drive
homing; use ecmc axis referencing when setting the axis coordinate.

## Axis-triggered drive homing (method 35)

The example enables `HOMING=1` and configures the normal axis homing
sequence **26**, as used for SmarAct MCS2. The drive's homing method is
**35** (reference current position), with home offset 0. These are two
different settings: sequence 26 coordinates the axis; method 35 runs in
the drive. Homing does not run automatically at IOC startup.

The option appends `homingMethod01` (S8, `6098:00`) and `homeOffset01`
(S32, `607C:00`) to RxPDO `1603`, increasing it to nine bytes. It also adds
a B1 output-data alias, `driveCmdExe01`, over controlword bit 4; that alias
adds no PDO bytes. Initial values are method 35, offset 0 and trigger 0.
Mode control/display and drive control/status are already mapped.

The axis YAML uses:

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
    postMoveEnable: true
    postMovePosition: 0
```

These are excerpts; retain the complete YAML, including its nonzero generic
homing velocities/accelerations. Method 35 does not make a search move.
Sequence 26 follows normal axis enabling and may energize the motor.

To reference:

1. Stop motion and disarm output 1 using `<slave-prefix>PosOut01-Ena=0`.
2. Verify method 35 and offset 0 in the Home tab.
3. Use the normal M1 **Home Forward** or **Home Reverse** command, for example
   `caput <axis-motor-record>.HOMF 1`.
4. Verify completion, the ecmc axis position at zero, scaled `6064` referenced
   and actual mode back at 9. Re-arm the output when the result is verified.

Sequence 26 switches to mode 6, waits for acknowledgment, asserts the
trigger, detects a rising ready bit 12, clears the trigger and references
the ecmc encoder object. Its post-home stage restores CSV and waits for
acknowledgment. `postMoveEnable=true` is intentional: keeping its target
identical to the home position makes that stage restore mode without an
extra move. Changing those positions can introduce a real post-home move.
On timeout/failure, stop/reset the axis and verify trigger clearing and
mode restoration before resuming motion.

The alias is necessary because the DS402 axis writes its whole controlword
later than sequence 26 sets the trigger. At process-image transfer, the
parent word is applied first, then the B1 alias replaces only bit 4.
Linking directly to `driveControl01.4` would lose the trigger. A global PLC
runs after the axes, but custom logic must also use the alias when HOMING
is mapped and must not compete with sequence 26 for it.

The Home tab displays method, offset, mode and status. The expert tab edits
parameters; the motor-record/axis panel starts the coordinated sequence.
Homing parameter PVs are `Drv01-HomeMethod`, `Drv01-HomeOffset`,
`Drv01-ModeCmd` (each with `-RB`) and `Drv01-ModeAct`. `CfgHoming` hides
optional fields when the interface is not mapped. Output parameter records
use `PINI=0` to preserve initialization.

Drive method 35 references logical `6064`; raw `6063` and `Enc01-PosAct`
remain unchanged. Sequence 26 separately offsets the ecmc axis to its home
position. The output gate is not automatically coordinated with this
sequence. Verify its pulse phase/first pulse after referencing on the bench.

The integration still needs commissioning on FIR-v2542-B1080909, especially
repeated method-35 completion: bit 12 must provide an observable rising
edge. Sequence 26 has no separate homing-error-bit input, so check bit 13
and timeout behavior as well. Full details are in the Hugo N6 OPT guide
and `manual/motion_cfg/homing.md` (sequence 26).

## Bench evidence and remaining checks

The user recorded these pairs with the sensorless interface disabled:

| Reading | Raw `6063` | Scaled `6064` |
| --- | ---: | ---: |
| Before | 1,131,727,804 | 691 |
| After approximately one revolution | 1,134,998,104 | 693 |
| Difference | 3,270,300 | 2 |

The raw difference corresponds to 359.29 degrees at the nominal native scale,
consistent with the reported approximate revolution and coarse count change.
This supports a fine open-loop counter; it is not a precision calibration or
verification of reversal, rollover, restart behavior or closed-loop axis operation.

The [FIR-v2542 manual](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.2.1.pdf?1773317058=)
warns that `6063` is invalid with zero interface resolution. The empirical
open-loop readings above are firmware-specific evidence, rather than a general
claim that the warning can be ignored for every mode or firmware.

Earlier attempts set `60E6:01=3276800` and produced `7305h`, sensor 1 faulty.
Do not re-enable that sensorless interface: nominal resolution alone does
not commission its observer. No simulated encoder is substituted.

## Settings

| Setting | Value | Meaning |
| --- | --- | --- |
| `60E6:01` | `0` | Sensorless interface remains disabled |
| `60A8:00` | `0x02AC0000` | `6064` unit is 100 full motor steps |
| `3252:02` | `0x0910` | Output 1 follows `6064` count changes, divider 1, gate bit 16 |
| `60FE:01` PDO bit 16 | `1` | Enable output 1; preserve all other bits |

There are no writes to `3203` or `205C`. The original feedback-selection
masks must remain zero. Use `PosOut01-Ena=0` to disarm and `1` to rearm
output 1. These masked controls and the component change only the selected
bit. Output records avoid initialization writes that could clear the gate.
Direct writes to `BO01-Arr` still replace the entire word; avoid them when
other outputs or brake control are in use.

## Commissioning the axis

Keep the drive stationary during the initial checks:

```sh
ethercat upload -m1 -p0 --type uint32 0x60E6 1
ethercat upload -m1 -p0 --type uint32 0x60A8 0
ethercat upload -m1 -p0 --type uint16 0x3252 2
ethercat upload -m1 -p0 --type uint32 0x3202 0
ethercat upload -m1 -p0 --type uint8  0x3203 1
ethercat upload -m1 -p0 --type int32  0x6063 0
ethercat upload -m1 -p0 --type int32  0x6064 0
ethercat upload -m1 -p0 --type uint16 0x6041 0
```

Expected settings are those above, `3202=0`, `3203:01=0`. Check statusword
`6041` bit 3 for an active drive fault; `603F` reports the last error and can
retain `7305` after its cause is removed. Reset a latched fault with the
drive stationary through the normal controls.

Use the M1 motor record for motion. Do not write the drive velocity/control
records manually while the axis controller owns those PDOs. Motion settings are configured in the dedicated YAML; begin with values
appropriate for the bench setup. The axis uses a 10-degree tweak and a
5-degree following-error tolerance. Begin with a small move and
confirm fine, correctly signed M1 feedback. Stop if it fails to follow.
Then check reverse motion, stop/restart and eventual signed-counter rollover.
The lab's constant limit/interlock inputs match the original example.

## Output measurement

Output 1 is **X4 pin 5**, with GNDD on **X4 pin 8**. The output defaults to
**5 V**. To select nominal 24 V/+UB_Logic, add `N6_IO_24V=1` to the
`Drive-Generic-PositionOutput` component macros. `N6_INPUT_PULLUP=0` selects
pull-down inputs (default inherited from the motor); `1` selects pull-up.
The voltage selector also changes the shared digital input thresholds.
These options do not configure the motor power supply. Use a compatible
scope or counter input.

The target spacing is 100 full steps = 180 degrees. Pulse period in seconds
is `180 / abs(velocity in degrees/second)` (for example ten seconds at 18
degrees/second). Expect two pulses per revolution over repeated
revolutions; verify pulse width, phase, reversal and stop/restart separately.
The routing limit is 500 Hz. No absolute compare point or pulse width is programmed.

## Return to the original axis

Stop and disable the drive, then restart with the original `startup.cmd`.
For full restoration of routing and interface settings, load
`cfg/disable_pulse_source.cmd` after the motor component and before applying
EtherCAT configuration. The normal component restores native position units.
No script saves settings to drive flash.
