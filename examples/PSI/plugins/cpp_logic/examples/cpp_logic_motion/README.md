# `MTEST04-MTN-CPP-LOGIC`

This IOC example uses the native `MC_*` wrappers against axis 1, following the
same open-loop EL7041 axis setup used by the motion MTEST examples.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `cfg/openloop.yaml`
- `MTEST04-MTN-CPP-LOGIC_startup.script`
- `MTEST04-MTN-CPP-LOGIC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc MTEST04-MTN-CPP-LOGIC`
3. start the IOC with `MTEST04-MTN-CPP-LOGIC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`
- `qt/MTEST04-MTN-CPP-LOGIC_cpp_logic.ui`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`

`make` also generates a simple IOC-local caQtDM panel:

```sh
caqtdm qt/MTEST04-MTN-CPP-LOGIC_cpp_logic.ui
```
