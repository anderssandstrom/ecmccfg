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

## Implementation — Jinja family profiles

`addSlave.cmd` registers two values per master/slave:

- `ECMC_HW_M<master>_S<slave>`: hardware component type
- `ECMC_HW_SCRIPT_M<master>_S<slave>`: exact `HW_DESC` script variant

The existing Python axis runner uses **Jinja2 only** to choose and merge
hardware defaults: `hwProfileResolve.jinja2` includes
`EL70xx`, `EL7062`, `EL72xx`, `EL5021`, `EL5042`, `EL5101`, or `EL5102` family templates.
These templates merge base PDO mappings with CSV/CSP variants and explicit
axis YAML overrides, producing the data for ordinary schema validation.
No hardware-specific Python resolver, additional Python invocation, or
hardware-resolved temporary YAML file remains.

**IOC installation:** `GNUmakefile` installs Jinja scripts into the flat
`/ioc/modules/ecmccfg/<version>/R<base>/` directory. For that reason the
runtime uses uniquely named top-level `hwProfileResolve.jinja2` and
`hwProfileEL*.jinja2` templates, not nested `hardwareProfiles/` paths.
Rebuild the local ECMCCFG module/image after changes. If `TemplateNotFound`
occurs, verify `hwProfileResolve.jinja2` is present beside
`axisYamlJinja2.py` in the installed module directory.


The rendering order is family base, selected PDO variant, then explicit axis
YAML values. Existing YAML without hardware slave selectors takes the
unmodified legacy path. The normal axis templates emit the final links once.
For EL7062, optional `input.limit.swap` exchanges the mapped limit inputs.

For drive profiles, `HW_DESC` must identify a standard CSV/CSP mapping
consistent with `axis.mode`. OPT, PosIF and CST mappings are not inferred:
configure those with explicit PDO paths. Servo scaling remains explicitly
motor-specific, and terminal-specific input PDO capabilities must be checked.
The legacy `ecb` backend still accepts fully specified axis YAML but does
**not** support the new compact hardware selectors; select the Jinja backend
to use this abstraction.

## Notes

- EL7062 example denominators (drive 2147483648, encoder 1048576) follow the
  existing EL7062 open-loop IOC example and must be checked for the motor.
- Example denominators and scaling must match the
  motor, encoder, microstepping and engineering units.
- The EL7062 incremental encoder PDO suffix `_2` indicates the encoder
  feedback source, not the second motor channel.
- This feature requires IOC integration and hardware testing before release.


## Additional profiles: EL5021, EL5042, EL5102, EL70xx and EL72xx

The following hardware profiles are now available:

| Model / component type | Sections | Default PDO mapping |
| --- | --- | --- |
| EL5021 | encoder (channel 1) | `positionActual01` (32-bit Sin/Cos 1 Vpp) |\n| EL5042 | encoder (channels 1/2) | `positionActual01/02` (64-bit BiSS-C) |
| EL5102 | encoder (channels 1/2) | `positionActual01/02` (32-bit incremental) |
| EL7031, EL7037, EL7041, EL7047 | drive + encoder | EX70XX standard CSV and open-loop `positionActual01` |
| EL7062 | drive + encoder + input | CSV, open-loop/incremental and channel-specific limit PDOs |
| EL7201_RES, EL7201_OCT, EL7211_RES, EL7211_OCT, EL7221_OCT | drive + encoder | EX72XX standard CSV and `positionActual01` |

For the EL7031, EL7037, EL7041 and EL7047 open-loop encoder, the
hardware-family default is `encoder.denominator: 12800` (16-bit counter),
unless explicitly overridden by axis YAML. This is a counter scale used by
the current test model, not a universal motor/mechanics calibration.
Drive scaling and other encoder engineering scaling remain the responsibility
of the axis YAML. For EL5042 the physical
BiSS-C encoder resolution (`absBits`) must also be specified explicitly.
No default limit wiring is assumed for EL70xx or EL72xx, so include explicit
`input.limit.forward` and `input.limit.backward` paths.

The Jinja family templates use the component type registered from
`ECMC_EC_COMP_TYPE` (falling back to `HW_DESC`). `addSlave.cmd` also
registers `ECMC_HW_SCRIPT_M<master>_S<slave>` to preserve the selected
hardware-script variant. This matters because several EL70xx/EL72xx
CSP and OPT scripts share the same component type as CSV versions.
The standard drive profiles support **CSV and matching CSP process images**. An incompatible mode,
PosIF or OPT hardware script is rejected for automatic drive mapping
rather than risking an invalid setpoint link. Such configurations can
still use the established explicit axis-YAML PDO mapping.

For EL5021, the terminal provides a 32-bit position PDO. The actual
Sin/Cos interpolation resolution, numerator and denominator remain
encoder-specific and must be set in the axis YAML.

Examples:

```yaml
encoder:
  slave: 11
  numerator: 360.0
  denominator: 65536  # example only: use actual interpolation scaling
```

```yaml
# Additional encoder on EL5042 channel 2
encoder:
  slave: 10
  channel: 2
  numerator: 360.0
  denominator: 16777216
  absBits: 24  # example only: use actual BiSS-C encoder resolution
```

```yaml
# EL7211 OCT standard CSV: motor-specific scaling intentionally explicit
axis:
  mode: CSV
drive:
  slave: 7
  numerator: 360.0
  denominator: 2147483648
encoder:
  slave: 7
  numerator: 360.0
  denominator: 1048576
input:
  limit:
    forward: ec0.s8.binaryInput01.0
    backward: ec0.s8.binaryInput01.1
```

The PDO names under `input.limit` in the latter example are **illustrative
external digital input paths** and must be replaced with the actual registered
EtherCAT entries. No generic EL72xx limit mapping is guaranteed.

## Simulation IOC integration coverage

A dedicated simulator configuration under
[`tests/integration/hardware_profiles/`](../tests/integration/hardware_profiles/README.md)
provides a 10-axis matrix: EL7031/7037/7041/7047, EL5021, EL5042,
EL5101/5102, EL7201/7211/7221, and EL7062 channels 1/2 with open-loop
and incremental feedback. It also covers mixed drive/encoder terminals,
CSV/CSP selection and swapped limit mapping. The runner calls the actual
`EcmcAxis` Jinja axis renderer and validator to check emitted PDO links,
with a separate, optional `SIM=1` IOC startup script. It never enables
motors or issues motion commands. Real IOC startup and hardware signal
integrity remain separate acceptance checks.

```sh
python3 tests/test_hardware_profile_sim.py -v
```

## Regression tests

```bash
python -m unittest discover -s scripts/jinja2/tests \
  -p 'test_resolve_axis_hardware_profiles.py'
```

Only `feature/hardware-abstraction` is modified; `v11.2.0_RC2` is unchanged.
