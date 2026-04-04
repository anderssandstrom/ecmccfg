# `CPP-LOGIC-MINIMAL-IOC`

This IOC example is the native C/C++ equivalent of the small direct-mapped
MTEST style example.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `CPP-LOGIC-MINIMAL-IOC_startup.script`
- `CPP-LOGIC-MINIMAL-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc CPP-LOGIC-MINIMAL-IOC`
3. start the IOC with `CPP-LOGIC-MINIMAL-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`
