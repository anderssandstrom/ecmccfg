+++
title = "plugins"
weight = 11
chapter = false
+++

## Scope
ECMC plugins extend the core ecmc runtime with domain-specific functionality.

Most plugins are loaded with:
```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, "PLUGIN_ID=<id>,FILE=<lib>,CONFIG='<cfg>',REPORT=1"
```

The safety plugin is loaded with:
```iocsh
ecmcConfigOrDie "Cfg.LoadSafetyPlugin(<lib>,<cfg>)"
```

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
