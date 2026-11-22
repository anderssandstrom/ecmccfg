# Slave-selected axis hardware defaults (work in progress)

The axis YAML selects **slave positions**, not terminal types. The type is
registered automatically by `addSlave.cmd` under the IOC environment key
`ECMC_HW_M<master>_S<slave>`, using its `HW_DESC` argument.

Example startup configuration:
```text
addSlave.cmd HW_DESC=EL7041-0052,SLAVE_ID=7
addSlave.cmd HW_DESC=EL5101,SLAVE_ID=8
```

Example axis YAML:
```yaml
drive:
  slave: $(DRV_SLAVE)
  numerator: 20
  control: ec0.s7.driveControl01

encoder:
  slave: $(ENC_SLAVE)
  position: ec0.s8.positionActual01

input:
  limit:
    forward: ec0.s7.binaryInput01
    backward: ec0.s7.binaryInput02
```

Here the *drive* profile is selected automatically from slave 7 and the
*encoder* profile from slave 8. Other existing axis YAML sections can remain
unchanged. The new `slave` selector is consumed by the preprocessing step and
is **not** passed to existing axis schemas or Jinja/ECB templates.

Hardware defaults live at
`scripts/jinja2/hardwareProfiles/<HW_DESC>/drive.yaml`, with optional
`encoder.yaml` and `input.yaml`. For variants such as EL7041-0052, the
resolver tries the exact HW_DESC and then the base model EL7041.

Hardware-profile values may use `$(MASTER)` and `$(SLAVE)` placeholders.
For example:
```yaml
drive:
  type: 0
  control: ec$(MASTER).s$(SLAVE).driveControl01
```

Deep merging means axis-specific fields always take precedence. Only
sections with a numeric `slave` selector are enriched with defaults. Legacy
configurations without these selectors are passed through unchanged.
An unknown slave or missing explicitly selected hardware profile is an error.

The existing `loadYamlAxis.cmd` handles preprocessing before **both** Jinja
and ECB. Unchanged legacy configs retain the original ECB path without an
additional Python invocation. **New slave-selected hardware profiles currently
use a Python preprocessing step even with ECB**. A native ECB implementation
would be needed to remove that dependency completely.

## Current limitations

- The initial included EL7041 drive and EL5101 encoder profiles contain
  conservative demonstration defaults only. Mechanical scaling and actual
  PDO links must still be supplied and validated for each installation.
- Slave registration assumes `addSlave.cmd` runs before axis YAML loading
  in the same IOC environment.
- Slave selectors may be numeric or reference IOC environment macros such as
  `$(DRV_SLAVE)` and `$(ENC_SLAVE)`. The resolver expands these selectors
  before looking up the registered slave hardware. Nested macros and
  `$(NAME=default)` are supported. Missing or nonnumeric macro values fail
  configuration rather than silently selecting another terminal.
- The IOC must define the slave macros before `loadYamlAxis.cmd` executes.
- Support for input profiles exists in the resolver, but default wiring for
  actual terminal variants must be reviewed before shipping profiles.
- ECMC bit aliases require the separate hardware-abstraction ECMC branch.
- This is a draft feature requiring IOC integration testing.

## Standalone test

```sh
ECMC_HW_M0_S7=EL7041 ECMC_HW_M0_S8=EL5101 DRV_SLAVE=7 ENC_SLAVE=8 \
python scripts/jinja2/resolveAxisHardwareProfiles.py axis.yaml resolved.yaml \
  --profiles scripts/jinja2/hardwareProfiles

python -m unittest discover -s scripts/jinja2/tests \
  -p 'test_resolve_axis_hardware_profiles.py'
```

No change was made to either repository's `v11.2.0_RC2` branch.
