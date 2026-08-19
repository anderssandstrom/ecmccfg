+++
title = "Nanotec N6 EtherCAT drive"
weight = 25
chapter = false
+++

## Scope and status

This page describes the ecmccfg and ecmccomp support for the Nanotec
`N6-1-1-1-S` EtherCAT drive with FIR-v2508 firmware. The supplied ESI is
`PLC_N6-1-1-1-S_2508-B1072143_N6-1-1-1-S.xml`.

Relevant files are:

- `hardware/Nanotec/ecmcN6-1-1-1-S.cmd`
- `db/Nanotec/ecmcN6-1-1-1-S.substitutions`
- `qt/ecmcN6-1-1-1-S.ui`
- `qt/ecmcN6-1-1-1-S_expert.ui`
- ecmccomp component type `N6`, implemented by `N6_2PH_STEPPER.cmd`

{{% notice warning %}}
The N6 hardware configuration and panels are currently marked **untested**.
Commission with conservative current settings and verify every safety-related
input and drive reaction on the actual machine.
{{% /notice %}}

## Motor configuration

The ecmccomp configuration supports a generic two-phase open-loop stepper.
The main component macros are:

| Macro | Meaning | Default or limit |
|-------|---------|------------------|
| `I_MAX_MA` | Rated/run phase current in mA | Required, drive limit 6000 mA |
| `I_STDBY_MA` | Standstill phase current in mA | Required |
| `STEPS` | Full steps per mechanical revolution | Motor value, normally 200 |
| `INV_DIR` | Invert position and velocity direction | `0` |
| `I2T_MAX_MS` | Maximum-current duration | `100` ms |
| `CURR_RED_DLY_MS` | Delay before standstill-current reduction | `1000` ms |
| `N6_POS_UNIT` | CiA-402 object `0x60A8` | `0x00B50000` |
| `N6_VEL_UNIT` | CiA-402 object `0x60A9` | `0x00B50300` |
| `N6_IO_24V` | Select 24 V inputs and +UB outputs | `1` |
| `N6_INPUT_PULLUP` | Select input pull-up instead of pull-down | `0` |

`U_NOM_MV`, `R_COIL_MOHM`, and `L_COIL_UH` are accepted for compatibility
with generic motor definitions. They are validated where applicable but are
not written to the N6 for open-loop stepper operation. The resistance and
inductance fields at `0x3380` belong to sensorless feedback and are not the
ordinary open-loop stepper winding parameters.

For example:

```text
I_MAX_MA=200,I_STDBY_MA=100,STEPS=200,INV_DIR=0
```

produces the following current settings:

| Object | Value | Result |
|--------|------:|--------|
| `0x6075` | `200` | Rated/run current 200 mA |
| `0x6073` | `1000` | 1000 per mille, maximum current 200 mA |
| `0x3219:02` | `1000` | Wait 1000 ms at zero setpoint |
| `0x3219:03` | `500` | 500 per mille, standby current 100 mA |

Standby reduction is automatic in open-loop mode when the commanded velocity
in `0x60FF` remains zero for the time in `0x3219:02`. No additional enable bit
is required.

{{% notice warning %}}
The N6 does not provide motor overload or motor overtemperature protection in
this open-loop setup. Nanotec also notes that sinusoidal commutation can cause
a winding current up to sqrt(2) times the configured value for a period of
time. Confirm whether the motor data-sheet current is the applicable bipolar
phase-current rating and perform a temperature endurance test.
{{% /notice %}}

## Position and velocity scaling

The default unit objects select the native, highest-resolution units:

```text
0x60A8 = 0x00B50000  # encoder increments
0x60A9 = 0x00B50300  # encoder increments per second
```

For an open-loop two-phase stepper, ecmccomp sets:

```text
pole pairs = STEPS / 4
increments per revolution = pole pairs * 65536
                          = STEPS * 16384
```

For a 200-step motor:

```text
pole pairs                = 50
increments per revolution = 3276800
degrees per increment      = 360 / 3276800
                           = 45 / 409600
```

Use the same numerical scaling magnitude for encoder position and drive
velocity:

```text
position: increments        * 45/409600 = degrees
velocity: increments/second * 45/409600 = degrees/second
```

The time dimension remains unchanged, which is why position and velocity use
the same conversion factor. Their resulting engineering units are different.
Direction may additionally be inverted with `INV_DIR` or at axis level.

## Cyclic PDO mapping

The N6 supports configurable PDO mappings, but `0x1C13` has only four TxPDO
assignment slots. Do not assign `0x1A04` or later as a fifth TxPDO: writing
`0x1C13:05` aborts with `0x06090011`, followed by `Invalid input
configuration`.

The additional input entries are therefore packed into `0x1A03`:

| Direction | PDO | Object | ecmc entry |
|-----------|-----|--------|------------|
| Output | `0x1600` | `0x6040:00` | `driveControl01` |
| Output | `0x1600` | `0x6060:00` | `modeControl01` |
| Output | `0x1602` | `0x60FF:00` | `velocitySetpoint01` |
| Output | `0x1603` | `0x60FE:01` | `binaryOutputArray01` |
| Input | `0x1A00` | `0x6041:00` | `driveStatus01` |
| Input | `0x1A00` | `0x6061:00` | `modeActual01` |
| Input | `0x1A01` | `0x6064:00` | `positionActual01` |
| Input | `0x1A02` | `0x606C:00` | `velocityActual01` |
| Input | `0x1A03` | `0x60FD:00` | `binaryInputArray01` |
| Input | `0x1A03` | `0x60E4:03` | `positionActualInc01` |
| Input | `0x1A03` | `0x60E4:04` | `positionActualSSI01` |
| Input | `0x1A03` | `0x603F:00` | `errorCode01` |
| Input | `0x1A03` | `0x6077:00` | `torqueActual01` |

The incremental and SSI velocity objects `0x60E5:03/04` are intentionally not
mapped. Objects `0x33A0` and `0x33B0` configure the incremental and SSI
interfaces; they are not the cyclic position values. The attached encoder's
resolution and protocol still require device-specific SDO configuration.

## Exposed EPICS process variables

The dedicated N6 panels use the following main PVs:

| PV suffix | Content |
|-----------|---------|
| `Drv01-VelAct` | Main actual velocity |
| `Drv01-TrqAct` | Actual torque, scaled by 0.1 percent |
| `Drv01-Stat` | CiA-402 statusword |
| `Drv01-ErrCode` | CiA-402 error code from `0x603F` |
| `Enc01-PosAct` | Main motor position from `0x6064` |
| `Inc01-PosAct` | Incremental-interface position |
| `SSI01-PosAct` | SSI-interface position |
| `BI01-Arr` | Complete 32-bit `0x60FD` input word |
| `BO01-Arr` | Complete 32-bit `0x60FE:01` output word |
| `BO01-Arr-RB` | Output-word readback |

N6-specific database templates use a `0xFFFFFFFF` asyn mask. The generic
binary-array templates use only `0xFFFF` and must not be substituted here,
because the N6 physical I/O bits are above bit 15.

## Digital inputs and ecmc limit handling

The configuration explicitly writes `0x323A:01=1` and `0x323A:02=0`. The
inputs therefore use 24 V thresholds with pull-down wiring. The voltage-level
selector is shared with the outputs, so outputs 1 through 3 use `+UB` rather
than 5 V. Override these values with `N6_IO_24V` and `N6_INPUT_PULLUP` only
when the connected electrical interface requires it.

`BI01-Arr` exposes two kinds of signals:

| Bit | Meaning |
|----:|---------|
| 0 | N6 internal negative-limit function |
| 1 | N6 internal positive-limit function |
| 2 | N6 internal home function |
| 3 | N6 internal interlock function |
| 16 | Physical input 1 |
| 17 | Physical input 2 |
| 18 | Physical input 3 |
| 19 | Physical input 4 |
| 20 | Physical input 5 |
| 21--23 | Other/reserved routed sources in this variant |
| 24 | Physical input 6 |

For normal ecmc handling, use physical bits 16 through 20 and 24. For example,
ecmc can use bit 16 as the negative axis limit and bit 17 as the positive axis
limit.

Object `0x3242` controls the N6 internal input routing. Its factory values for
subindices 1 through 4 are zero, meaning that the internal NLS, PLS, home and
interlock bits are sourced from constant zero. This leaves the physical inputs
available as ordinary inputs and lets ecmc implement the reaction.

{{% notice warning %}}
`0x3242` is savable. A drive previously configured by another application may
not have its factory routing. To guarantee ecmc-only handling, verify or write
`0x3242:01`, `:02`, `:03`, and `:04` to zero. Merely exposing `BI01-Arr` does
not connect its physical bits to the ecmc axis limits; configure the axis
interlocks explicitly.
{{% /notice %}}

If internal drive handling is deliberately enabled, `0x3701` selects the
reaction. The factory value `-1` only records the limit position. Values `1`
and `5` use the normal deceleration ramp; values `2` and `6` use the quick-stop
ramp. This internal behavior is separate from ecmc limit handling.

## Digital outputs

`BO01-Arr` maps the complete `0x60FE:01` word:

| Bit | Meaning |
|----:|---------|
| 0 | Brake output control |
| 16 | Physical output 1 |
| 17 | Physical output 2 |
| 18 | Physical output 3 |

Output routing is configured in `0x3252`. The factory mapping routes outputs
1 through 3 to `0x60FE:01` bits 16 through 18. As with input routing, verify
saved settings on a drive that may have been configured previously.

## Useful commissioning checks

Adjust master and slave position as required:

```bash
ethercat upload -m1 -p0 --type uint32 0x3202 0
ethercat upload -m1 -p0 --type int32  0x60FF 0
ethercat upload -m1 -p0 --type uint32 0x6075 0
ethercat upload -m1 -p0 --type uint16 0x6073 0
ethercat upload -m1 -p0 --type uint16 0x3219 2
ethercat upload -m1 -p0 --type uint16 0x3219 3
ethercat upload -m1 -p0 --type int16  0x3701 0
```

Expected for open-loop standstill are `0x3202=0` and `0x60FF=0`.

## Related pages

- [Hardware knowledge base]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
- [Motion scaling]({{< relref "/manual/motion_cfg/scaling.md" >}})
- [ecmccomp]({{< relref "/manual/motion_cfg/ecmccomp.md" >}})
