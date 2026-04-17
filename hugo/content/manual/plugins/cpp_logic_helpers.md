+++
title = "C++ Logic Helpers"
weight = 14
chapter = false
+++

## Scope
This page documents the helper headers that come with the additive
`cpp_logic` interface in `ecmc`.

Use it when:

- you already know how to load a `cpp_logic` module
- and you want a quick reference for the helper classes/functions available in
  the C++ headers

For the IOC loading and runtime model, start with
[C++ Logic]({{< relref "/manual/plugins/cpp_logic.md" >}}).

## Main Headers

The current helper headers are:

- `ecmcCppLogic.hpp`
  Includes `ecmcCpp::getMacrosText()` for reading the free-form `MACROS` startup string.
- `ecmcCppMotion.hpp`
- `ecmcCppControl.hpp`
- `ecmcCppUtils.hpp`
- `ecmcCppTrace.hpp`
- `ecmcCppPersist.hpp`

These are additive helper layers on top of the `cpp_logic` ABI. They do not
replace the original plugin ABI in `ecmcPluginDefs.h`.

## ecmcCppLogic.hpp

This is the core C++ programming layer.

It provides:

- `ecmcCpp::LogicBase`
- registration macros such as:
  - `ECMC_CPP_LOGIC_REGISTER(...)`
  - `ECMC_CPP_LOGIC_REGISTER_DEFAULT(...)`
- host-service access helpers
- the `ecmc...` item-binding builder
- the `epics...` export builder

Typical pattern:

```cpp
struct MyLogic : public ecmcCpp::LogicBase {
  int32_t actual_position {0};
  int16_t velocity_setpoint {1000};

  MyLogic() {
    ecmc.input("ec.s14.positionActual01", actual_position);
    epics.writable("main.velocity_setpoint", velocity_setpoint);
  }

  void run() override {}
};

ECMC_CPP_LOGIC_REGISTER_DEFAULT(MyLogic)
```

### Binding/export helpers

For scalar values:

- `ecmc.input(...)`
- `ecmc.output(...)`
- `epics.readOnly(...)`
- `epics.writable(...)`

For arrays:

- `ecmc.inputArray(...)`
- `ecmc.outputArray(...)`
- `ecmc.inputAutoArray(...)`
- `ecmc.outputAutoArray(...)`
- `epics.readOnlyArray(...)`
- `epics.writableArray(...)`

For raw buffers:

- `ecmc.inputBytes(...)`
- `ecmc.outputBytes(...)`
- `epics.readOnlyBytes(...)`
- `epics.writableBytes(...)`

### Runtime/service helpers

The core header also exposes small helper functions backed by ECMC host
services:

- `ecmcCpp::getCycleTimeS()`
- `ecmcCpp::getEcMasterStateWord(...)`
- `ecmcCpp::getEcSlaveStateWord(...)`
- `ecmcCpp::setEnableDbg(...)`
- `ecmcCpp::publishDebugText(...)`

Typical use cases:

- read the configured realtime cycle time without hard-coding it
- inspect EtherCAT master/slave state words from logic code
- enable cpp-logic debug publishing from code
- publish one-line runtime debug/status messages to the built-in debug text path

### Axis host-service helpers

`ecmcCppLogic.hpp` also exposes direct axis-oriented helpers backed by ECMC host
services. These are separate from the `MC_*` wrappers in `ecmcCppMotion.hpp`.

Trajectory and encoder source selection:

- `ecmcCpp::axisUseInternalTraj(...)`
- `ecmcCpp::axisUseExternalTraj(...)`
- `ecmcCpp::axisUseInternalEnc(...)`
- `ecmcCpp::axisUseExternalEnc(...)`

Axis state readback:

- `ecmcCpp::axisGetActualPos(...)`
- `ecmcCpp::axisGetSetpointPos(...)`
- `ecmcCpp::axisGetActualVel(...)`
- `ecmcCpp::axisGetSetpointVel(...)`
- `ecmcCpp::axisIsEnabled(...)`
- `ecmcCpp::axisIsBusy(...)`
- `ecmcCpp::axisHasError(...)`
- `ecmcCpp::axisGetErrorId(...)`

External source value injection:

- `ecmcCpp::axisSetExternalSetpointPos(...)`
- `ecmcCpp::axisSetExternalEncoderPos(...)`

Use these helpers when the logic should work directly with ECMC axis source
selection or external trajectory/encoder feeds, instead of using the higher
level PLCopen-style `MC_*` blocks.

## ecmcCppControl.hpp

Current control helper:

- `ecmcCpp::Pid`

It supports:

- `Kp`, `Ki`, `Kd`
- feed-forward with `FF` and `Kff`
- output limiting with `OutMin` / `OutMax`
- integral limiting with `IMin` / `IMax`
- optional derivative filtering with `DFilterTau`

Outputs include:

- `Output`
- `Error`
- `PPart`
- `IPart`
- `DPart`
- `FFPart`
- `Limited`

## ecmcCppMotion.hpp

This header provides `MC_*` style wrappers on top of the existing `ecmc`
motion backend.

Current wrappers include:

- `ecmcCpp::McAxisRef`
- `ecmcCpp::McPower`
- `ecmcCpp::McReset`
- `ecmcCpp::McMoveAbsolute`
- `ecmcCpp::McMoveRelative`
- `ecmcCpp::McHome`
- `ecmcCpp::McMoveVelocity`
- `ecmcCpp::McStop`
- `ecmcCpp::McReadStatus`
- `ecmcCpp::McReadActualPosition`
- `ecmcCpp::McReadActualVelocity`

Use it when you want PLCopen-style motion patterns from native C++ logic
without writing the lower-level axis API calls directly.

## ecmcCppUtils.hpp

This header contains the small reusable helpers that are most often used in
scan-based logic.

### Triggers and timers

- `ecmcCpp::RTrig`
- `ecmcCpp::FTrig`
- `ecmcCpp::Ton`
- `ecmcCpp::Tof`
- `ecmcCpp::Tp`

These are intended to feel familiar to users coming from IEC/ST helper blocks.

### Latches and toggles

- `ecmcCpp::Sr`
- `ecmcCpp::Rs`
- `ecmcCpp::FlipFlop`

### Small runtime/state helpers

- `ecmcCpp::Blink`
- `ecmcCpp::StateTimer<T>`
- `ecmcCpp::DebounceBool`
- `ecmcCpp::StartupDelay`
- `ecmcCpp::RateLimiter`
- `ecmcCpp::FirstOrderFilter`
- `ecmcCpp::HysteresisBool`
- `ecmcCpp::Integrator`
- `ecmcCpp::MoveAverage`
- `ecmcCpp::MinMaxHold`

### Scalar helper functions

- `ecmcCpp::applyDeadband(...)`
- `ecmcCpp::clampValue(...)`
- `ecmcCpp::inWindow(...)`

### EtherCAT status wrappers

- `ecmcCpp::EcMasterStatus`
- `ecmcCpp::EcSlaveStatus`

## ecmcCppTrace.hpp

Current trace helper:

- `ecmcCpp::TriggeredTrace<T, Capacity>`

It provides:

- rolling pre-trigger history
- capture of pre-trigger, trigger, and post-trigger samples
- fixed-capacity waveform-style output arrays
- explicit arming and capture-ready state

## ecmcCppPersist.hpp

Current persistence helper:

- `ecmcCpp::RetainedValue<T>`

It provides:

- binary load/save of trivially copyable values
- explicit `restore()` and `store()` calls
- a simple retained-parameter pattern for startup/manual save actions
- a design intended for infrequent persistence, not per-cycle file I/O

## Examples

The main example families are:

- starter IOC project
- minimal scalar binding/export
- control/helper usage
- motion wrappers
- array/buffer bindings
- reusable triggered trace capture
- retained parameter/state handling
- triggered EL3702/EL1252-style scope capture

See the IOC-style examples in:

```text
examples/PSI/plugins/cpp_logic/
```

The best example for container and array bindings is the array-oriented
example. The best example for timers/triggers/filtering is the control example.
The best examples for the new helpers are the dedicated trace and retained
examples.

## Related Pages

- [C++ Logic]({{< relref "/manual/plugins/cpp_logic.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
