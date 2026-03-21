+++
title = "manual"
weight = 1
chapter = true
+++

# ecmccfg

A configuration framework for ECMC Motion Control Module for EPICS.

## Start here

Use this manual as follows:

1. Start with [Quickstart](./quickstart/) if you want to bring up one axis with the current YAML-based workflow.
2. Go to [Examples](./examples/) if you want a reusable starting point from `examples/PSI/best_practice/`.
3. Go directly to the section below if you already know what you want to configure.

## Common tasks

- I want to configure one or more axes:
  [motion configuration](./motion_cfg/) and
  [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
- I want to load PLC logic:
  [PLC configuration]({{< relref "/manual/PLC_cfg/_index.md" >}})
- I want to expose PLC variables as EPICS PVs:
  [PLC best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}})
- I want to run without EtherCAT hardware:
  [startup]({{< relref "/manual/general_cfg/startup/_index.md" >}})
  and the `MASTER_ID=-1` section
- I want to capture buffered data or use data storage:
  [data storage]({{< relref "/manual/general_cfg/data_storage.md" >}})
- I want to load plugins:
  [plugins](./plugins/)
- I want a ready-made example:
  [examples](./examples/)
- I need troubleshooting or hardware notes:
  [knowledge base](./knowledgebase/)

## Recommended workflow

For new configurations, the normal path is:

1. `require ecmccfg`
2. add slaves with `addSlave.cmd`
3. apply hardware-specific setup with `applyComponent.cmd`
4. load axes with `loadYamlAxis.cmd`
5. load PLCs with `loadYamlPlc.cmd` or `loadPLCFile.cmd`
6. add optional features such as data storage or plugins
7. switch to runtime with `setAppMode.cmd` or `finalize.cmd`

Minimal startup skeleton:

```bash
require ecmccfg <VERSION>

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL7062"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000, I_STDBY_MA=100, U_NOM_MV=24000, R_COIL_MOHM=1230,L_COIL_UH=500'"

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/ax1.yaml, ECMC_TMPDIR=/tmp/"
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "FILE=./cfg/main.plc, SAMPLE_RATE_MS=100"
```

For the detailed step-by-step breakdown of the startup structure, see
[introduction](./introduction/).

## Preferred entry points

- `loadYamlAxis.cmd`: preferred axis configuration path
- `loadYamlPlc.cmd`: preferred structured PLC path
- `loadPLCFile.cmd`: classic PLC-file path
- `applyComponent.cmd`: preferred drive and encoder component setup
- `configureAxis.cmd`, `configureVirtualAxis.cmd`, and `applyAxisSynchronization.cmd`:
  still supported, but mainly legacy compared to the YAML-first flow

## Main sections

- [Quickstart](./quickstart/) for a minimal single-axis bring-up
- [Introduction](./introduction/) for the detailed IOC startup structure
- [Motion configuration](./motion_cfg/) for scaling, direction, homing, synchronization, and YAML axis details
- [PLC configuration]({{< relref "/manual/PLC_cfg/_index.md" >}}) for syntax, variables, patterns, functions, and best practices
- [General configuration]({{< relref "/manual/general_cfg/_index.md" >}}) for startup, scripts, data storage, and utilities
- [Plugins](./plugins/) for available ecmc plugins and when to use them
- [Examples](./examples/) for ready-to-adapt scenarios and scripts
- [Knowledge base](./knowledgebase/) for troubleshooting, hardware notes, and diagnostics
- [Upgrades](./upgrades/) for migration checklists and breaking changes

## Topics
{{% children %}}
