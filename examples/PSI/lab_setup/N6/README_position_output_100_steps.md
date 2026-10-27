# Dedicated drive-only output trial: 100 full steps

Use `startup_position_output_100_steps.cmd` instead of the original startup
or the failed `startup_pulse_per_fullstep.cmd`. Run from this directory.
This revision uses the existing N6 hardware descriptor and needs no new PDOs.

**This is now a drive-only bench test. It loads no ECMC axis and starts no
motion automatically.** Manual drive commands have no ECMC axis ramps or
limit monitoring; use them only on the lab motor with suitable clearance.
The position-divider output itself remains unverified on hardware.

## Why the raw-feedback axis was withdrawn

The previous trial set `60E6:01=3276800` to obtain raw `6063` feedback. The
drive subsequently reported `7305h`, sensor 1 faulty. Sensor 1 is the
internal/sensorless interface. A nonzero resolution enables sensor checking;
setting nominal resolution alone does not commission a sensorless observer.

The [FIR-v2542 manual](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.2.1.pdf?1773317058=)
also warns that `6063` is invalid when the interface resolution is zero.
The trial therefore restores `60E6:01=0` and **does not use `6063` for axis
feedback**. It does not substitute simulated feedback or use coarse `6064`
as feedback to the original fine-position controller.

`cfg/axis_position_output.yaml` and the `N6-1-1-1-S_POS_OUT` descriptor are
retained as diagnostic artifacts. They are not loaded by the active trial.
Restoring a functioning position-controlled axis with high-resolution
feedback requires a valid commissioned feedback source; that is unresolved.

## Active dedicated files

| File | Purpose |
| --- | --- |
| `startup_position_output_100_steps.cmd` | Drive-only startup, no axis |
| `cfg/position_output_100_steps.cmd` | Disable sensorless interface; configure units and output |

The original `startup.cmd`, `cfg/axis.yaml`, and base hardware descriptor are
unchanged. Restart the IOC with the dedicated startup so the previous SDO
queue and raw-feedback axis are discarded.

## Settings

| Setting | Value | Meaning |
| --- | --- | --- |
| `60E6:01` | `0` | Restore disabled sensorless interface |
| `60A8:00` | `0x02AC0000` | `6064` unit is 100 full motor steps |
| `3252:02` | `0x0910` | Output 1 follows `6064` count changes, divider 1, gate bit 16 |
| Existing `60FE:01` PDO | `65536` | Enable output 1; other output bits zero |

There are no writes to `3203` or `205C`. The original feedback-selection
masks must remain zero. Velocity stays in native increments/second.
The normal `Enc01-PosAct` drive record shows the scaled `6064` position:
two counts/revolution for this 200-full-step motor. Do not interpret it as
native counts or degrees. Additional `60E4` positions also use the new units.

## Check configuration before motion

```sh
ethercat upload -m1 -p0 --type uint32 0x60E6 1
ethercat upload -m1 -p0 --type uint32 0x60A8 0
ethercat upload -m1 -p0 --type uint16 0x3252 2
ethercat upload -m1 -p0 --type uint32 0x3202 0
ethercat upload -m1 -p0 --type uint8  0x3203 1
```

Expected values are those above, `3202=0` and `3203:01=0`. Reset the latched
drive fault using the usual DS402 reset/enable sequence only after the
sensorless interface is disabled. If sensor 1 remains faulty, stop and
collect its error/readbacks rather than changing motor-model parameters.

## Manual bench measurement

Output 1 is **X4 pin 5**, with GNDD on **X4 pin 8**. Output level is nominal
24 V/+UB_Logic. Use a compatible scope or counter input.

Use the existing N6 drive panel or these PV suffixes, with the actual slave
PV prefix. They are direct drive controls, not motor-record commands:

| Step | PV suffix | Value |
| --- | --- | --- |
| Ensure zero demand | `Drv01-Spd` | `0` |
| Reset fault and enable via the existing DS402 sequence | `Drv01-TrgDS402Ena.PROC` | `1` |
| Apply a low bench velocity | `Drv01-Spd` | `163840` native increments/s = 18 degrees/s |
| Stop | `Drv01-Spd` | `0` |
| Disable drive | `Drv01-TrgDS402Dis.PROC` | `1` |

These values assume the configured 200-step motor and native velocity units.
Do not download velocity by SDO: the existing target-velocity PDO would
continually overwrite it. Check the actual drive status after enabling.

The existing `BO01-Arr` record controls the whole output word: `65536` arms
output 1 and `0` disarms it. `PINI=0` avoids initialization overwriting the
startup gate. The brake-control bit and other output bits remain zero.

Observe output 1 during slow monotonic motion. The target pulse spacing is
100 full steps = 180 degrees, or ten seconds at the listed bench velocity.
Expect two pulses per revolution over repeated revolutions; verify pulse
width, phase, reversal and stop/restart behavior separately. The routing
limit is 500 Hz. No absolute compare point or pulse width is programmed.

## Return to normal axis operation

Stop and disable the drive, then restart with the original `startup.cmd`.
For a full restoration of the output routing and interface settings, load
`cfg/disable_pulse_source.cmd` after the motor component and before applying
EtherCAT configuration. The normal component restores native position units.
No script saves settings to drive flash.
