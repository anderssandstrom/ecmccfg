+++
title = "DAQ Plugin"
weight = 13
chapter = false
+++

## Scope
The DAQ plugin is used for deterministic, synchronized acquisition of runtime values into array buffers.

Use it when:

- several signals must be captured together in the ecmc cycle
- oversampling data should be packaged into arrays
- post-processing or external analysis needs synchronized snapshots instead of one scalar PV at a time

## Interface Model

The DAQ plugin follows the normal plugin load model described in [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}).

In practice, DAQ setups usually have two layers:

1. load the DAQ plugin package
2. create DAQ arrays/channels/items with the plugin package's own helper scripts

Typical helper entry points are:

- `ecmcDAQAddArray.cmd`
- `ecmcDAQAddChannel.cmd`
- `ecmcDAQAddDataItem.cmd`
- `ecmcDAQFinalizeArray.cmd`

These helpers belong to the DAQ plugin package rather than to core `ecmccfg`.

The plugin README and helper scripts verify the following object model:

- `Array`: top-level acquisition object
- `Channel`: logical sub-block inside one array
- `DataItem`: one runtime source inside one channel

The first elements of the final waveform contain a header describing channel count, EtherCAT time, and per-channel metadata.

## Verified Startup Pattern

The plugin README uses this load style:

```bash
require ecmc_plugin_daq sandst_a "PLUGIN_ID=0"
```

Then the helper scripts build the DAQ object tree:

```bash
${SCRIPTEXEC} ${ecmc_plugin_daq_DIR}ecmcDAQAddArray.cmd "NAME=TestArray01"
${SCRIPTEXEC} ${ecmc_plugin_daq_DIR}ecmcDAQAddChannel.cmd "TYPE=1234,NAME=TestArray01"
${SCRIPTEXEC} ${ecmc_plugin_daq_DIR}ecmcDAQAddDataItem.cmd "PARAM=ax1.setpos,NAME=TestArray01"
${SCRIPTEXEC} ${ecmc_plugin_daq_DIR}ecmcDAQFinalizeArray.cmd "NAME=TestArray01"
```

Verified helper-script parameters:

- `ecmcDAQAddArray.cmd`
  - `NAME`
- `ecmcDAQAddChannel.cmd`
  - `TYPE`
  - `NAME`
  - `DESC`
- `ecmcDAQAddDataItem.cmd`
  - `PARAM`
  - `FORMAT`
  - `SEND_OLD`
  - `NAME`
- `ecmcDAQFinalizeArray.cmd`
  - `NAME`
  - `DATA_FLNK`

Verified `FORMAT` values:

- `0`: raw
- `1`: time in microseconds
- `2`: time in microseconds minus one period
- `3`: time in nanoseconds minus one period

The helper scripts also verify the asyn naming model:

- DAQ port name: `ECMC.PLUGIN.DAQ.<NAME>`

And the finalizer loads:

- `ecmcPluginDAQ.template`
- `ecmcPluginDAQ_chX.template`
- `ecmcPluginDAQ_chX-itmX.template`

## When To Choose DAQ Instead Of Data Storage

Prefer the DAQ plugin when:

- many values must be captured as one synchronized acquisition object
- oversampling data is involved
- waveform-style output is the natural result

Prefer core [data storage]({{< relref "/manual/general_cfg/data_storage.md" >}}) when:

- one PLC or one small workflow appends scalar values over time
- the capture logic is simple
- you do not need the DAQ plugin's richer acquisition object model

## Typical Setup Pattern

The normal setup flow is:

1. install/require the DAQ plugin package
2. load the DAQ plugin
3. create one or more DAQ arrays
4. add channels or data items to those arrays
5. finalize the array configuration
6. use the resulting plugin-specific PVs/templates for runtime acquisition

The normal waveform record loaded by the finalizer is:

- `$(IOC):DAQ-<NAME>-DataAct`

## Design Guidance

Use the DAQ plugin for acquisition structure and synchronization, not as a replacement for:

- normal scalar status PVs
- small PLC-local buffering
- one-off debug values

For those simpler cases, normal EPICS records or [data storage]({{< relref "/manual/general_cfg/data_storage.md" >}}) are usually easier.

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [data storage]({{< relref "/manual/general_cfg/data_storage.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
