+++
title = "motion"
weight = 10
chapter = false
+++


## Topics
{{% children %}}
---

## Axis Overview

ECMC has two axis types:
1. Physical axes (joints)
2. Virtual axes (end effectors)

Both are classes in ECMC. A physical axis is effectively a superset of a virtual axis, since it includes hardware coupling.

### [YAML config](axisYaml)
Since v7, axes can be configured with YAML files.
This is a huge improvement over the classic configuration based on EPICS environment variables.
For backward compatibility the classical configuration is still supported.

#### Linting and schema check
From v8+, YAML files are linted for syntactic errors. Check iocsh for warnings and errors.
Additionally, the schema of the YAML file is checked by Cerberus.
This check will point out errors in the structure of the configuration as well as certain type errors.

### [PLC YAML config](axisPLC)
Synchronization configuration

### [ecmc_cfg_tool](ecmc_cfg_tool)
Runtime tool for inspecting and adjusting settings through the ecmc command parser.

### [scaling](scaling)
Configuration of scaling

### [direction](direction)
Defining the direction of motion

### [homing](homing)
Configuration of homing

## Recommended Reading Order
1. Start with [YAML config](axisYaml) to understand required sections and examples.
2. Continue with [scaling](scaling) and [direction](direction) before tuning.
3. Add [homing](homing) once basic motion is stable.
4. Use the [motion knowledge base](../knowledgebase/motion/) for troubleshooting.
5. Use [ecmc_cfg_tool](ecmc_cfg_tool) for runtime inspection/tuning via the ecmc command parser.
