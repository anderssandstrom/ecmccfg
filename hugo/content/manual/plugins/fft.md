+++
title = "FFT Plugin"
weight = 14
chapter = false
+++

## Scope
The FFT plugin performs spectral analysis of one runtime source with limited realtime impact.

Use it when:

- you want frequency-domain diagnostics
- you suspect resonance or periodic disturbance
- a scalar runtime value or waveform source should be analyzed continuously or on trigger

## Common Setup Pattern

The FFT plugin follows the normal plugin load model from [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}).

Example from the local test material:

```bash
epicsEnvSet(ECMC_PLUGIN_CONFIG,"SOURCE=plcs.plc0.static.sineval;DBG_PRINT=0;NFFT=1024;RATE=100;RM_DC=1;RM_LIN=1;APPLY_SCALE=1;MODE=TRIGG;")
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, "PLUGIN_ID=0,FILE=${ECMC_PLUGIN_FILNAME},CONFIG='${ECMC_PLUGIN_CONFIG}', REPORT=1"
dbLoadRecords(ecmcPluginFFT.template,"P=$(IOC):,INDEX=0,NELM=1024")
```

Verified config keys from repo examples and the plugin README include:

- `SOURCE`
- `DBG_PRINT`
- `NFFT`
- `RATE`
- `RM_DC`
- `RM_LIN`
- `APPLY_SCALE`
- `MODE`
- `ENABLE`
- `SCALE`
- `BREAKTABLE`

## Important Interface Detail

For the FFT plugin, `PLUGIN_ID` is not the same thing as the FFT object `INDEX`.

The local examples explicitly note that `INDEX` refers to the FFT object inside the plugin/template layer.

## Typical Sources

Examples in this repo use sources such as:

- `ax1.poserr`
- `ax1.actpos`
- `ecmc.thread.latency.max`
- `ec0.s11.mm.analogInputArray03`
- `plcs.plc0.static.sineval`

So the plugin can be used with motion, PLC, thread-diagnostic, and process-image style sources.

## Runtime EPICS Interface

The normal EPICS-facing interface is the plugin-provided template:

```bash
dbLoadRecords(ecmcPluginFFT.template,"P=$(IOC):,INDEX=0,NELM=1024")
```

This is the preferred path instead of building generic records manually.

The plugin README also verifies that each FFT object creates its own dedicated asyn port:

- `PLUGIN.FFT<index>`

This dedicated port is used so the FFT communication path does not reuse the main ecmc asyn port.

The template exposes at least:

- raw data array
- FFT amplitude array
- FFT x-axis / frequency array
- status
- mode
- sample rate

## PLC Interface

The plugin README also documents PLC control through plugin functions such as:

- `fft_enable(index,enable)`

So the FFT object can be armed or enabled either from EPICS or from PLC code.

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [DAQ Plugin]({{< relref "/manual/plugins/daq.md" >}})
- [Examples]({{< relref "/manual/examples.md" >}})
