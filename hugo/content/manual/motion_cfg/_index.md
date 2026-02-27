+++
title = "motion"
weight = 8
chapter = false
+++


## Topics
{{% children %}}
---

## Scope
ECMC motion covers two axis classes:
1. Physical axes (joints, hardware-coupled)
2. Virtual axes (end effectors)

## By Task
### Configure a motion axis (startup/static config)
- [YAML config]({{< relref "/manual/motion_cfg/axisYaml.md" >}}) for full axis definition.
- [Axis YAML settings table]({{< relref "/manual/motion_cfg/axisYamlSettingsTable.md" >}}) for fast key lookup.
- [Axis YAML settings (heading view)]({{< relref "/manual/motion_cfg/axisYamlSettingsHeadings.md" >}}) for grouped key overview.
- [Drive modes CSV, CSP, CSP-PC]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}}) for mode selection.
- [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}}), [direction]({{< relref "/manual/motion_cfg/direction.md" >}}), and [homing]({{< relref "/manual/motion_cfg/homing.md" >}}) for core behavior.

### Configure synchronization and logic around axes
- [PLC YAML config]({{< relref "/manual/motion_cfg/axisPLC.md" >}}) for PLC-based synchronization/interlocking.
- [Motor Record]({{< relref "/manual/motion_cfg/motor.md" >}}) for motor record behavior and integration.

### Runtime commissioning and tuning
- [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}}) for runtime inspection and tuning via the ecmc command parser.
- [motion knowledge base]({{< relref "/manual/knowledgebase/motion.md" >}}) and [tuning knowledge base]({{< relref "/manual/knowledgebase/tuning.md" >}}) for troubleshooting/tuning workflows.

### YAML parser backend
- [ecb]({{< relref "/manual/motion_cfg/ecb.md" >}}) for C++ schema validation/rendering backend used by YAML loaders (`ECMC_CFG_TOOL=ecb`).

### Reusable component-level slave configuration
- [ecmccomp]({{< relref "/manual/motion_cfg/ecmccomp.md" >}}) for applying validated motor/encoder/slave components using `applyComponent.cmd`.

### Patterns and conventions
- [best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}}) for recommended configuration patterns.

## Recommended Reading Paths
### New axis bring-up (YAML-first)
1. [YAML config]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
2. [Drive modes CSV, CSP, CSP-PC]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}})
3. [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}})
4. [direction]({{< relref "/manual/motion_cfg/direction.md" >}})
5. [homing]({{< relref "/manual/motion_cfg/homing.md" >}})
6. [Motor Record]({{< relref "/manual/motion_cfg/motor.md" >}})
7. [motion knowledge base]({{< relref "/manual/knowledgebase/motion.md" >}})

### Runtime tuning/optimization
1. [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}})
2. [tuning knowledge base]({{< relref "/manual/knowledgebase/tuning.md" >}})
3. Reflect validated runtime changes back into [YAML config]({{< relref "/manual/motion_cfg/axisYaml.md" >}}) or startup scripts.

### YAML parser backend selection
1. [ecb]({{< relref "/manual/motion_cfg/ecb.md" >}})
2. [YAML config]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
3. [knowledge base motion parser notes]({{< relref "/manual/knowledgebase/motion.md" >}})

### Component-library based hardware setup
1. [ecmccomp]({{< relref "/manual/motion_cfg/ecmccomp.md" >}})
2. [YAML config]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
3. [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}}) and [direction]({{< relref "/manual/motion_cfg/direction.md" >}})
