# N6 drive-side pulse generator trial

Run `startup_pulse_per_fullstep.cmd` from this directory instead of
`startup.cmd`. It loads `cfg/pulse_per_fullstep.cmd` after the motor component
and before EtherCAT configuration is applied. The original `positionActual01`
PDO, `6064` units, axis YAML and hardware descriptor are unchanged. No extra
PDOs or `_OPT` descriptor are needed.

**This is an untested commissioning example targeting one pulse per full
step.** The pulse-generator source resolution and behavior in open-loop mode
must be measured before treating the ratio as verified.

## Configuration

The [N6 EtherCAT manual V1.1.0 / FIR-v2508](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.1.0.pdf),
section 7.1.3 and object `205C`, describe the pulse generator and its ratio.
The script queues SDO settings for startup and reconnection:

| Object | Final value | Purpose |
| --- | --- | --- |
| `205C:01` | `0` | No free-running increments if no source is selected |
| `3203:01` | `8` | Select internal/sensorless interface for pulse generator |
| `3203:02..04` | `0` | Clear other feedback selections for this open-loop example |
| `205C:02` | `1` | Clock/direction on generator channels A/B |
| `205C:03` | `1` | Numerator |
| `205C:04` | `16384` | Denominator |
| `3252:02` | `0x2010` | Pulse generator on output 1; gate bit 16 |
| `3252:03` | `0x2011` | Pulse generator on output 2; gate bit 17 |

The existing `60FE:01` output PDO holds `196608` (`0x00030000`) to enable
both channels. Only the enable word is cyclic; the drive generates the pulses.
Writing the existing `BO01-Arr` PV to `0` disarms both channels; writing
`196608` rearms them. These values replace the entire output word, including
the brake-control bit. The example loads records with `PINI=0` to avoid an
initialization write to that gate.

The source masks deliberately keep position/velocity selection bits 0 and 1
clear, matching the original synthesized open-loop feedback setup. Do not
apply this snippet to an axis using external or closed-loop feedback.
It does not change encoder resolution or enable sensorless closed-loop mode.
Whether the internal interface feeds usable open-loop position to this pulse
generator remains an experimental question.

The generic routing example mentions `3250:08`, but the FIR-v2508 N6 object
dictionary lists only `3250:01`. The script omits the undocumented write;
verify routing support on the installed firmware if no signal appears.

## Wiring and measurement

The candidate channel assignment is output 1 = clock and output 2 = direction.
Check it on the installed firmware:

| Connection | X4 pin |
| --- | --- |
| Output 1 | 5 |
| Output 2 | 6 |
| Digital ground, GNDD | 8 |

The original N6 setup selects +UB_Logic outputs (nominally 24 V). Check that
the oscilloscope/counter input accepts this voltage.

After startup, inspect the settings using read-only uploads (adjust master
and slave position if necessary):

```sh
ethercat upload -m1 -p0 --type string 0x100A 0
ethercat upload -m1 -p0 --type uint32 0x60A8 0
ethercat upload -m1 -p0 --type uint8  0x3203 1
ethercat upload -m1 -p0 --type uint16 0x3205 4
ethercat upload -m1 -p0 --type int16  0x205C 1
ethercat upload -m1 -p0 --type int16  0x205C 2
ethercat upload -m1 -p0 --type int16  0x205C 3
ethercat upload -m1 -p0 --type int16  0x205C 4
ethercat upload -m1 -p0 --type uint16 0x3252 2
ethercat upload -m1 -p0 --type uint16 0x3252 3
```

`60A8` must still read `0x00B50000`. Inspect `3205:04` (selected pulse-generator
sensor); an unselected source is not a valid position-based test.

Start at low speed, for example 18 degrees/second (10 full steps/second for
the configured 200-step motor). Verify no continuous pulses at standstill.
Count clock rising edges over a slow 360-degree move, then repeat in reverse.
The target is **200 pulses per revolution**, with direction changing on the
other channel. Also check pulse width and behavior across stop/restart and
reversal. The maximum timing/frequency specifications alone do not establish
trigger phase or accuracy.

If the count is different, record the count, direction, firmware version and
SDO readbacks. That measurement establishes the actual source scaling and
any channel-mode counting factor; do not silently compensate by changing the
axis scaling. If there are no pulses, first check the gate PV, source selection,
channel assignment and routing. Do not enable closed-loop operation merely
to make the source produce a signal.

## Original 100-full-step target

The simple `3252` divider offers powers of two up to 64. `205C` uses signed
16-bit ratio fields. If its source has 16,384 increments per full step, the
one-full-step trial fits; the original 100-full-step denominator of 1,638,400
does not. The source-resolution assumption must be verified by this trial.
No NanoJ program is used.
