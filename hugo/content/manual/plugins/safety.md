+++
title = "Safety Plugin"
weight = 16
chapter = false
+++

## Scope
The safety plugin is the interface layer between ecmc and an external safety system.

Use it when:

- an external safety PLC/system coordinates SS1-t style stop handling
- ecmc should provide standstill or velocity-related feedback into that safety flow
- normal motion logic must react to external safety commands

This plugin is not the safety function itself. It is only the interface towards the external certified safety chain.

## Loading Model

The safety plugin is a special case and uses `Cfg.LoadSafetyPlugin(...)` rather than the normal `Cfg.LoadPlugin(...)` wrapper.

In practice, local examples use the plugin package directly:

```bash
require ecmc_plugin_safety
```

Then the plugin package helper scripts are used to create safety objects.

## Helper Scripts Seen In This Repo

The local startup material uses:

- `addSS1Group.cmd`
- `addAxisToSafetyGroup.cmd`

Example:

```bash
${SCRIPTEXEC} ${ecmc_plugin_safety_DIR}addSS1Group.cmd "NAME=first,EC_RAMP_DOWN_CMD=${EC_RAMP_DOWN_CMD},EC_AXES_AT_REST_STAT=${EC_AXES_AT_REST_STAT},EC_AXES_LIM_VELO_CMD=${EC_AXES_LIM_VELO_CMD=empty},DELAY_MS=${SAFETY_TIMEOUT}"
${SCRIPTEXEC} ${ecmc_plugin_safety_DIR}addAxisToSafetyGroup.cmd "NAME=first,AX_ID=1,VELO_REST_LIM=1,VELO_MAX_LIM=100"
```

Verified helper-script parameters from local examples include:

- group/object name
- EtherCAT entries for ramp-down and standstill/velocity status
- delay time
- axis id
- standstill velocity limit
- maximum velocity limit

The plugin repo confirms the underlying command model:

- `ecmcAddSS1SafetyGroup(...)`
- `ecmcAddAxisToSafetyGroup(...)`

And the helper scripts load the plugin templates:

- `ecmcSS1Group.template`
- `ecmcSS1Axis.template`

The plugin package also contains:

- `ecmcSS1Main.template`

## When To Use It

Use the safety plugin when safety-related commands and feedback must cross the boundary between:

- external safety logic
- ecmc runtime state
- axis-level motion behavior

Do not describe it as a safety-certified function by itself.

The plugin README also clarifies two important behaviors:

- the interface is centered around three binary EtherCAT signals:
  - ramp-down command into ecmc
  - standstill status back to the safety system
  - optional velocity-limitation command into ecmc
- standstill evaluation uses the trajectory-generated velocity, not the measured actual velocity

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [knowledgebase: motion]({{< relref "/manual/knowledgebase/motion.md" >}})
