# Native hardware profile support

The implementation lives in `src/ecmcHardwareProfiles.cpp` and
`src/ecmcHardwareProfilesInternal.h`. The IOC-shell adapter is
`src/ecmcHardwareProfilesIocsh.cpp`, registered by
`dbd/ecmcHardwareProfiles.dbd`. `GNUmakefile` builds them into ecmccfg.

## Normal IOC use

Load the original YAML with `loadYamlAxis.cmd` or `loadYamlEnc.cmd`. The loaders
call the native command before backend validation and rendering, place the
expanded YAML under `ECMC_TMP_DIR` (normally under `/tmp`), then remove the
intermediate file on success. No separate generation command is required.

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis.yaml"
```

Use `ECMC_CFG_TOOL=ecb` for a completely Python-free runtime. ECB remains unchanged.
Rebuild/install **ecmccfg** to register the new command. Both backends accept the
expanded YAML. Manual PDO configurations without profiles pass through byte-for-byte.
Profile selection is explicit; the IOC registry is used only by compatibility listing.
Pass `KEEP_HW_PROFILE=1` to either YAML loader to retain the expanded file and
print its path for inspection.

The command is also available directly:

```iocsh
on error halt
ecmcExpandHwProfiles("./cfg/axis.yaml", "/tmp/axis-expanded.yaml")
```

The optional third argument selects the catalogue; otherwise it uses
`ECMC_CONFIG_ROOT/hardwareProfiles.json`. Input/output must differ. Output parent
directories are created. Parse/profile errors are reported via `iocshSetError`,
so `on error halt` prevents loading an older output after a failed expansion.
Temporary files may remain on a failed startup to assist diagnosis.

Only data is expanded: no hardware settings, SDO writes, or homing moves are
performed. IOC macros and PLC paths are preserved. Profile output uses
YAML-compatible JSON. Normal schema validation still happens in the backend.

## Build dependencies

The native core requires C++17. The nlohmann/json and rapidyaml single headers and
licences are bundled under `src/vendor`; no ECB checkout is required to build
or run this module. `GNUmakefile` also links `stdc++fs` for the supported GCC 8
builds. This module does not change the ECB sources or ABI.

## Optional offline tool

The standalone CLI wraps the same core code:

```sh
make -C utils/hw_profiles
utils/hw_profiles/ecmc-hw-profiles \
  --profiles scripts/jinja2/hardwareProfiles.json cfg/axis.yaml /tmp/axis-expanded.yaml
```

`make -C examples/PSI/hw_profiles` remains available for inspecting offline
expansions. The example startup files load `cfg/*.yaml` directly and do not
require that make step. Python is not required for building or generation.

## Tests

Real IOC-shell registration, default catalogue lookup, error propagation and
`on error halt` can be tested without Python or an EtherCAT IOC:

```sh
make -C utils/hw_profiles test-iocsh EPICS_BASE=/path/to/built/epics-base
```

Override `EPICS_HOST_ARCH`, `EPICS_OS_CLASS` or `LDLIBS` for your platform if
needed (for example `LDLIBS=-lstdc++fs` on GCC 8). The test links EPICS libCom.
The full ecmccfg module build uses the site's `/ioc/tools/driver.makefile`.

The optional Python regression suite also checks native generation and rendering
with an unchanged ECB binary:

```sh
PROFILE_TOOL="$PWD/utils/hw_profiles/ecmc-hw-profiles" ECB_BIN=/path/to/ecb \
  python -m pytest scripts/jinja2/pytest
```

Keep the C++ resolver and `scripts/jinja2/ecmcHardwareProfiles.py` aligned.
Both use `scripts/jinja2/hardwareProfiles.json`.
