# Native Logic C++ Examples

This directory mirrors the additive native C/C++ logic examples from `ecmc` so
that they are easy to discover from the PSI `ecmccfg` example tree.

Examples:

- [`examples/native_logic_minimal`](./examples/native_logic_minimal/): minimal native logic example using `ecmcNative::LogicBase`
- [`examples/native_logic_control`](./examples/native_logic_control/): control example using `ecmcNative::Pid`, `RateLimiter`, and `HysteresisBool`
- [`examples/native_logic_motion`](./examples/native_logic_motion/): motion example using the native `MC_*` style wrappers
- [`examples/native_logic_scope`](./examples/native_logic_scope/): EL3702/EL1252 scope example with buffered trigger-aligned capture

Helper script:

- [`utils/ecmcNativeLogicSubstGen.py`](./utils/ecmcNativeLogicSubstGen.py): offline substitutions generator for native logic `epics` exports

Notes:

- The native logic headers live in the `ecmc` repository under `devEcmcSup/logic/`.
- These files are mirrored here for example discovery and IOC-side workflow discussions.
- A native logic loader is not implemented in `ecmc` yet, so these examples are source examples rather than complete runnable IOC examples today.
- The substitutions generator can emit custom record substitutions for exported variables from a compiled native logic `.so`, but there is not yet a standard built-in core substitutions file for native logic.
