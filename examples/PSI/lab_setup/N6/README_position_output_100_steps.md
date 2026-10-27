# Dedicated output and fine open-loop counter trial: 100 full steps

Use `startup_position_output_100_steps.cmd` instead of the original startup
or the failed `startup_pulse_per_fullstep.cmd`. Run from this directory and
restart the IOC so the previous configuration is discarded. The installed
ecmccfg must include `ecmcN6-1-1-1-S_POS_OUT.cmd`.

The output was reported working in the drive-only bench test. Subsequent SDO
readings support using `6063` as the fine open-loop counter on the tested
FIR-v2542-B1080909 firmware while `60E6:01=0`. The dedicated startup now maps
that counter and loads its axis YAML. **Cyclic feedback and axis operation
still require commissioning.**

## Dedicated files

| File | Purpose |
| --- | --- |
| `startup_position_output_100_steps.cmd` | Output trial with the M1 axis |
| `cfg/position_output_100_steps.cmd` | Sensorless interface off; position units and output routing |
| `cfg/axis_position_output.yaml` | Axis feedback from fine `positionActualRaw01` |
| `hardware/Nanotec/ecmcN6-1-1-1-S_POS_OUT.cmd` | Base N6 mapping plus `6063:00` in existing PDO `1A03` |

The original `startup.cmd`, `cfg/axis.yaml` and base N6 descriptor are unchanged.
There are still four TxPDO assignments; the extra raw entry is appended to
`1A03`, which becomes 20 bytes.

## Two simultaneous position values

| Value | Units | Use |
| --- | --- | --- |
| `6063`, `positionActualRaw01` | Native counter increments; nominally 3,276,800/revolution | Axis feedback |
| `6064`, `positionActual01` | 100 full motor steps/count; two counts/revolution | Direct drive-side output |

The M1 axis position readback is in degrees and uses `360/3276800` scaling.
The normal N6 `Enc01-PosAct` drive record and panel still display coarse
`6064`; use the M1 axis readback to observe fine position. Additional `60E4`
positions also use the changed position units. Velocity remains in native
increments/second, with matching `360/3276800` drive scaling and `INV_DIR=0`.

This is the generated open-loop motor counter, not measured rotor position;
it does not detect lost motor steps. Raw `6063` does not reset during drive
homing; use ecmc axis referencing when setting the axis coordinate.

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
| Existing `60FE:01` PDO | `65536` | Enable output 1; other output bits zero |

There are no writes to `3203` or `205C`. The original feedback-selection
masks must remain zero. `PINI=0` prevents record initialization from
overwriting the gate; `BO01-Arr=0` disarms it and `65536` rearms it. This
replaces the whole output word, with the brake-control bit and other outputs zero.

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
records manually while the axis controller owns those PDOs. The dedicated
YAML starts at 18 degrees/second, 36 degrees/second squared, with a 10-degree
tweak and a 5-degree following-error tolerance. Begin with a small move and
confirm fine, correctly signed M1 feedback. Stop if it fails to follow.
Then check reverse motion, stop/restart and eventual signed-counter rollover.
The lab's constant limit/interlock inputs match the original example.

## Output measurement

Output 1 is **X4 pin 5**, with GNDD on **X4 pin 8**. Output level is nominal
24 V/+UB_Logic. Use a compatible scope or counter input.

The target spacing is 100 full steps = 180 degrees, or ten seconds at a
steady 18 degrees/second. Expect two pulses per revolution over repeated
revolutions; verify pulse width, phase, reversal and stop/restart separately.
The routing limit is 500 Hz. No absolute compare point or pulse width is programmed.

## Return to the original axis

Stop and disable the drive, then restart with the original `startup.cmd`.
For full restoration of routing and interface settings, load
`cfg/disable_pulse_source.cmd` after the motor component and before applying
EtherCAT configuration. The normal component restores native position units.
No script saves settings to drive flash.
