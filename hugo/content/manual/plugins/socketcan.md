+++
title = "SocketCAN Plugin"
weight = 17
chapter = false
+++

## Scope
The SocketCAN plugin is used when CAN or CANopen devices must be integrated into an ecmc IOC.

Use it when:

- the system needs SocketCAN access
- CANopen SDO/PDO, heartbeat, or sync handling is needed
- the IOC should coordinate EtherCAT and CAN/CANopen related runtime behavior

## Common Interface

The SocketCAN plugin follows the normal [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}).

The plugin index already shows the typical load style:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, "PLUGIN_ID=0,FILE=${ECMC_PLUGIN_FILNAME},CONFIG='IF=can0;DBG_PRINT=0;',REPORT=1"
```

Verified config keys from the local docs/examples layer:

- `IF`
- `DBG_PRINT`
- `CONNECT`

## Current Documentation Scope

The plugin repo adds more verified interface detail:

- helper iocsh commands:
  - `ecmcCANOpenAddMaster`
  - `ecmcCANOpenAddDevice`
  - `ecmcCANOpenAddSDO`
  - `ecmcCANOpenAddPDO`
- plugin-provided EPICS templates:
  - `ecmcPluginSocketCAN_Dev.template`
  - `ecmcPluginSocketCAN_Com.template`
  - `ecmcPluginSocketCAN_SDO_input.template`
  - `ecmcPluginSocketCAN_SDO_output.template`
  - `ecmcPluginSocketCAN_SDO_error.template`
  - `ecmcPluginSocketCAN_PDO_input.template`
  - `ecmcPluginSocketCAN_PDO_output.template`
  - `ecmcPluginSocketCAN_PDO_error.template`

So this plugin is more than a raw CAN interface. It also exposes a small CANopen object model on top of SocketCAN.

This repo documents the common loading model and the intended use case, but it does not contain a full public best-practice startup example for the SocketCAN plugin itself.

So the detailed CANopen object model, runtime names, and helper scripts still belong to the plugin package.

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
