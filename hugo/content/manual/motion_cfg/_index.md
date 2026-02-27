+++
title = "motion"
weight = 10
chapter = false
+++


## Topics
{{% children %}}
---

## axis

ECMC has two types of axes, (1) physical axes, aka joints, and (2) virtual axes, aka end effector.
Both types are classes in ECMC, the physical axis is a super-set of the virtual axes, as the latter lacks the hardware.

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

### [scaling](scaling)
Configuration of scaling

### [direction](direction)
Defining the direction of motion

### [homing](homing)
Configuration of homing
