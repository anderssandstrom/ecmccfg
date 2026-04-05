+++
title = "C++ Logic"
weight = 13
chapter = false
+++

## Scope
This page documents the additive `cpp_logic` interface in `ecmc`.

Use it when:

- you want to run small cyclic user logic written in C/C++
- that logic should bind directly to `ecmc` data items
- and it should expose its own runtime values on a dedicated asyn interface

`cpp_logic` does **not** replace the existing plugin ABI in `ecmcPluginDefs.h`.
It is a second interface in `ecmc`, intended for user-defined cyclic logic
modules rather than full standalone plugins.

## Recommended IOC Startup Interface

The normal IOC-level entry point is:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}scripts/loadCppLogic.cmd, "FILE=/path/to/main.so,LOAD_APP_PVS=1,REPORT=1"
```

Important defaults in `loadCppLogic.cmd`:

- `FILE`: defaults to `bin/main.so`
- `LOGIC_ID`: defaults to the next free id
- `ASYN_PORT`: defaults to `CPP.LOGIC<LOGIC_ID>`
- `APP_PANEL`: defaults to `qt/${IOC}_cpp_logic.ui`
- `LOAD_DEFAULT_PVS`: defaults to `1`
- `LOAD_APP_PVS`: defaults to `0`
- `EPICS_SUBST`: defaults to `${FILE}.substitutions` when `LOAD_APP_PVS=1`
- `DB_PREFIX`: defaults to `$(IOC):`

The wrapper:

1. loads one compiled C++ logic shared library
2. optionally reports the loaded object
3. loads the built-in control/status PVs
4. optionally loads generated substitutions for user-defined `epics.*` exports

## Underlying ecmc Commands

The underlying parser commands are:

```text
Cfg.LoadCppLogic(<id>,<file>)
Cfg.LoadCppLogic(<id>,<file>,<config>)
Cfg.ReportCppLogic(<id>)
```

The IOC wrapper script mainly fills in defaults and handles the EPICS record
loading around those commands.

## C++ Programming Model

The public C++ headers are:

- `ecmcCppLogic.hpp`
- `ecmcCppMotion.hpp`
- `ecmcCppControl.hpp`
- `ecmcCppUtils.hpp`

For a helper/header-oriented summary, see
[C++ Logic Helpers]({{< relref "/manual/plugins/cpp_logic_helpers.md" >}}).

Typical user code looks like:

```cpp
#include "ecmcCppLogic.hpp"

struct MyLogic : public ecmcCpp::LogicBase {
  int32_t actual_position {0};
  int16_t drive_control {0};
  int16_t velocity_setpoint {1000};

  MyLogic() {
    ecmc.input("ec.s14.positionActual01", actual_position)
        .output("ec.s14.driveControl01", drive_control)
        .output("ec.s14.velocitySetpoint01", velocity_setpoint);

    epics.readOnly("main.actual_position", actual_position)
         .writable("main.velocity_setpoint", velocity_setpoint);
  }

  void run() override {
    drive_control = 1;
  }
};

ECMC_CPP_LOGIC_REGISTER_DEFAULT(MyLogic)
```

The main split is:

- `ecmc...`: live realtime bindings to `ecmc` item names
- `epics...`: values exported on the C++ logic instance's dedicated asyn port

## Supported Binding Styles

For normal scalars, the C++ value type is inferred from the bound variable type.

Supported patterns include:

- scalar input/output:
  - `ecmc.input(...)`
  - `ecmc.output(...)`
- arrays:
  - `ecmc.inputArray(...)`
  - `ecmc.outputArray(...)`
- raw bytes:
  - `ecmc.inputBytes(...)`
  - `ecmc.outputBytes(...)`
- startup-sized vectors:
  - `ecmc.inputAutoArray(...)`
  - `ecmc.outputAutoArray(...)`

On the exported EPICS side, corresponding helpers exist for:

- scalars:
  - `epics.readOnly(...)`
  - `epics.writable(...)`
- arrays:
  - `epics.readOnlyArray(...)`
  - `epics.writableArray(...)`
- raw bytes:
  - `epics.readOnlyBytes(...)`
  - `epics.writableBytes(...)`

## Runtime Interface

Each loaded `cpp_logic` instance gets:

- its own dedicated asyn port
- built-in control, timing, and debug variables on that port
- all exported `epics.*` variables on that same port

The built-in core substitutions are loaded from:

```text
$(ecmccfg_DIR)db/generic/ecmcCppLogicCore.substitutions
```

The generic caQtDM runtime panel is:

```text
$(ecmccfg_DIR)qt/ecmcCppLogic.ui
```

Open it with macros such as:

```bash
caqtdm -macro "IOC=<ioc-name>,CPP_ID=0" $(ecmccfg_DIR)qt/ecmcCppLogic.ui
```

There is also a compact overview panel for several logic instances:

```bash
caqtdm -macro "IOC=<ioc-name>" $(ecmccfg_DIR)qt/ecmcCppLogicOverview.ui
```

That overview shows logic ids `0..7` and opens one instance in
`ecmcCppLogic.ui`.

The built-in runtime names currently include:

- `logic.ctrl.word`
- `logic.ctrl.rate_ms`
- `logic.stat.rate_ms`
- `logic.ctrl.update_rate_ms`
- `logic.stat.update_rate_ms`
- `logic.stat.exec_ms`
- `logic.stat.input_ms`
- `logic.stat.output_ms`
- `logic.stat.total_ms`
- `logic.stat.div`
- `logic.stat.count`
- `logic.stat.dbg_txt`

The generic core substitutions also add one soft EPICS record for the
application panel path:

- `$(IOC):CppLogic$(CPP_ID)-AppPnlPath`

That defaults to `qt/<IOC>_cpp_logic.ui` and is used by the `Open app panel`
button in the generic `ecmcCppLogic.ui` panel. Override it with
`APP_PANEL=...` in `loadCppLogic.cmd` if needed.

Current control word bits are:

- bit 0: enable execution
- bit 1: enable timing measurements
- bit 2: enable debug text/print publishing

## Generated EPICS Substitutions

User-defined `epics.*` exports can be turned into substitutions offline with:

```bash
python3 examples/PSI/plugins/cpp_logic/utils/ecmcCppLogicSubstGen.py \
  --logic-lib path/to/main.so \
  --output cpp_logic.subs
```

The `loadCppLogic.cmd` wrapper can then load:

- built-in core substitutions automatically
- the generated custom substitutions when `LOAD_APP_PVS=1`

In the IOC-style `cpp_logic` examples, the custom substitutions are normally
staged as:

```text
bin/main.so.substitutions
```

The IOC-style examples also generate a simple local caQtDM panel by default:

```text
qt/<IOC>_cpp_logic.ui
```

Disable that generation with:

```bash
make GENERATE_QT=0
```

For new IOC projects there is also a scaffold helper in the `cpp_logic` utils
area:

```bash
python3 examples/PSI/plugins/cpp_logic/utils/cpp_logic_new_ioc.py <new-dir>
```

Generated and checked-in startup scripts also include exact `caqtdm` commands
for:

- `ecmcCppLogicOverview.ui`
- `ecmcCppLogic.ui`
- the IOC-local generated app panel

## Execution Order

The `cpp_logic` execution point is before the safety plugin.

That means user logic can produce values that the safety plugin may still
override afterwards, which is the intended order.

## Examples

IOC-style examples are available in:

```text
examples/PSI/plugins/cpp_logic/
```

Current example families include:

- starter IOC project with one input, two outputs, and two exported PVs
- minimal scalar binding/export
- control/helper usage
- motion wrappers (`MC_*` style)
- EL3702/EL1252-style triggered scope capture

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [C++ Logic Helpers]({{< relref "/manual/plugins/cpp_logic_helpers.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
