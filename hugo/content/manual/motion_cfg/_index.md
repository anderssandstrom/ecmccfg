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

## Configuration Warnings

When an axis is validated before runtime, ecmc can write warnings to the
configuration log buffer. These warnings are intended to catch configurations
that are legal but likely to behave badly. They do not block startup by
themselves, but they should be reviewed before the IOC is put into service.

Examples include:

- enabled monitors with a zero limit or tolerance, such as at-target,
  position-lag, max-velocity, velocity-difference, or controller-output
  monitoring
- controller `Kp` equal to zero when the ecmc position controller is used
- controller settings configured in pure CSP, where the drive closes the
  position loop and ecmc controller parameters are not used
- controller deadband larger than the at-target tolerance
- requested target, maximum, or homing velocities that exceed the integer CSV
  velocity-setpoint range after scaling

For CSV axes with an integer velocity setpoint, a small at-target tolerance
combined with a low `Kp` can also cause a warning. Close to the target, the
position controller output is converted to the drive velocity setpoint. If
`Kp * monitoring.target.tolerance * abs(drive.denominator / drive.numerator)`
is below about `0.5` raw counts, the velocity setpoint may round to zero. The
axis can then stop near the target because the remaining error no longer
produces an effective velocity command. If stall monitoring is enabled, this
can also result in `ERROR_MON_STALL`.

Mitigate this by increasing `monitoring.target.tolerance`, increasing the
active `Kp`, or using suitable inner controller parameters for final
positioning. This specific rounding warning applies to CSV axes with integer
velocity setpoints. See also [tuning]({{< relref "/manual/knowledgebase/tuning.md#axis-stops-close-to-target" >}})
and [RT logger diagnostics]({{< relref "/manual/general_cfg/rt_logger_diagnostics.md" >}}).

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
