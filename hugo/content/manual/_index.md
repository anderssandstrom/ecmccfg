+++
title = "Manual"
weight = 1
chapter = true
+++

# ecmccfg

A configuration framework for ECMC Motion Control Module for EPICS.

## Start here

1. Follow the [Quickstart]({{< relref "/manual/quickstart.md" >}}) to bring up one axis using YAML.
2. Read the [Introduction]({{< relref "/manual/introduction.md" >}}) for the IOC startup structure.
3. Use the [motion commissioning path]({{< relref "/manual/motion_cfg/_index.md" >}}) for axis configuration, scaling, direction, homing, motor-record behavior, and autosave.
4. Check the system through the [overview panel]({{< relref "/manual/knowledgebase/panel.md" >}}) and use [Troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}}) when behavior differs from expectations.

For terminology such as `axis`, `axis PLC`, `component`, `plugin`, and
`master-less`, see [Terminology]({{< relref "/manual/terminology.md" >}}).

<!-- Preserve links to the former overview headings. -->
<a id="common-tasks"></a>
<a id="main-sections"></a>
<a id="topics"></a>

## Choose the material you need

| Need | Start with |
| --- | --- |
| A working configuration to adapt | [Examples]({{< relref "/manual/examples.md" >}}) and [Best practice]({{< relref "/manual/best_practice.md" >}}) |
| IOC startup or hardware-free operation (`MASTER_ID=-1`) | [Startup and IOC configuration]({{< relref "/manual/general_cfg/startup/_index.md" >}}) |
| EtherCAT setup and commissioning | [EtherCAT and commissioning]({{< relref "/manual/general_cfg/ethercat/_index.md" >}}) |
| Axis configuration and motion behavior | [Motion]({{< relref "/manual/motion_cfg/_index.md" >}}) |
| PLC logic and EPICS variable exposure | [PLC configuration]({{< relref "/manual/plc_cfg/_index.md" >}}) and [PLC best practice]({{< relref "/manual/plc_cfg/best_practice.md" >}}) |
| Plugins | [Plugins]({{< relref "/manual/plugins/_index.md" >}}) |
| Buffered data, utilities, or command lookup | [Utilities and reference]({{< relref "/manual/general_cfg/utilities/_index.md" >}}) |
| Runtime problems or device-specific notes | [Knowledge base]({{< relref "/manual/knowledgebase/_index.md" >}}) |

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

## Maintenance

Use [Upgrades]({{< relref "/manual/upgrades.md" >}}) for migration checklists and breaking changes.
