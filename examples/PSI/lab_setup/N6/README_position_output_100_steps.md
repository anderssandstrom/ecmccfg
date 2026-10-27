# Dedicated output trial: one pulse per 100 full steps

Use `startup_position_output_100_steps.cmd` instead of the original startup
or the failed `startup_pulse_per_fullstep.cmd`. Run from this directory.
Rebuild/install ecmccfg with the new `N6-1-1-1-S_POS_OUT` hardware descriptor
before loading this startup.

This trial is **not verified on hardware**. It uses direct position-divider
routing, independently of the rejected `205C` pulse-generator source.

## Dedicated files

| File | Purpose |
| --- | --- |
| `startup_position_output_100_steps.cmd` | Load this trial |
| `cfg/position_output_100_steps.cmd` | SDO units, raw resolution and output routing |
| `cfg/axis_position_output.yaml` | Axis control using native `6063` feedback |
| `hardware/Nanotec/ecmcN6-1-1-1-S_POS_OUT.cmd` | Standard N6 PDOs plus `positionActualRaw01` |

The original `startup.cmd`, `cfg/axis.yaml`, and base hardware descriptor are
unchanged. Do not combine this startup with the old pulse-generator trial;
restart the IOC so the failed SDO queue is discarded.

## Settings and expected behavior

The [N6 manual for FIR-v2542](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.2.1.pdf?1773317058=)
describes step units in section 5.3, direct output routing in section 7.1.2,
and raw position in object `6063`.

| Setting | Value | Meaning |
| --- | --- | --- |
| `60A8:00` | `0x02AC0000` | `6064` unit is 100 full motor steps |
| `3252:02` | `0x0910` | Output 1 follows `6064` count changes, divider 1, gate bit 16 |
| `60EB:01` | `1` | Internal-interface resolution denominator |
| `60E6:01` | `3276800` | Native counts/revolution for this 200-full-step motor |
| Existing `60FE:01` PDO | `65536` | Enable output 1; all other output bits zero |

There are **no writes to `3203` or `205C`**. This assumes the original
open-loop selection masks remain zero; the failed value `8` must not be
present. Velocity units remain native increments/second. `INV_DIR=0` avoids
sign differences between velocity demand and raw feedback in this trial.

The additional `6063:00` entry is appended to existing TxPDO `1A03`; the N6
still has four TxPDO assignments. Axis feedback uses this raw entry and its
original `360/3276800` degree scaling. Existing `positionActual01` and the
normal N6 encoder panel instead show the scaled `6064` value: two counts
per revolution for a 200-full-step motor. Additional `60E4` positions also
use the changed position units. `6063` does not reset on drive homing; use
the ecmc axis referencing in the dedicated YAML.

The manual warns that raw `6063` values are invalid when encoder resolution
is zero. The SDO snippet therefore configures interface 1's nominal native
resolution without selecting it for the rejected pulse generator. Its
open-loop raw feedback must still be verified. If feedback is absent,
unstable or incorrectly scaled, stop the test; do not increase gains or
alter the axis scaling to compensate.

## Commissioning

Output 1 is X4 pin 5; GNDD is pin 8. The base N6 configuration selects
nominal 24 V/+UB_Logic outputs; use a compatible scope or counter input.

After EtherCAT configuration succeeds, check these readbacks:

```sh
ethercat upload -m1 -p0 --type uint32 0x60A8 0
ethercat upload -m1 -p0 --type uint16 0x3252 2
ethercat upload -m1 -p0 --type uint32 0x60E6 1
ethercat upload -m1 -p0 --type uint32 0x3202 0
ethercat upload -m1 -p0 --type uint8  0x3203 1
ethercat upload -m1 -p0 --type int32  0x6063 0
ethercat upload -m1 -p0 --type int32  0x6064 0
```

Expected settings are those in the table, `3202=0`, and `3203:01=0`.
Keep the motor stationary for the initial readbacks. Check the gate through
the existing `BO01-Arr` record: `65536` enables output 1, `0` disables it.
The example sets `PINI=0` to avoid a record initialization write to the gate.
It owns the whole output word, including a zero brake-control bit.

The dedicated axis limits velocity/jog to 18 degrees/second and uses a
10-degree tweak. Begin with a small move and confirm that raw position and
the axis readback follow it correctly. A 10-degree movement corresponds to
about 91,022 raw counts. The axis lag monitor is enabled with a 5-degree
tolerance; stop immediately if feedback does not follow the move.

Once feedback is verified, observe output 1 during slow monotonic motion.
The target rising-edge spacing is **100 full steps = 180 degrees = 1,638,400
raw counts**. Over repeated revolutions, expect two pulses per revolution.
Measure the width and starting phase; they are not specified by these SDO
settings. Check reverse motion and stop/restart behavior separately.

The routing limit is 500 Hz. This test runs at about 0.1 pulse/second at its
18-degree/second velocity. It is a periodic position-divider output; it has
no programmed absolute compare point, scan window or pulse width.

## Return to normal operation

Restart using the original `startup.cmd`. To undo the internal-interface
resolution and routing from the trials, load `cfg/disable_pulse_source.cmd`
after the motor component and before applying EtherCAT configuration, as
described in `README.md`. The normal component restores native position
units. No script writes a save-to-flash command.
