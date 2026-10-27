# N6 drive-side pulse generator trial

For the separate **scaled-position output trial**, use
[startup_position_output_100_steps.cmd](startup_position_output_100_steps.cmd)
and [its dedicated instructions](README_position_output_100_steps.md).
The files below describe the earlier `205C` pulse-generator approach.

## Current status: source selection rejected after all three trials

The final, order-corrected script also failed with abort `0x06040047` at
`3203:01`. That script writes this subindex exactly once, with value `8`,
after the interface-resolution settings. Thus neither configuring the
disabled interface nor removing the early zero write resolved the failure.
The proposed internal pulse source is incompatible with the tested
configuration. This does not establish that every pulse-generator source
or every N6 firmware has the same limitation.

**Stop this trial.** It is retained as a reproducer for Nanotec, not a working
one-pulse-per-full-step configuration. Use the recovery procedure below to
return to the original open-loop setup. Further SDO guesses are not justified
by the evidence collected so far.

## Test evidence

The drive rejected the trial's `3203:01=8` write with SDO abort `0x06040047`
(general internal incompatibility). EtherCAT SDO configuration consequently
failed. Subsequent readbacks were:

| Object | Reported value |
| --- | --- |
| `100A:00` | `FIR-v2542-B1080909` |
| `60E6:01` | `0` (internal/sensorless interface disabled) |
| `60EB:01` | `1` |
| `3202:00` | `0` (open-loop stepper) |

The revision configures `60EB:01=1` and `60E6:01=3276800` **before**
selecting `3203:01=8`. The user reported the same `0x3203:01` abort after
retrying this revision. Enabling the interface therefore did not produce a
working configuration; a disabled interface alone is not an established
explanation for the failure. No further selection-bit combinations are
proposed without firmware-specific evidence.

The EtherCAT error does not print the downloaded value. The previous revision
wrote `3203:01` twice (first `0`, later `8`), so this log alone cannot identify
which write was rejected or prove that the resolution writes were reached.
Read back `60E6:01` and `3203:01` after the failure to narrow that down.
Even a nonzero resolution would not prove support for the proposed source.

The final revision removed the redundant `3203:01=0` write that preceded
interface setup. It now configures the interface first and writes `3203:01`
exactly once, with value `8`. This corrects the setup order without trying
another source mask. The reported abort at kernel time `19145.605130`
confirms that this final revision also failed at source selection.

Do not simply skip the failed write and continue the trial: `205C` requires a valid
position source. The candidate explicitly sets `205C:01=0` so an absent
source cannot fall back to continuous free-running pulses.

To investigate the failed startup without changing settings, collect:

```sh
ethercat upload -m1 -p0 --type string 0x100A 0
ethercat upload -m1 -p0 --type uint32 0x60E6 1
ethercat upload -m1 -p0 --type uint32 0x60EB 1
ethercat upload -m1 -p0 --type uint32 0x3202 0
ethercat upload -m1 -p0 --type uint8 0x3203 1
ethercat upload -m1 -p0 --type uint16 0x3205 4
```

The attempted final configuration values were `60E6:01=3276800`,
`60EB:01=1`, `3202:00=0`, `3203:01=8`. They must not be assumed to have been
applied after an aborted startup. The corrected order still failed. Do not
switch to closed-loop or invent motor-model parameters to make the source work.

The question for Nanotec is: on N6-1-1-1-S with FIR-v2542-B1080909 and
`3202=0`, can the `205C` pulse generator use synthesized open-loop motor
position while `6064` remains in native units? Is `3203:01` bit 3 supported,
and what prerequisites apply? Include all three attempts (initial selection,
interface-enable revision, and order-corrected revision) with the abort and
fresh readbacks. Firmware-specific source restrictions or an alternative
documented SDO path are needed before trying another configuration.

The [FIR-v2542 manual, object 60E6](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.2.1.pdf?1773317058=)
documents that zero disables an interface and that nonzero enables sensor
checks. Enabling interface 1 does not establish that its position is the same
as the synthesized open-loop position. Verify normal `positionActual01`
behavior and 3,276,800 counts per revolution before using the output.

## Restore the original setup

Restart the IOC using `startup.cmd` rather than the pulse trial, and load
the following **before** applying the EtherCAT configuration:

```text
${SCRIPTEXEC} ./cfg/disable_pulse_source.cmd "N6_SID=${DRV_SID}"
```

This disarms the outputs, clears source selections, restores `60E6:01=0`,
and returns outputs 1/2 to ordinary digital-output routing. Restarting with
`startup.cmd` alone does not explicitly restore the interface resolution.
Neither script saves settings to drive flash.

## Candidate retained for investigation

`startup_pulse_per_fullstep.cmd` loads `cfg/pulse_per_fullstep.cmd` after the motor component
and before EtherCAT configuration is applied. The original `positionActual01`
PDO, `6064` units, axis YAML and hardware descriptor are unchanged. No extra
PDOs or `_OPT` descriptor are needed.

The intended target is one pulse per full step. Source selection must first
be resolved; source resolution and behavior in open-loop mode then need
measurement before treating the ratio as verified. The measurement procedure
below applies only after a supported source selection has been established.

## Configuration

The [N6 EtherCAT manual V1.1.0 / FIR-v2508](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.1.0.pdf),
section 7.1.3 and object `205C`, describe the pulse generator and its ratio.
The script queues SDO settings for startup and reconnection:

| Object | Final value | Purpose |
| --- | --- | --- |
| `205C:01` | `0` | No free-running increments if no source is selected |
| `60EB:01` | `1` | Internal-interface resolution denominator, revolutions |
| `60E6:01` | `3276800` | Enable internal interface with nominal native counts/revolution |
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
It configures the internal-interface resolution for this 200-step motor,
retains native position/velocity units, and does not enable closed-loop mode.
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
