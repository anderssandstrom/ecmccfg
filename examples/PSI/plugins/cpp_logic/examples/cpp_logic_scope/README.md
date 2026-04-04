# `CPP-LOGIC-SCOPE-IOC`

This IOC example uses EL3702 and EL1252 terminals to build a small
trigger-aligned scope around the C++ logic array helpers.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `CPP-LOGIC-SCOPE-IOC_startup.script`
- `CPP-LOGIC-SCOPE-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc CPP-LOGIC-SCOPE-IOC`
3. start the IOC with `CPP-LOGIC-SCOPE-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`
