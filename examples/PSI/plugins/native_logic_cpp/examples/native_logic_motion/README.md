# `NATIVE-LOGIC-CPP-MOTION-IOC`

This IOC example uses the native `MC_*` wrappers against axis 1, following the
same open-loop EL7041 axis setup used by the motion MTEST examples.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `cfg/openloop.yaml`
- `NATIVE-LOGIC-CPP-MOTION-IOC_startup.script`
- `NATIVE-LOGIC-CPP-MOTION-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc NATIVE-LOGIC-CPP-MOTION-IOC`
3. start the IOC with `NATIVE-LOGIC-CPP-MOTION-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`

The startup script uses the defaults from `loadNativeLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`
