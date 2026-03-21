+++
title = "motion"
weight = 8
chapter = false
+++

## How to use this section

Start here if you want to configure axes, synchronization, homing, motor record
behavior, or motion-related PLC logic.

If you want the preferred meaning of terms such as `axis`, `axis PLC`, and
`legacy motion`, see [Terminology]({{< relref "/manual/terminology.md" >}}).

For new configurations, the preferred path is YAML-based:

1. configure slaves with `addSlave.cmd` and `applyComponent.cmd`
2. load axes with `loadYamlAxis.cmd`
3. load PLC logic with `loadYamlPlc.cmd` or `loadPLCFile.cmd`

If you are maintaining an older IOC based on `.ax`, `.vax`, and `.sax` files,
go directly to [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}}).

## Common tasks

- I want to bring up a new axis:
  [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- I want example-driven guidance:
  [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
- I need scaling, direction, or homing:
  [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}}),
  [direction]({{< relref "/manual/motion_cfg/direction.md" >}}),
  [homing]({{< relref "/manual/motion_cfg/homing.md" >}})
- I need synchronization or axis-local PLC logic:
  [axis PLC]({{< relref "/manual/motion_cfg/axisPLC.md" >}})
- I need motor record behavior or PVT/profile moves:
  [motor record]({{< relref "/manual/motion_cfg/motor.md" >}}),
  [PVT]({{< relref "/manual/motion_cfg/pvt.md" >}})
- I need runtime tuning or investigation:
  [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}})
- I need older classic motion docs:
  [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}})

## Recommended reading paths

### New axis bring-up

1. [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
2. [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
3. [drive modes CSV, CSP, CSP-PC]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}})
4. [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}})
5. [direction]({{< relref "/manual/motion_cfg/direction.md" >}})
6. [homing]({{< relref "/manual/motion_cfg/homing.md" >}})
7. [motor record]({{< relref "/manual/motion_cfg/motor.md" >}}) if the EPICS motor record is used

### Synchronization and axis logic

1. [axis PLC]({{< relref "/manual/motion_cfg/axisPLC.md" >}})
2. [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
3. [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})

### Existing IOC with classic motion files

1. [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}})
2. [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}})
3. [direction]({{< relref "/manual/motion_cfg/direction.md" >}})
4. [homing]({{< relref "/manual/motion_cfg/homing.md" >}})
5. [motion knowledge base]({{< relref "/manual/knowledgebase/motion.md" >}})

### Runtime tuning and diagnostics

1. [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}})
2. [motion knowledge base]({{< relref "/manual/knowledgebase/motion.md" >}})
3. [tuning knowledge base]({{< relref "/manual/knowledgebase/tuning.md" >}})

## Key references

- [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [axis YAML settings table]({{< relref "/manual/motion_cfg/axisYamlSettingsTable.md" >}})
- [axis YAML settings (heading view)]({{< relref "/manual/motion_cfg/axisYamlSettingsHeadings.md" >}})
- [drive modes CSV, CSP, CSP-PC]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}})
- [PVT]({{< relref "/manual/motion_cfg/pvt.md" >}})
- [ecmccomp]({{< relref "/manual/motion_cfg/ecmccomp.md" >}})
- [ecb]({{< relref "/manual/motion_cfg/ecb.md" >}})

## Topics
{{% children %}}
