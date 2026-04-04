# `NATIVE-LOGIC-CPP-MINIMAL-IOC`

This IOC example is the native C/C++ equivalent of the small direct-mapped
MTEST style example.

The source tree is:

- `src/main.cpp`
- `src/Makefile`
- `NATIVE-LOGIC-CPP-MINIMAL-IOC_startup.script`
- `NATIVE-LOGIC-CPP-MINIMAL-IOC_parameters.yaml`

Expected flow:

1. `make`
2. `ioc install --clean -V --ioc NATIVE-LOGIC-CPP-MINIMAL-IOC`
3. start the IOC with `NATIVE-LOGIC-CPP-MINIMAL-IOC_startup.script`

The build stages:

- `bin/main.so`
- `bin/main.so.substitutions`
- `NATIVE-LOGIC-CPP-MINIMAL-IOC_native_logic.subs`
