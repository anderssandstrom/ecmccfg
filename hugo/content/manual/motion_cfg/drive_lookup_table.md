+++
title = "Drive output lookup-table compensation"
weight = 36
chapter = false
+++

## Purpose

A CSV axis can add a position-dependent feed-forward value to its drive output.
This is useful for a voice coil working against a spring, gravity compensation,
or another repeatable load that needs a non-zero command to remain stationary.

The compensation is applied as:

```text
raw drive output =
  (controller output + scale * LUT(actual position)) / drive scale
  + raw drive offset
```

Both LUT columns use engineering units:

- column 1: actual axis position, in the encoder/axis position unit
- column 2: CSV drive-command offset, in the controller-output unit

The sum passes through the normal `drive.numerator` and `drive.denominator`
scaling. Do not store raw EtherCAT setpoint counts in the LUT.

This feature affects CSV velocity/force output only. It does not alter CSP
position output. Drive interlocks suppress the compensation.

## YAML configuration

```yaml
axis:
  mode: CSV

drive:
  numerator: 1
  denominator: 1000
  lookuptable:
    filename: ./cfg/voice_coil_spring.lut
    scale: 1.0
    enable: true
    # range: 360.0   # optional modulo range in position engineering units
```

Loading a valid table enables it by default. Set `enable: false` when the table
should be loaded but not active. `scale` defaults to `1.0`; use `-1.0` to invert
the compensation sign. If `range` is positive, the actual position is wrapped
into `0 <= position < range` before lookup.

## LUT file

```text
# position [mm]    holding output [engineering units]
-10.0              -0.80
  0.0               0.00
 10.0               0.85
```

Values between rows are interpolated by the standard ecmc lookup-table
implementation. Outside the table domain, the closest endpoint is used.

## Direct commands

```text
Cfg.LoadAxisDrvLookupTable(1,./cfg/voice_coil_spring.lut)
Cfg.SetAxisDrvLookupTableScale(1,1.0)
Cfg.SetAxisDrvLookupTableRange(1,0)
Cfg.SetAxisDrvLookupTableEnable(1,1)
```

The corresponding query commands are
`GetAxisDrvLookupTableEnable`, `GetAxisDrvLookupTableScale`, and
`GetAxisDrvLookupTableRange`.

Commission the LUT initially with conservative drive limits and verify its sign
over the full travel before relying on it for holding force.
