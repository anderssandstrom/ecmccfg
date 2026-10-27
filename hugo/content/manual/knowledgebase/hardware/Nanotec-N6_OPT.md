+++
title = "Nanotec N6 optional PDOs and position output"
weight = 26
chapter = false
+++

`N6-1-1-1-S_OPT` adds optional raw position and individual output-enable
records to the standard N6 CSV mapping. The original `N6-1-1-1-S` descriptor
is unchanged. Motor components still identify the drive as type `N6`.

## Configuration

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PositionOutput,MACROS='FULL_STEPS=100,OUTPUT=1,ARM=1'"
```

Build/install both ecmccfg and ecmccomp with these additions. Load the output
component after the motor and before applying EtherCAT configuration. It is
not a live scan parameter. The dedicated lab example is
`examples/PSI/lab_setup/N6/startup_position_output_100_steps.cmd`.

## Hardware option

| Option | Default | Effect |
| --- | --- | --- |
| `RAW_POS` | `0` | With `1`, map `6063:00` as `positionActual01` and rename `6064` to `positionActualScaled01` |

With `RAW_POS=0`, the process image matches the original descriptor. The
optional S32 entry is appended to existing TxPDO `1A03` (20 bytes total with
raw position), retaining the four TxPDO assignment slots. With `RAW_POS=1`, the existing
`6064` entry is named `positionActualScaled01` so the fine counter can use
the conventional feedback name `positionActual01`. Neither position
units nor output routing are changed by this option.

The companion `Drive-Generic-PositionOutput` ecmccomp component requires raw
position mapped, a motor applied first and motor `INV_DIR=0`. Its choices are:

| Macro | Default | Meaning |
| --- | --- | --- |
| `FULL_STEPS` | `100` | Full motor steps per output pulse |
| `OUTPUT` | `1` | Physical output 1, 2 or 3 |
| `ARM` | `0` | Startup output-enable bit, 0 or 1 |
| `N6_IO_24V` | `0` for first output | `0` = 5 V output, `1` = nominal 24 V/+UB_Logic |
| `N6_INPUT_PULLUP` | Inherit motor (default `0`) | `0` = pull-down, `1` = pull-up |

Supported intervals are `10^n * d`, with `n=0..6` and
`d` in `1,2,4,8,16,32,64`. Other intervals are rejected. All configured outputs
on one slave must use the same canonical unit exponent because `60A8` is
shared. For example, 100 and 200 steps share unit 100 with dividers 1 and 2;
100 and 10 steps conflict and are rejected. The motor cannot be reapplied
after an output component has set those units in the same startup.

## Two positions and output gates

For the 200-full-step example, use `positionActual01` for the axis and
`360/3276800` scaling for both encoder position and native CSV velocity.
`positionActualScaled01` maps `6064`; its values become coarse when
the component changes `60A8` to 100 full steps/count. Do not use that coarse
entry with the original native encoder scaling. The raw counter represents
generated open-loop motion, not measured rotor position or lost-step detection.

| PV suffix | Meaning |
| --- | --- |
| `Enc01-PosAct` | Fine `6063` open-loop counter with `RAW_POS=1`; otherwise legacy `6064` position |
| `Enc01-PosScaled` | Scaled `6064` position; present only with `RAW_POS=1` |
| `PosOut01-Ena`, `PosOut02-Ena`, `PosOut03-Ena` | Individual gate controls |
| Corresponding `-RB` suffixes | Gate readbacks |
| `CfgRawPosition` | Read-only resolved hardware option for the panel |
| `BO01-Arr` | Existing complete output word, including brake bit 0 |

The hardware snippet loads the six gate control/readback records directly,
including when default substitutions are disabled.

The component uses bit-addressed `WriteEcEntryEcPath` calls and the gate PVs
use asyn masks. Both preserve unrelated outputs and brake control. Output
records use `PINI=0`/`NO` so initialization does not clear an explicitly armed
gate. Whole-word writes to `BO01-Arr` intentionally still replace every bit.

## Panels

The hardware selects `ecmcN6-1-1-1-S_OPT.ui` and its expert display. They show
position actual, optional scaled position and all three masked gate controls.
Raw fields are shown only when `CfgRawPosition=1`. The original compact and
expert panels remain available for the unchanged legacy descriptor.

## Commissioned scope

The user demonstrated simultaneous fine `6063` axis feedback and a working
100-full-step output on N6-1-1-1-S, FIR-v2542-B1080909, with `60E6:01=0`.
The packaged optional choices and gate-bit operations have hardware-free
checks; other intervals, outputs and firmware still need commissioning.

The manual's generic warning about raw `6063` with zero interface resolution
must not be generalized away: the observed open-loop counter behavior is
firmware-specific evidence. Enabling the uncommissioned sensorless interface
with a nominal resolution caused sensor fault `7305`; this feature deliberately
keeps it disabled and makes no writes to `3203` or `205C`.

Output 1 is X4 pin 5 with GNDD on pin 8. The position-output component defaults to
5 V outputs. Select `N6_IO_24V=1` for nominal 24 V/+UB_Logic outputs.
This shared selector also changes digital input thresholds; it does not
configure the motor power supply. Later output components inherit the first
output's voltage and reject conflicting electrical settings. Direct position routing is limited to 500 Hz;
pulse width, phase, reversal and counter rollover remain commissioning checks.

See also [the base N6 configuration]({{< relref "Nanotec-N6.md" >}}).
