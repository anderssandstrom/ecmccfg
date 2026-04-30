+++
title = "Script Reference"
weight = 16
chapter = false
+++

## Scope
This page gives a practical overview of the scripts in `scripts/`.

It is not intended as a full replacement for the per-topic chapters.
Instead, it answers two questions:

1. Which scripts are normal user-facing entry points in startup files?
2. Which scripts are advanced building blocks or internal helpers?

## How To Read This Page

- Use the scripts in the `Primary startup commands` section as the normal public interface.
- Use the `Advanced commands` section when you need lower-level control than the usual YAML or component workflows provide.
- Treat the `Internal and helper scripts` section as implementation details unless you already know why you need them.

## Primary Startup Commands

These are the scripts most users should start from.

| Script | Purpose | Typical use |
| --- | --- | --- |
| `startup.cmd` | Initialize `ecmccfg`, set global macros, select mode and EtherCAT rate. | First step after `require ecmccfg`. |
| `addMaster.cmd` | Claim an EtherCAT master. | Explicit multi-master or custom startup setups. |
| `addSlave.cmd` | Add one slave and load default PVs/templates for it. | Standard EtherCAT hardware setup. |
| `addSlaveKL.cmd` | Add one KL-bus slave behind a BK coupler. | KL terminals. |
| `applyComponent.cmd` | Apply validated motor/encoder/drive component settings from `ecmccomp`. | Preferred hardware-specific configuration after `addSlave.cmd`. |
| `configureSlave.cmd` | Legacy combined slave-add plus config workflow. | Older classic setups. Prefer `addSlave.cmd` plus `applyComponent.cmd` for new configs. |
| `loadYamlAxis.cmd` | Load a physical or virtual axis from YAML. | Preferred axis configuration path. |
| `loadYamlEnc.cmd` | Load an encoder from YAML. | Additional encoder objects and encoder-only YAML workflows. |
| `loadYamlPlc.cmd` | Load a PLC from YAML or YAML header plus external PLC file. | Preferred structured PLC loading. |
| `loadPLCFile.cmd` | Load a classic PLC text file. | Standard text PLC workflow. |
| `loadPLCLib.cmd` | Load a reusable PLC function library into a PLC. | Shared PLC functions and includes. |
| `addPlcVarAnalog.cmd` | Link one PLC numeric variable to an EPICS `ao` named `DEV:NAME`. | Simple EPICS exposure of `static` or `global` PLC variables. |
| `addPlcVarBinary.cmd` | Link one PLC boolean variable to an EPICS `bo` named `DEV:NAME`. | Simple EPICS exposure of `static` or `global` PLC variables. |
| `addAsynVarAnalog.cmd` | Link one asyn variable to an EPICS `ao` named `DEV:NAME`. | Simple EPICS exposure of plugin or other runtime asyn values. |
| `addAsynVarBinary.cmd` | Link one asyn variable to an EPICS `bo` named `DEV:NAME`. | Simple EPICS exposure of plugin or other runtime asyn values. |
| `loadCppLogic.cmd` | Load one additive C++ logic module and optionally its built-in/custom PVs. | User-defined cyclic C/C++ logic with dedicated asyn interface. |
| `configureAxis.cmd` | Legacy classic axis configuration from `.ax`/`.pax` style files. | Older classic axis setups. |
| `configureVirtualAxis.cmd` | Legacy classic virtual-axis configuration. | Older classic virtual-axis setups. |
| `applyAxisSynchronization.cmd` | Attach synchronization logic to the most recently configured axis. | Classic synchronization setups. |
| `addDataStorage.cmd` | Create a data-storage buffer and its PVs. | Buffered waveform/data capture workflows. |
| `loadPlugin.cmd` | Load an ecmc plugin shared library. | FFT, motion capture, DAQ, safety, SocketCAN, Grbl, and related plugin workflows. |
| `setAppMode.cmd` | Switch to operational mode and start the realtime thread. | Normal transition to running IOC. |
| `finalize.cmd` | Convenience wrapper that applies config if needed, loads some summary objects, and sets app mode. | Compact startup files that want the default finishing sequence. |

For a generated list of available `HW_DESC` values together with product IDs and
hardware snippet paths, see [Supported Slaves]({{< relref "/manual/general_cfg/supported_slaves.md" >}}).

## Advanced Commands

These commands are real user-facing interfaces, but they are lower level or more specialized.

### EtherCAT / Process Image

| Script | Purpose |
| --- | --- |
| `applyConfig.cmd` | Apply the EtherCAT configuration and calculate process-image offsets. |
| `addDomain.cmd` | Create an additional EtherCAT domain with custom execution rate/offset. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |
| `addEcDataItem.cmd` | Expose a custom pointer into already configured process-image data as an EPICS-accessible item. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |
| `addEcSdoRT.cmd` | Add runtime asynchronous SDO access objects and EPICS control/readback records. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |
| `applySlaveConfig.cmd` | Apply one legacy slave-specific config file after `addSlave.cmd`. |
| `applySlaveDCconfig.cmd` | Apply distributed-clock settings to a slave. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |
| `slaveVerify.cmd` | Verify slave identity and optionally reset/read firmware. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |
| `ignoreSlaves.cmd` | Skip one or more slave positions in the topology. See [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}}). |

### Motion / Encoders / Synchronization

| Script | Purpose |
| --- | --- |
| `addAxis.cmd` | Low-level axis object and PV creation after a classic config file has populated the environment. |
| `addVirtualAxis.cmd` | Low-level virtual-axis object and PV creation. |
| `addEncoder.cmd` | Add an extra encoder to the most recently configured axis in classic setups. |
| `addMasterSlaveSM.cmd` | Create a master/slave state machine object and its PVs. See [Master/Slave State Machine]({{< relref "/manual/general_cfg/master_slave_state_machine.md" >}}). |
| `loadAxisPLCFile.cmd` | Load an axis PLC file tied to a specific axis id. |
| `loadLUTFile.cmd` | Load a lookup table into ecmc, for example for corrections or PLC use. See [Lookup Tables]({{< relref "/manual/general_cfg/lut.md" >}}). |
| `pvtControllerConfig.cmd` | Configure the profile-move/PVT controller records and trigger handling. |

### IOC / Record Behavior

| Script | Purpose |
| --- | --- |
| `setDiagnostics.cmd` | Set default EtherCAT diagnostics and printout behavior. |
| `setRecordUpdateRate.cmd` | Change the update rate for records loaded after this call. |
| `restoreRecordUpdateRate.cmd` | Restore the default update rate from startup. |
| `setProcHook.cmd` | Configure the `<P>:MCU-Updated` processing hook and hook sample time. |

## Internal And Helper Scripts

These scripts exist for implementation support, conversions, or developer workflows.
They are generally not the first thing to call directly from a normal IOC startup file.

### Utility Scripts In `utils/`

These are repository utilities rather than IOC startup scripts:

- legacy EtherCAT ESI parser for extracting PDO mappings and generating draft
  ecmc hardware snippets. See
  [ESI Parser]({{< relref "/manual/general_cfg/esi_parser.md" >}}).
- `utils/esi_mapping_browser.py`: newer interactive/browser-oriented ESI mapping
  inspection and snippet generation tool.

### Template / Substitution Helpers

- `applySubstitutions.cmd`
- `applyTemplate.cmd`
- `loadSubstAxes.cmd`
- `loadSubstConfig.cmd`
- `loadSubstHw.cmd`
- `loadCompleteCfgSubst.sh`
- `loadCompleteCfgSubst.awk`

### PLC Conversion Helpers

- `appendCodeToPlc.sh`
- `convertPlcFileToAppend.sh`

### Multi-Object Generation Helpers

- `multiAxis.sh`
- `multiAxis.awk`
- `multiHw.sh`
- `finalizeAxGrp_loopStep.cmd`

### Backend / YAML Loader Implementation

The files under `scripts/jinja2/` are backend tooling used by the YAML loaders.
Typical users normally call:

- `loadYamlAxis.cmd`
- `loadYamlEnc.cmd`
- `loadYamlPlc.cmd`

and do not call the Python helpers directly.

### EC Tool Helpers

These are troubleshooting or commissioning utilities rather than normal IOC startup commands:

- `ecToolEthercatMaster.sh`
- `ecToolEthercatSlaves.sh`
- `ecToolReadHwDiag.sh`
- `ecToolEL7062_readBackParams.sh`
- `ecToolEL7062_triggTune.sh`

### Miscellaneous

- `empty.cmd`: do-nothing placeholder used in some macro-driven flows.

## Recommended Usage Pattern

For new configurations, the normal order is:

1. `startup.cmd`
2. `addSlave.cmd` and `applyComponent.cmd`
3. `loadYamlAxis.cmd` / `loadYamlEnc.cmd` / `loadYamlPlc.cmd`
4. `addDataStorage.cmd` and `loadPlugin.cmd` if needed
5. `loadCppLogic.cmd` if user-defined C++ logic is part of the IOC
6. `setAppMode.cmd` or `finalize.cmd`

For older classic configurations, `configureAxis.cmd`, `configureVirtualAxis.cmd`,
`configureSlave.cmd`, and `applyAxisSynchronization.cmd` are still valid, but they
should generally be seen as legacy entry points compared to the YAML-first path.

## Related Pages

- [startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}})
- [PV Processing Rate]({{< relref "/manual/general_cfg/PVProcessingRate.md" >}})
- [iocsh utilities]({{< relref "/manual/general_cfg/iocsh_utils.md" >}})
- [ESI Parser]({{< relref "/manual/general_cfg/esi_parser.md" >}})
- [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}})
- [Axis Groups]({{< relref "/manual/general_cfg/axis_groups.md" >}})
- [Master/Slave State Machine]({{< relref "/manual/general_cfg/master_slave_state_machine.md" >}})
- [Lookup Tables]({{< relref "/manual/general_cfg/lut.md" >}})
- [motion configuration]({{< relref "/manual/motion_cfg/_index.md" >}})
- [PLC configuration]({{< relref "/manual/PLC_cfg/_index.md" >}})
- [plugins]({{< relref "/manual/plugins/_index.md" >}})
