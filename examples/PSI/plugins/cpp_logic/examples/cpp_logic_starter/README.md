# `CPP-LOGIC-STARTER-IOC`

This IOC example is the smallest practical starting point for a new
`cpp_logic` shared library.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `CPP-LOGIC-STARTER-IOC_startup.script`
- `CPP-LOGIC-STARTER-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc CPP-LOGIC-STARTER-IOC`
3. start the IOC with `CPP-LOGIC-STARTER-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`
- `qt/CPP-LOGIC-STARTER-IOC_cpp_logic.ui`

The startup script uses the defaults from `loadCppLogic.cmd`, so with
`LOAD_APP_PVS=1` it automatically loads:

- `bin/main.so`
- `bin/main.so.substitutions`

`make` also generates a simple IOC-local caQtDM panel:

```sh
caqtdm qt/CPP-LOGIC-STARTER-IOC_cpp_logic.ui
```
