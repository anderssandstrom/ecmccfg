+++
title = "Plugin Interface"
weight = 12
chapter = false
+++

## Scope
This page describes the common interface that all ecmc plugins use.

That interface has two parts:

- a common load/report/overview interface provided by ecmc/ecmccfg
- a plugin-specific runtime interface defined by each plugin

This distinction is important: plugin loading is standardized, but the actual runtime names, functions, records, and configuration keys are usually plugin-specific.

## Common Startup Interface

The normal startup entry point is:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, \
  "PLUGIN_ID=0,FILE=/path/to/libecmc_plugin_xxx.so,CONFIG='KEY=VALUE;KEY2=VALUE2;',REPORT=1"
```

Main arguments:

- `PLUGIN_ID`: numeric plugin object id
- `FILE`: shared library to load
- `CONFIG`: plugin-specific configuration string
- `REPORT`: if `1`, call `Cfg.ReportPlugin(...)` after load

The underlying command-parser calls are:

```text
Cfg.LoadPlugin(<id>,<file>)
Cfg.LoadPlugin(<id>,<file>,<config>)
Cfg.ReportPlugin(<id>)
```

The safety plugin is a special case and is loaded with:

```text
Cfg.LoadSafetyPlugin(<file>,<config>)
```

## Configuration String

`CONFIG` is passed directly to the plugin constructor.

Important points:

- the key names are defined by the plugin, not by ecmccfg
- the exact syntax is plugin-specific, but many plugins use a `KEY=VALUE;...` style string
- this means the manual can describe the common wrapper, but the valid config keys must still come from the plugin itself or from its examples

Examples:

```bash
CONFIG='DBG_PRINT=1;'
CONFIG='SOURCE=ec0.s11.mm.analogInputArray01;ELEMENTS=1024;'
CONFIG='IF=can0;DBG_PRINT=0;'
```

## Common IOC-Level Summary Interface

After plugins are loaded, the IOC exposes common summary information:

- `$(IOC):MCU-Cfg-PLG-Cnt` for the plugin count
- `$(IOC):MCU-Cfg-PLG-FrstObjId` for the first plugin object id

These PVs are mainly used by overview panels and configuration summaries.

## Common Runtime Interface Patterns

The runtime interface is not identical across plugins, but most plugins expose one or more of these surfaces:

### Asyn variables

Some plugins expose runtime values through the normal ecmc asyn port.

Those values can then be mapped to EPICS records with generic db templates.

Example:

```bash
dbLoadRecords("ecmcGenericAnalog.db", \
  "REC_NAME=$(IOC):Plugin-Adv-Counter,PORT=MC_CPU1,ASYN_NAME=plugin.adv.counter,TSE=0,T_SMP_MS=100")
```

Here:

- `PORT` is the normal ecmc asyn port
- `ASYN_NAME` is the plugin-defined runtime variable name
- the `plugin.adv.counter` namespace is defined by that specific plugin

### Plugin-specific db templates

Some plugins ship their own record templates instead of relying only on generic analog/binary templates.

Example:

```bash
dbLoadRecords(ecmcPluginFFT.template,"P=$(IOC):,INDEX=0,NELM=4096")
```

This is common when a plugin has a richer object model, such as FFT spectra, trigger control, or waveform readback.

### PLC functions and constants

Some plugins also register extra PLC functions and constants.

Examples from plugin test material:

```text
adv_plugin_func_1(...)
adv_plugin_func_2(...)
adv_CONST_1
rpi_digitalWrite(...)
rpi_digitalRead(...)
rpi_OUTPUT
```

These names become available in PLC code after the plugin has been loaded.

Use this when plugin functionality should be driven directly from PLC logic.

### Standalone helper scripts

Some plugin packages provide their own helper scripts, for example DAQ or safety setup scripts.

In those cases, the common pattern is:

1. load the plugin itself
2. call the plugin package's own object-creation scripts

## What Is Standardized vs Plugin-Specific

### Standardized

- `loadPlugin.cmd`
- `Cfg.LoadPlugin(...)`
- `Cfg.ReportPlugin(...)`
- `PLUGIN_ID`
- the existence of a plugin config string
- IOC-level plugin summary/count information

### Plugin-specific

- valid `CONFIG` keys
- runtime variable names such as `plugin.adv.counter`
- plugin-provided EPICS templates
- PLC functions/constants added by the plugin
- helper scripts shipped by the plugin package

## Recommended Usage Pattern

1. Load the plugin with `loadPlugin.cmd`.
2. Use `REPORT=1` while commissioning so the plugin reports its object/config details.
3. Expose plugin data either with plugin templates or with generic `ecmcGeneric*.db` records.
4. If the plugin adds PLC functions, keep the PLC code explicit about those plugin dependencies.
5. Treat plugin runtime names as plugin API, not as generic ecmccfg names.

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
- [PLC syntax]({{< relref "/manual/PLC_cfg/syntax.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
