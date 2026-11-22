# Axis hardware profiles (opt-in, initial implementation)

This is a first increment toward hardware-dependent axis defaults. It does **not**
yet infer hardware types from `addSlave.cmd`. Profiles are selected explicitly
and resolved before either the Python/Jinja renderer or ECB sees the axis YAML.

To enable preprocessing in `loadYamlAxis.cmd`, supply `HW_PROFILES=1`.
The existing behaviour remains the default when that macro is omitted.

```yaml
hardwareProfiles:
  drive: EL7041
  encoder: EL5101

drive:
  numerator: 20    # Explicit application value overrides the profile default
  control: ec0.s$(DRV_SLAVE).driveControl01
  status: ec0.s$(DRV_SLAVE).driveStatus01
  setpoint: ec0.s$(DRV_SLAVE).velocitySetpoint01

encoder:
  position: ec0.s$(ENC_SLAVE).positionActual01
```

The current profiles are intentionally minimal. They do not assume mechanical
scaling or terminal-specific PDO selections that vary between configurations.

Profile file format: `scripts/jinja2/hardwareProfiles/EL7041/drive.yaml`

```yaml
drive:
  type: 0
```

Profiles apply **only** to sections explicitly selected in the
`hardwareProfiles` map. The resolver deep-merges defaults, then overrides them
with the axis YAML; explicit values including `false`, `0`, and `null` win.
After the merge, `hardwareProfiles` is removed before the existing schema
validator runs. Missing or malformed explicitly requested profiles fail closed.

A standalone preprocessing command is available for testing:

```sh
python scripts/jinja2/resolveAxisHardwareProfiles.py axis.yaml resolved.yaml \
    --profiles scripts/jinja2/hardwareProfiles
python -m unittest discover -s scripts/jinja2/tests -p test_resolve_axis_hardware_profiles.py
```

**Next increments:** register slave-to-HW_DESC metadata from `addSlave.cmd`;
introduce a slave-based section selector with fallback matching for variants
(e.g. EL7041-0052 → EL7041); add real, hardware-reviewed drive and encoder
defaults and integration tests. Python preprocessing is currently needed even
when ECB is selected; a native ECB resolver can later remove that dependency.

The ECMC side is developed in the matching
`anderssandstrom/ecmc:feature/hardware-abstraction` branch.
