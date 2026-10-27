+++
title = "Motion configuration"
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

<!-- Preserve links to the former overview headings. -->
<a id="new-axis-bring-up"></a>
<a id="recommended-reading-paths"></a>

## Commission a new axis

1. Follow the [Quickstart]({{< relref "/manual/quickstart.md" >}}) and select a [motion example]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}}).
2. Configure the axis with the [YAML guide]({{< relref "/manual/motion_cfg/axisYaml.md" >}}) and choose the [drive mode]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}}).
3. Verify [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}}) and [direction of motion]({{< relref "/manual/motion_cfg/direction.md" >}}).
4. Configure and verify [homing]({{< relref "/manual/motion_cfg/homing.md" >}}).
5. Configure [motor-record behavior]({{< relref "/manual/motion_cfg/motor.md" >}}) and [position and soft-limit autosave]({{< relref "/manual/motion_cfg/autosave.md" >}}) when needed.
6. Check [motion diagnostics]({{< relref "/manual/knowledgebase/motion.md" >}}) and [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}}). Review the configuration warnings below before putting the IOC into service.

<!-- Preserve links to the former overview headings. -->
<a id="common-tasks"></a>
<a id="existing-ioc-with-classic-motion-files"></a>
<a id="key-references"></a>
<a id="runtime-tuning-and-diagnostics"></a>
<a id="synchronization-and-axis-logic"></a>
<a id="topics"></a>

## Find a topic

| Task | Guide |
| --- | --- |
| Look up YAML keys | [Settings table]({{< relref "/manual/motion_cfg/axisYamlSettingsTable.md" >}}) or [grouped settings]({{< relref "/manual/motion_cfg/axisYamlSettingsHeadings.md" >}}) |
| See all settings in a configuration | [Complete axis YAML example]({{< relref "/manual/motion_cfg/axisYamlExample.md" >}}) |
| Configure motor-record examples and retry tests | [Motor record examples]({{< relref "/manual/motion_cfg/best_practice/motor.md" >}}) |
| Create named collections of axes | [Axis groups]({{< relref "/manual/motion_cfg/axis_groups.md" >}}) |
| Coordinate virtual master and physical slave axes | [Master/slave state machine]({{< relref "/manual/motion_cfg/master_slave_state_machine.md" >}}) |
| Synchronize axes and add axis-local logic | [Axis PLC]({{< relref "/manual/motion_cfg/axisPLC.md" >}}) and [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}}) |
| Configure PVT/profile moves | [PVT]({{< relref "/manual/motion_cfg/pvt.md" >}}) |
| Use motion sequences | [Motion sequencer]({{< relref "/manual/motion_cfg/sequencer.md" >}}) |
| Inspect or tune a running IOC | [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}}) |
| Select a configuration backend | [ecb]({{< relref "/manual/motion_cfg/ecb.md" >}}) and [ecmccomp]({{< relref "/manual/motion_cfg/ecmccomp.md" >}}) |
| Maintain classic `.ax`, `.vax`, or `.sax` files | [Legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}}); use the scaling, direction, homing, and motion diagnostics guides above as needed |

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
and [RT logger diagnostics]({{< relref "/manual/general_cfg/utilities/rt_logger_diagnostics.md" >}}).
