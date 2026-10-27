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

## Optional drive homing interface (method 35)

The example enables `HOMING=1` in `_OPT`. This maps parameters for a PLC or
C++ logic state machine; **it does not execute homing at startup**. Without
this option the original RxPDO layout is unchanged. The two extra entries
are appended to existing RxPDO `1603` (9 bytes total); no additional RxPDO
assignment slot is used. The initialized method is 35 and home offset is 0.

| EtherCAT entry | Object | Type | Purpose |
| --- | --- | --- | --- |
| `homingMethod01` | `6098:00` | S8 | Homing method; initialized to 35 |
| `homeOffset01` | `607C:00` | S32 | Home offset in configured `6064` units; initialized to 0 |
| `modeControl01` | `6060:00` | S8 | Already mapped; 6 = homing, 9 = CSV |
| `modeActual01` | `6061:00` | S8 | Already mapped; confirms the selected mode |
| `driveControl01` | `6040:00` | U16 | Already mapped; bit 4 starts homing |
| `driveStatus01` | `6041:00` | U16 | Already mapped; bits 12/13 report attained/error |

With `HOMING=1`, additional diagnostic/control PVs are `Drv01-HomeMethod`,
`Drv01-HomeOffset`, `Drv01-ModeCmd` (each with `-RB`) and `Drv01-ModeAct`.
Output records use `PINI=0` so IOC initialization does not overwrite the
method 35, zero offset or CSV mode initialized in the process image.
The OPT panels have a Home tab. With `HOMING=1`, the compact tab displays
method, offset and actual mode; the expert tab adds edits and homing status
bits. `CfgHoming` hides these fields when the PDOs are not mapped.
These PVs are low-level controls, not a coordinated homing trigger.

A drive-referencing state machine should:

1. Obtain exclusive ownership of the drive command PDOs, stop motion, hold
   target velocity at zero, and disable the position-output gate.
2. Write method 35 and offset 0, clear controlword bit 4, select mode 6, and
   wait for `modeActual01=6`.
3. Start homing with a rising edge on controlword bit 4. Method 35 does not
   require Operation enabled; do not energize the motor merely to reference.
4. Check completion for this request (statusword bits 12 and 10 set), bit 13
   clear and fault bit 3 clear, with a timeout. Do not accept an old attained
   bit as proof that a new request has executed. Check scaled `6064` as well.
5. Clear bit 4, restore mode 9, wait for `modeActual01=9`, then release command
   ownership. Leave the drive disabled on errors; re-arm the output only after
   successful referencing and application checks.

**Disabling M1 is not sufficient to obtain command ownership.** The ecmc
DS402 axis writes the full controlword and velocity setpoint every cycle,
even when disabled. An ordinary PLC/PV write can therefore be overwritten.
Run the sequence while no axis owns those entries, or provide an explicit
ownership mechanism in the C++/PLC integration. The example maps the interface
but deliberately does not install an uncoordinated automatic sequence.

Method 35 references logical `6064`; the fine `6063` counter remains unchanged.
Zero the ecmc axis coordinate separately if required. Test the effect on the
direct output's phase and first pulse on the bench before depending on it.
The mapping and homing behavior need verification on FIR-v2542-B1080909.
See the [Nanotec N6 manual](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.1.0.pdf),
sections 6.4, 607Ch and 6098h.

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
