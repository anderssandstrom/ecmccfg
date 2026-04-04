# `CPP-LOGIC-MOTION-IOC`

This IOC example uses the native `MC_*` wrappers against axis 1, following the
same open-loop EL7041 axis setup used by the motion MTEST examples.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `cfg/openloop.yaml`
- `CPP-LOGIC-MOTION-IOC_startup.script`
- `CPP-LOGIC-MOTION-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc CPP-LOGIC-MOTION-IOC`
3. start the IOC with `CPP-LOGIC-MOTION-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`
- `qt/CPP-LOGIC-MOTION-IOC_cpp_logic.ui`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`

`make` also generates a simple IOC-local caQtDM panel:

```sh
caqtdm qt/CPP-LOGIC-MOTION-IOC_cpp_logic.ui
```
