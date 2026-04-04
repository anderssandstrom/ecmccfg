# `CPP-LOGIC-CONTROL-IOC`

This IOC example uses the native control and utility helpers on the same direct
EL7041 mapping as the minimal example.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `CPP-LOGIC-CONTROL-IOC_startup.script`
- `CPP-LOGIC-CONTROL-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc CPP-LOGIC-CONTROL-IOC`
3. start the IOC with `CPP-LOGIC-CONTROL-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`
