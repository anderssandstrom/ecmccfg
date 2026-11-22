# Axis hardware defaults and Jinja command snippets (draft)

Axis YAML selects a slave and, for multichannel terminals, a channel. The IOC
registers the hardware type during `addSlave.cmd` as
`ECMC_HW_M<master>_S<slave>` using `ECMC_EC_COMP_TYPE` if set by
the selected slave hardware script, otherwise `HW_DESC`. `addSlave.cmd` clears
`ECMC_EC_COMP_TYPE` before running each slave script to prevent carrying over
a value from the previously configured slave.

## Axis example: EL7062

```yaml
drive:
  slave: $(DRV_SLAVE)
  channel: $(DRV_CHANNEL=1)
  numerator: 10.0

encoder:
  slave: $(DRV_SLAVE)
  channel: $(DRV_CHANNEL=1)
  feedback: $(ENC_FEEDBACK=openloop)
  numerator: 1.0
```

For EL7062 the `input` section can inherit the drive slave and channel.
The hardware profile supplies `binaryInputs01.1` (forward) and
`binaryInputs01.0` (backward), or the corresponding `02` entries.
To exchange these two default links without repeating their paths:

```yaml
input:
  limit:
    swap: true
```

Use `swap: $(SWAP_LIMITS=false)` to select this at startup. Explicit
`input.limit.forward` and `input.limit.backward` paths take precedence
over the swapped defaults, independently. `input.slave` and `input.channel`
may be specified to use a different input terminal with a suitable profile.
The swap changes signal assignment, **not electrical polarity**. Verify
the wiring, active levels, and limit handling before enabling motion.
EL7041 has no verified default limit mapping here, so continue to supply
explicit limit input paths for that terminal.

The EL7041 example needs only `slave`, with channel 1 implicit. EL7062
supports channels 1 and 2, and encoder feedback `openloop` (default) or
`incremental`. Incremental feedback selects `positionActual01_2` for
channel 1 or `positionActual02_2` for channel 2. This does not configure
the drive's internal control loop.

Master, slave and channel selectors accept IOC environment macros such as
`$(DRV_SLAVE)`, including `$(NAME=default)`, where present in the IOC
process environment. Unregistered hardware, unsupported channels/feedback,
or missing profiles produce configuration errors.

## Implementation

The **normal Jinja axis renderer** identifies hardware using the registered
slave, loads `hardwareProfiles/<model>/<section>.yaml` and applies defaults
in memory before the usual schema validation. No extra Python process or
intermediate hardware-resolved YAML is needed on this path. For variants
such as EL7041-0052, the base EL7041 profile is used if an exact profile is
not available.

Hardware profile strings expand `$(MASTER)`, `$(SLAVE)` and `$(CHANNEL)`;
the channel placeholder becomes a two-digit suffix `01` or `02`.

Optional `hardwareProfiles/<model>/drive.jinja2` and `encoder.jinja2`
files generate additional `ecmcConfigOrDie` commands. The renderer
includes these **after `Cfg.CreateAxis()` and before the normal encoder
and drive configuration**. The EL7041 and EL7062 snippets emit default scale denominators and PDO links.
Normal axis templates then apply the resolved YAML configuration, including
explicit overrides. ECMC permits configuration-time relinking: later commands
replace earlier links to the same axis slot.

Values explicitly specified in the axis YAML always override hardware
defaults. Hardware snippets set defaults first; the regular templates run
afterwards, so PDO links may be configured twice (last successful link wins).
The hardware-defined drive type is available before `Cfg.CreateAxis()`.

The ECB backend still uses the compatibility adapter
`resolveAxisHardwareProfiles.py` for slave-selected profiles. Unchanged
legacy ECB YAML continues through its original path. The ECB compatibility
adapter is **not** part of the Jinja rendering path.

## Notes

- EL7062 example denominators (drive 2147483648, encoder 1048576) follow the
  existing EL7062 open-loop IOC example and must be checked for the motor.
- Example denominators and scaling must match the
  motor, encoder, microstepping and engineering units.
- The EL7062 incremental encoder PDO suffix `_2` indicates the encoder
  feedback source, not the second motor channel.
- Hardware profiles with no command snippet work normally via the
  regular configuration templates.
- This feature requires IOC integration and hardware testing before release.

## Regression tests

```bash
python -m unittest discover -s scripts/jinja2/tests \
  -p 'test_resolve_axis_hardware_profiles.py'
```

Only `feature/hardware-abstraction` is modified; `v11.2.0_RC2` is unchanged.
