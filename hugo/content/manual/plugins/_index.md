+++
title = "plugins"
weight = 11
chapter = false
+++

## Scope
ECMC plugins extend the core ecmc runtime with domain-specific functionality.

Use this page when you need functionality that does not naturally belong in the
core axis, PLC, or data-storage configuration.

Most plugins are loaded with:
```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, "PLUGIN_ID=<id>,FILE=<lib>,CONFIG='<cfg>',REPORT=1"
```

For the common load/report/runtime model, see
[Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}).

The safety plugin is loaded with:
```bash
ecmcConfigOrDie "Cfg.LoadSafetyPlugin(<lib>,<cfg>)"
```

For the general script overview, see
[Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}}).

## Start here

- Use [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}) first for the common plugin API and runtime model.
- Use [C++ Logic]({{< relref "/manual/plugins/cpp_logic.md" >}}) for additive user-defined cyclic C/C++ logic loaded directly by `ecmc`.
- Use [C++ Logic Helpers]({{< relref "/manual/plugins/cpp_logic_helpers.md" >}}) for the helper headers (`ecmcCppLogic.hpp`, `ecmcCppMotion.hpp`, `ecmcCppControl.hpp`, `ecmcCppUtils.hpp`).
- Use [DAQ Plugin]({{< relref "/manual/plugins/daq.md" >}}) when your main question is synchronized acquisition rather than general plugin loading.
- Use [FFT Plugin]({{< relref "/manual/plugins/fft.md" >}}) for spectral analysis.
- Use [Motion Plugin]({{< relref "/manual/plugins/motion.md" >}}) for axis-focused commissioning capture.
- Use [Safety Plugin]({{< relref "/manual/plugins/safety.md" >}}) for the interface towards external safety logic.
- Use [SocketCAN Plugin]({{< relref "/manual/plugins/socketcan.md" >}}) for CAN/CANopen integration.
- Use [Grbl Plugin]({{< relref "/manual/plugins/grbl.md" >}}) for NC/G-code workflows.
- Use this page to decide which plugin family you need.
- Then use the chosen plugin package's own examples/scripts for its plugin-specific config keys and objects.

## Available plugin repositories
The list below is based on currently available `ecmc_plugin*` repositories.

| Plugin | Primary use | Typical entry points |
|---|---|---|
| `ecmc_plugin_daq` | Deterministic data acquisition buffers. Packages synchronized EtherCAT, motion, and other ecmc values into waveform arrays (supports oversampling data). | `startup.cmd`, `ecmcDAQAddArray.cmd`, `ecmcDAQAddChannel.cmd`, `ecmcDAQAddDataItem.cmd`, `ecmcDAQFinalizeArray.cmd` |
| `ecmc_plugin_fft` | FFT/spectral analysis of ecmc variables with minimal real-time impact (calculation in a worker thread). Supports continuous and triggered modes. | Load via `loadPlugin.cmd` with `libecmcPlugin_FFT.so` and `SOURCE=...` config |
| `ecmc_plugin_grbl` | CNC/G-code execution (Grbl-based) mapped to ecmc axes (`X/Y/Z` and spindle). Useful for NC-style motion programs on top of ecmc. | Load via `loadPlugin.cmd` with `libecmc_plugin_grbl.so`; configure `X_AXIS`, `Y_AXIS`, `Z_AXIS`, `SPINDLE_AXIS` |
| `ecmc_plugin_motion` | Commissioning/troubleshooting capture for motion axes. Samples and buffers motion signals and exposes waveform records for analysis tools. | `startup.cmd`, `addMotionObj.cmd` |
| `ecmc_plugin_safety` | Interface layer between ecmc and an external safety PLC/system (SS1-t style stop coordination, standstill feedback, optional velocity limiting). | `startup.cmd`, `addSS1Group.cmd`, `addAxisToSafetyGroup.cmd` |
| `ecmc_plugin_socketcan` | SocketCAN/CANopen integration for ecmc systems (master/device, SDO/PDO, heartbeat/sync utilities). | Load via `loadPlugin.cmd` with `libecmc_plugin_socketcan.so` and CAN interface config (`IF=can0`, etc.) |

## Selection guide
- Use `ecmc_plugin_daq` when you need synchronized multi-signal capture in the ecmc cycle.
- Use `ecmc_plugin_motion` when commissioning/tuning a specific axis and you want dedicated motion waveforms/tools.
- Use `ecmc_plugin_fft` for frequency-domain diagnostics (vibration, resonance, periodic disturbances).
- Use `ecmc_plugin_grbl` for NC/G-code driven workflows.
- Use `ecmc_plugin_socketcan` when CAN/CANopen devices must be integrated into the IOC.
- Use `ecmc_plugin_safety` only as a non-safety-rated interface towards certified external safety logic.

## Related pages
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [C++ Logic]({{< relref "/manual/plugins/cpp_logic.md" >}})
- [C++ Logic Helpers]({{< relref "/manual/plugins/cpp_logic_helpers.md" >}})
- [DAQ Plugin]({{< relref "/manual/plugins/daq.md" >}})
- [FFT Plugin]({{< relref "/manual/plugins/fft.md" >}})
- [Motion Plugin]({{< relref "/manual/plugins/motion.md" >}})
- [Safety Plugin]({{< relref "/manual/plugins/safety.md" >}})
- [SocketCAN Plugin]({{< relref "/manual/plugins/socketcan.md" >}})
- [Grbl Plugin]({{< relref "/manual/plugins/grbl.md" >}})
- [General configuration]({{< relref "/manual/general_cfg/_index.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
