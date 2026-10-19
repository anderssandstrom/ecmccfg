+++
title = "Hardware profiles"
weight = 27
chapter = false
+++

Hardware profiles are an opt-in shorthand for the existing axis and encoder YAML
fields. `loadYamlAxis.cmd` and `loadYamlEnc.cmd` call the native
`ecmcExpandHwProfiles` IOC-shell command before backend validation. Expanded YAML
is written under `ECMC_TMP_DIR` (normally `/tmp/...`), consumed by the existing
backend and removed on success. Just pass the original YAML to the normal loader.

Rebuild/install ecmccfg to register the new command. ECB requires no changes or
rebuild; the ECB path requires no Python. Existing explicit PDO configurations without profiles are
copied byte-for-byte, retaining the previous backend behavior.

## Initial profiles

| Section | Profile | Channels | Supplies |
| --- | --- | --- | --- |
| drive | `beckhoff/EL7041/CSV` | 1 | Stepper type, PDO links, enable/reset/warning/error bits, raw velocity denominator 32768 |
| drive | `beckhoff/EL7062/CSV` | 1, 2 | DS402 type, PDO links, raw velocity denominator 2147483648 |
| encoder | `beckhoff/EL7062/incremental` | 1, 2 | Secondary position PDO, incremental type, 32-bit counter, optional touch-probe index homing |

These profiles target the corresponding ecmccfg hardware mappings. EL7041
variants and CSP drive modes are not covered by these initial drive profiles.
EL7062 uses ECMC's existing DS402 status/error handling rather than the EL7041
individual drive bits. EL7041 torque reduction defaults to enabled; explicitly
set `reduceTorqueEnable: false` to disable it.

## Discover profiles from the IOC shell

```iocsh
ecmcListHwProfiles
# After addSlave.cmd has configured EL7062_OPT:
ecmcListCompatibleProfiles(0, 1, 1)
```

The first command lists the installed catalogue, channels, required options,
digital inputs and named index-homing methods. The second takes master, slave
and channel (1-based). Both accept an optional final catalogue filename;
otherwise they use `ECMC_CONFIG_ROOT/hardwareProfiles.json`.

EX7062 `_OPT` setup records the resolved options separately for each master,
slave and channel. For `EL7062_OPT`, the CSV drive profile requires `MODE=CSV`
and `INPUTS=1` for its default limits. The incremental encoder requires `ENC2=1`.
Index homing additionally needs `TP=1`; a mapped capture PDO does not verify
that the index trigger/source has been configured by `applyComponent.cmd`.
Numeric homing IDs do not automatically require capture.

Output reports `COMPATIBLE`, `UNAVAILABLE` with reasons, or `UNVERIFIED` if no
startup metadata exists. These are advisory checks against profile defaults;
YAML overrides (such as external limit inputs) are not evaluated by discovery.
Explicit profiles and existing manual configurations retain their previous behavior.

This first version declares compatibility only for EL7062_OPT. ED/MO7062
options are recorded but have no declared compatible profiles yet. EL7041 and
legacy hardware scripts still support profile expansion, but do not register
metadata, so compatibility is unverified. EX72XX profiles/registration are not
yet supplied. The catalogue is the source of truth for supported profile names.

The registry is a startup snapshot, not live hardware verification. EX7062_OPT
clears its previous slave metadata before reconfiguration. If replacing that
setup with a legacy/custom mapping in the same IOC, first call
`ecmcClearHwProfileSlave(master, slave)` to discard the snapshot.

## Explicit selection and troubleshooting

Specify `profile` in each section that should use a profile. There is no automatic
selection from slave/channel and `profile: auto` is not supported. Expansion is
independent of the `_OPT` registry. Compatibility listing remains an advisory
check of the configured channel; it does not change or reject explicit profiles.

To inspect exactly what the backend receives, retain the expanded YAML:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis.yaml,KEEP_HW_PROFILE=1"
```

The same option works for `loadYamlEnc.cmd`. The loader prints the retained file
path (`FILE_TEMP_PROFILE` or `ECMC_ENC_PROFILE_FILE`) under `ECMC_TMP_DIR`.
The expanded file contains the merged profile defaults and explicit overrides;
it does not annotate which source supplied each field. Normal cleanup remains
the default. You can also expand without loading an axis:

```iocsh
ecmcExpandHwProfiles("./cfg/axis.yaml", "/tmp/axis-expanded.yaml")
```

## Drive scaling

Replace the drive section of an otherwise complete axis YAML with, for example:

```yaml
drive:
  profile: beckhoff/EL7041/CSV
  slave: ${DRV_SID}
  channel: 1
  maxVelocity: 10  # configured full-scale velocity in engineering units/second
```

`master` defaults to 0 and `channel` to 1. `slave` is required. Master/slave values
can be integer addresses or IOC macro strings. Channel must be a literal integer;
the profile checks supported channels and formats it as `01` or `02` in PDO names.

`maxVelocity` supplies `drive.numerator`; the profile supplies the denominator.
This is the velocity corresponding to the raw command scale, **not** the desired
trajectory speed or a motor safety limit. Derive it from the actual configured
terminal settings and mechanics. For example, 2000 full steps/second, 200 full
steps/revolution and 1 mm/revolution give 10 mm/second. The profile does not assume
that the terminal has been configured to 2000 full steps/second.

Alternatively, use the existing `numerator` and `denominator` fields. An explicit
value overrides its profile-derived value. Missing numerator is an error rather
than silently taking a generic schema default. Scaling helper inputs must be
finite positive numbers; use explicit signed numerator/denominator fields for
reversed scaling. Numeric helper macros must be expanded before rendering.

Drive profiles default `axis.mode` to CSV and reject a conflicting mode.

## Digital inputs

Drive profiles supply default limit inputs: DI1 for backward/low limit and DI2 for
forward/high limit. Explicit `input.limit` links override these defaults, including
when only one direction is overridden. Home and interlock inputs are not selected
automatically.

| Profile | DI1 | DI2 |
| --- | --- | --- |
| EL7041 CSV | `driveStatus01.11` | `driveStatus01.12` |
| EL7062 CSV | `binaryInputs<channel>.0` | `binaryInputs<channel>.1` |

The slave, master and channel come from the drive profile selection. Select an
available input explicitly with `driveInput`, for example:

```yaml
input:
  home: {driveInput: 1}
  limit:
    backward: ec0.s8.binaryInput01  # external low-limit switch
    forward: {driveInput: 2}
  homePolarity: 1
```

This example uses DI1 for home and a separate external input for the low limit.
`driveInput` is supported for `home`, `interlock`, `limit.backward` and
`limit.forward`. It requires a drive profile and a supported integer input number
(currently 1 or 2). Ordinary EtherCAT links and `plcOverride` remain supported.
Polarity fields retain the existing schema behavior; profiles do not change them.

## Incremental feedback and homing

Drive and encoder profiles are independent. This section works in an axis file
or a standalone encoder file loaded with `loadYamlEnc.cmd`:

```yaml
encoder:
  profile: beckhoff/EL7062/incremental
  slave: ${ENC_SID}
  channel: 1
  countsPerMotorRev: 1048576
  unitsPerMotorRev: 360
  homing:
    method: low-limit-index
    position: 0
    velocity:
      to: 360
      from: 36
    acceleration: 360
    deceleration: 360
```

`countsPerMotorRev` is the effective reported position counts, not encoder lines.
It supplies the denominator; `unitsPerMotorRev` supplies the numerator (default 1).
Use values matching the configured position representation. Explicit scaling
fields remain supported and take precedence.

Supported named methods are `low-limit-index` (sequence 11) and
`high-limit-index` (sequence 12). These are limit-switch plus index procedures,
not index-only procedures. Select and wire the appropriate axis limit inputs.
The selected method supplies the touch-probe control/status/position links, latch
arm command 17 with width 5, and latch count 1. Explicit latch fields and homing
parameters override defaults. A conflicting explicit homing `type` is rejected.
Without a named method, the profile adds no homing procedure or latch settings;
existing numeric homing configuration can still be supplied explicitly:

```yaml
encoder:
  profile: beckhoff/EL7062/incremental
  slave: ${ENC_SID}
  countsPerMotorRev: 1048576
  unitsPerMotorRev: 360
  homing:
    type: 1  # low-limit switch homing, no latch/touch probe
    position: 0
    velocity: {to: 36, from: 3.6}
```

Numeric sequence IDs pass through to the existing homing implementation. IDs
1–10 use switches, and 15/25 set position without index capture. Other procedures
retain their normal requirements (for example absolute feedback for 21/22 and
external handshaking for 26); a profile does not remove those requirements.
Numeric IDs 11/12 still require explicit latch configuration, or use the named
index methods above to obtain it automatically. See the homing manual for the
complete sequence descriptions.

For index homing, the terminal must already have the matching PDOs and index trigger configured.
For example, the existing EL7062 component setup uses
`TP1_POS_SRC=SEC,TP1_TRG=INDEX` with `Encoder-Generic-INC`. Profiles do not issue SDO
writes, configure hardware, or verify live device identity. See
[homing]({{< relref "/manual/motion_cfg/homing.md" >}}) for the startup setup.

## Overrides, inspection and installation

Nested mappings merge recursively; explicit scalar values and lists replace the
profile values. For example, `error: [14]` replaces the EL7041 error list, and
`error: []` explicitly removes those alarm links. Use overrides only for the
actual hardware mapping in use.

The loaders handle expansion automatically. For direct inspection in IOC shell:

```iocsh
on error halt
ecmcExpandHwProfiles("./cfg/axis.yaml", "/tmp/axis-expanded.yaml")
```

The optional third argument is the catalogue filename. By default the command
uses `ECMC_CONFIG_ROOT/hardwareProfiles.json`. Output parent directories are
created. Errors propagate to IOC shell, so `on error halt` stops startup before
an older generated file can be loaded. Failed-startup temporary files may remain
for diagnosis.

The core and IOC-shell adapter live in `src`; `GNUmakefile` builds them and
installs the registrar DBD. C++17 and the bundled headers in `src/vendor` are used;
there is no build dependency on an ECB checkout. See `utils/hw_profiles/README.md`
for build and test details.

The optional standalone tool uses the same core:

```bash
make -C utils/hw_profiles
utils/hw_profiles/ecmc-hw-profiles --profiles scripts/jinja2/hardwareProfiles.json \
  axis.yaml axis-expanded.yaml
```

Profile output uses YAML-compatible JSON syntax accepted by both backends.
PLC paths and macro strings are preserved; profile source comments are not copied.
The original source is not modified. Configurations without profiles retain their
original text. The examples load `cfg/*.yaml` directly; their Makefile is optional
and only generates offline expansions for inspection.

The catalogue remains `scripts/jinja2/hardwareProfiles.json`, installed by the
existing script rules. The optional Python inspection tool remains available.

Run native IOC-shell tests against a built EPICS Base without Python:

```bash
make -C utils/hw_profiles test-iocsh EPICS_BASE=/path/to/epics-base
```

For optional rendering/regression tests (the test harness itself uses Python):

```bash
PROFILE_TOOL=/path/to/ecmc-hw-profiles ECB_BIN=/path/to/existing/ecb \
  python -m pytest scripts/jinja2/pytest
```
