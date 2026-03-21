+++
title = "Motion Plugin"
weight = 15
chapter = false
+++

## Scope
The motion plugin is intended for commissioning and troubleshooting of motion axes.

Use it when:

- you want buffered motion-related waveforms for one axis
- you are tuning or diagnosing a specific axis
- the standard scalar PVs are not enough for the analysis

## Setup Pattern Seen In This Repo

The local examples typically load the plugin package directly with `require`:

```bash
epicsEnvSet(ECMC_PLUGIN_CONFIG,"PLUGIN_ID=1,AX=1,BUFF_SIZE=2000,DBG=0,ENA=1")
require ecmc_plugin_motion "${ECMC_PLUGIN_CONFIG}"
```

Verified config keys from local examples:

- `PLUGIN_ID`
- `AX` / `AXIS`
- `BUFF_SIZE` / `BUFFER_SIZE`
- `DBG` / `DBG_PRINT`
- `ENA` / `ENABLE`

The local plugin repo confirms a dedicated helper script:

- `addMotionObj.cmd`

That helper script:

- loads `libecmc_plugin_motion.so`
- builds the plugin config string
- calls `loadPlugin.cmd`
- loads `ecmcPluginMotion.template`

It also tracks a separate motion-object index:

- `ECMC_PLG_MOTION_OBJ_INDEX`

That index is not the same thing as `PLUGIN_ID`.

## Practical Meaning

Compared to the general [DAQ Plugin]({{< relref "/manual/plugins/daq.md" >}}), the motion plugin is more axis-focused.

Choose it when the task is:

- inspect one motion axis in detail
- capture axis behavior during tuning or troubleshooting

Choose DAQ instead when the task is:

- synchronized acquisition of many different channels
- richer multi-signal acquisition objects

## Notes

This repo contains load examples, but not a full public best-practice example tree for the motion plugin itself.

The plugin README verifies the intended runtime role clearly:

- motion data are sampled
- motion data are buffered
- the buffered data are exposed to EPICS as waveforms

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [DAQ Plugin]({{< relref "/manual/plugins/daq.md" >}})
- [knowledgebase: tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
