# Cpp Logic IOC Examples

This directory contains IOC-style example projects for the additive cpp C/C++
logic interface in `ecmc`.

Each example follows the same basic layout as the `MTEST` IOC examples used for
`ecmc_plugin_strucpp`:

- IOC-root `Makefile`
- IOC-named `*_startup.script`
- IOC-named `*_parameters.yaml`
- `src/` with `main.cpp` and a small build `Makefile`
- `bin/` for staged `main.so` and `main.so.substitutions`
- `qt/` for an auto-generated simple caQtDM panel

Examples:

- `examples/cpp_logic_starter`
- `examples/cpp_logic_minimal`
- `examples/cpp_logic_control`
- `examples/cpp_logic_motion`
- `examples/cpp_logic_scope`

Helper files:

- `utils/cpp_logic_ioc.make`: shared cpp logic build helper
- `utils/ecmcCppLogicSubstGen.py`: substitutions generator for `epics.*` exports
- `utils/cpp_logic_ioc_qtgen.py`: simple IOC-local caQtDM panel generator
- `utils/cpp_logic_new_ioc.py`: scaffold generator for a new IOC-style cpp logic example

Generic UI:

- `$(ecmccfg_DIR)qt/ecmcCppLogic.ui`: generic runtime panel for one cpp logic instance
  - uses macros `IOC=<ioc-name>,CPP_ID=<logic-id>`
  - includes an `Open app panel` button
  - that button resolves the IOC-local app panel path from
    `$(IOC):CppLogic$(CPP_ID)-AppPnlPath`
- `$(ecmccfg_DIR)qt/ecmcCppLogicOverview.ui`: compact overview for logic ids `0..7`
  - uses macro `IOC=<ioc-name>`
  - each row opens one instance in `ecmcCppLogic.ui`

Notes:

- The default build helper points at a sibling `ecmc` source tree through `ECMC=...`.
  Override `ECMC` if your local layout differs.
- IOC startup is intended to use:
  - `$(ecmccfg_DIR)scripts/loadCppLogic.cmd`
- Built-in cpp_logic PVs load by default through that script.
- With `LOAD_APP_PVS=1`, generated custom `epics.*` substitutions default to
  `bin/main.so.substitutions`.
- `make` also generates `qt/<IOC>_cpp_logic.ui` by default. Disable with
  `make GENERATE_QT=0`.
- `loadCppLogic.cmd` also publishes a soft PV for the app panel path:
  - `$(IOC):CppLogic$(CPP_ID)-AppPnlPath`
  - default value: `qt/<IOC>_cpp_logic.ui`
  - override with `APP_PANEL=...`
