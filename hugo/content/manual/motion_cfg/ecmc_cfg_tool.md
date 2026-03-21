+++
title = "ecmc_cfg_tool"
weight = 24
chapter = false
+++

`ecmc_cfg_tool` is an external runtime tool repository for interacting with ecmc through the ecmc command parser.
It is useful when you need to inspect and adjust settings on a running system.

## What It Is Good For
- Reading status and configuration values from a running ecmc instance.
- Adjusting axis/drive/encoder related settings at runtime.
- Testing command-parser based changes before writing them into static startup/YAML configuration.

## Controller Tuning App
`ecmc_cfg_tool` includes a dedicated controller configurator app (`start_cntrl.sh`/`ecmc_cntrl_qt.py`).
It builds and uses a controller-focused command catalog and provides runtime read/write access to:
- PID core parameters (`Kp`, `Ki`, `Kd`, `Kff`)
- Inner-loop PID parameters and tolerance
- Deadband and deadband time
- Output and integral limits
- At-target monitor parameters
- Scaling numerator/denominator

## Motion App (`mtn`)
The motion app (`start_mtn.sh`/`ecmc_mtn_qt.py`) is a motor-record based runtime motion test UI.
It provides:
- Absolute/relative moves and jog control (forward/backward)
- A<->B sequence test with step count, idle time, and snake mode
- Drive enable/disable plus explicit `STOP`/`KILL` actions
- Compact runtime trend plots for position/setpoint/error

## Axis Config App (`axis`)
The axis app (`start_axis.sh`/`ecmc_axis_cfg.py`) is a YAML-oriented runtime configuration UI.
It loads an axis YAML template and maps keys to command-parser `Get`/`Set` commands for:
- Per-parameter read/write operations
- Bulk `Read All`, `Copy Read->Set`, and `Write Filled`
- Session change tracking and "Changed YAML" export view
- Optional YAML-to-command mapping overrides via `*.command_map.csv`

## Stream App (`stream`)
The stream app (`start.sh`/`ecmc_stream_qt.py`) is the generic command-parser frontend.
It provides:
- Direct `CMD`/`QRY` access for arbitrary ecmc command parser calls
- Catalog-based command browser with descriptions and runtime metadata
- Blocklist support to mark/hide blocked commands
- Multi-command editor panels for grouped command workflows

## How It Fits With `ecmccfg`
`ecmc_cfg_tool` complements `ecmccfg` by operating at runtime.
It does not replace static configuration files or IOC startup scripts.

Typical flow:
1. Start the IOC and load your normal configuration with `ecmccfg`/`loadYamlAxis.cmd`.
2. Use `ecmc_cfg_tool` to inspect and adjust settings through the ecmc command parser.
3. Persist useful runtime changes back into your YAML/startup configuration as needed.

## Runtime Still Uses `loadYamlAxis.cmd`
Initial axis configuration is still typically loaded through:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/ax1.yaml, DEV=${DEV}, DRV_SLAVE=4, ENC_SLAVE=3, ENC_CHANNEL=01"
```

## Notes
- Treat `ecmc_cfg_tool` runtime changes as temporary until reflected in versioned config files.
- At PSI, the tool can also be started from the generic `ecmcMain.ui` panel.
- Follow the `ecmc_cfg_tool` repository README for exact install/CLI usage, as that tool can evolve independently of `ecmccfg`.
