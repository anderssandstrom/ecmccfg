+++
title = "general"
weight = 7
chapter = false
+++

## Topics
{{% children %}}
---

## Scope
General configuration covers IOC/bootstrap behavior that is not axis-specific:
- startup mode and global macros
- record update/processing behavior
- iocsh utility functions
- common data buffering patterns
- command-parser reference access

## By Task
### Start and parameterize ecmccfg
- [startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}}) for startup arguments/macros and initialization behavior.
- [modes]({{< relref "/manual/general_cfg/startup/modes.md" >}}) for `FULL`, `DAQ`, `NO_MR`, and `ENG_MODE`.

### Configure EPICS record processing/update rate
- [PV Processing Rate]({{< relref "/manual/general_cfg/PVProcessingRate.md" >}}) for `ECMC_SAMPLE_RATE_MS`, per-record overrides, and processing hooks.

### Use utility functions in startup scripts
- [iocsh utilities]({{< relref "/manual/general_cfg/iocsh_utils.md" >}}) for `ecmcEpicsEnvSetCalc`, `ecmcIf`, loops, and file existence checks.
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}}) for which `scripts/` entry points are public, advanced, or internal helpers.

### Configure generic data capture/buffering
- [data storage buffer]({{< relref "/manual/general_cfg/data_storage.md" >}}) for `ds_append_data`/`ds_push_asyn` usage patterns.

### Apply platform-level recommendations
- [best practice]({{< relref "/manual/general_cfg/best_practice.md" >}}) for EtherCAT rate and host-side setup guidance.

### Browse command API details
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}}) for command syntax by domain.

## Recommended Reading Paths
### New IOC bootstrap/config path
1. [startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}})
2. [modes]({{< relref "/manual/general_cfg/startup/modes.md" >}})
3. [PV Processing Rate]({{< relref "/manual/general_cfg/PVProcessingRate.md" >}})
4. [best practice]({{< relref "/manual/general_cfg/best_practice.md" >}})

### Script authoring / automation path
1. [iocsh utilities]({{< relref "/manual/general_cfg/iocsh_utils.md" >}})
2. [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
3. [data storage buffer]({{< relref "/manual/general_cfg/data_storage.md" >}})
4. [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
