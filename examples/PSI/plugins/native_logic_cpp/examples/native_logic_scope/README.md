# `NATIVE-LOGIC-CPP-SCOPE-IOC`

This IOC example uses EL3702 and EL1252 terminals to build a small
trigger-aligned scope around the native logic array helpers.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `NATIVE-LOGIC-CPP-SCOPE-IOC_startup.script`
- `NATIVE-LOGIC-CPP-SCOPE-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc NATIVE-LOGIC-CPP-SCOPE-IOC`
3. start the IOC with `NATIVE-LOGIC-CPP-SCOPE-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`

The startup script uses the defaults from `loadNativeLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`
