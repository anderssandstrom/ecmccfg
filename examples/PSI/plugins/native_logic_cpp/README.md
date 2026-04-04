# Native Logic C++ IOC Examples

This directory contains IOC-style example projects for the additive native C/C++
logic interface in `ecmc`.

Each example follows the same basic layout as the `MTEST` IOC examples used for
`ecmc_plugin_strucpp`:

- IOC-root `Makefile`
- IOC-named `*_startup.script`
- IOC-named `*_parameters.yaml`
- `src/` with `main.cpp` and a small build `Makefile`
- `bin/` for staged `main.so` and `main.so.substitutions`

Examples:

- `examples/native_logic_minimal`
- `examples/native_logic_control`
- `examples/native_logic_motion`
- `examples/native_logic_scope`

Helper files:

- `utils/native_logic_ioc.make`: shared native logic build helper
- `utils/ecmcNativeLogicSubstGen.py`: substitutions generator for `epics.*` exports

Notes:

- The default build helper points at a sibling `ecmc` source tree through `ECMC=...`.
  Override `ECMC` if your local layout differs.
- IOC startup is intended to use:
  - `$(ecmccfg_DIR)scripts/loadNativeLogic.cmd`
- Built-in native-logic PVs load by default through that script.
- Generated custom `epics.*` substitutions are loaded through the IOC-local
  `*_native_logic.subs` file.
