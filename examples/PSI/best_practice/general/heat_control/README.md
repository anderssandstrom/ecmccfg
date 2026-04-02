# Heat Control With Motion Axis

This example shows how an ecmc motion axis can be reused as a simple temperature
controller:

- `EL2535-0002` provides the PWM heater output
- `ELM3504_F32_Scalar` provides the temperature feedback
- the axis controller closes the loop between temperature setpoint and heater output

## Files

- `startup.cmd`: startup example for the EL2535 + ELM3504 setup
- `cfg/axis.yaml`: YAML axis configuration for the heat-control loop

## Overview

The heater is configured as the axis drive output and the measured temperature is
configured as the axis encoder input. This allows the normal ecmc controller and
trajectory handling to be used for thermal control.

The example uses:

- PWM output from `EL2535-0002`
- `F32` scalar analog input from `ELM3504`
- absolute encoder mode with `F32` input (`bits: 32`, `absBits: 32`)
- PT1000 4-wire sensor setup with Celsius scaling
- controller output limited to `0..100` so the heater command cannot go negative

## Startup

Run from this directory:

```sh
iocsh.bash startup.cmd
```
