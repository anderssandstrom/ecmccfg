+++
title = "Axis YAML settings (heading view)"
slug = "axisyaml-headings"
weight = 17
chapter = false
+++

Reference companion to [yaml configuration](../axisyaml/).
Use this page when you want to browse YAML settings by section instead of by
full key name.

Use the heading view when:

- you are building a new axis YAML file section by section
- you want to see related settings together
- you know you are working in `encoder`, `trajectory`, `monitoring`, or `plc`
  but do not remember the exact key names

Use the table view when:

- you want the exact full key path
- you want the fastest mandatory/optional lookup

See also: [Axis YAML settings table](../axisyaml-table/).

For examples and configuration guidance, use [yaml configuration](../axisyaml/).

<!-- BEGIN GENERATED AXIS YAML REFERENCE -->

## axis

- `axis.id` (required) — Axis id.
- `axis.type` (optional) — Future selection of axis type; see type mapping in the axis section.
- `axis.mode` (optional) — Supported modes CSV or CSP; defaults to CSV.
- `axis.parameters` (optional) — Additional motor driver options (e.g. powerAutoOnOff, powerOffDelay, powerOnDelay). `restoreMotorSoftLims=1;` enables startup restoration of motor dial limits and ongoing synchronization; see [autosave]({{< relref "/manual/motion_cfg/autosave.md" >}}).
- `axis.healthOutput` (optional) — EtherCAT entry for health output.
- `axis.feedSwitchesOutput` (optional) — EtherCAT entry for fed switches.
- `axis.feedSwitchesValue` (optional) — Value written to `axis.feedSwitchesOutput`; defaults to 1.
- `axis.group` (optional) — Group name; creates/uses a group and stores its id in `GRP_<axis.group>_ID`. See [Axis Groups]({{< relref "/manual/motion_cfg/axis_groups.md" >}}).
- `axis.autoMode` (optional) — Auto-switch drive modes for motion/homing.
- `axis.autoMode.modeSet` (optional) — EtherCAT entry to write drive mode (CSV/CSP/homing).
- `axis.autoMode.modeAct` (optional) — EtherCAT entry reading drive mode.
- `axis.autoMode.modeCmdMotion` (optional) — Drive mode value used during normal motion.
- `axis.autoMode.modeCmdHome` (optional) — Drive mode value used during homing.
- `axis.features` (optional) — Feature switches.
- `axis.features.blockCom` (optional) — Block communication to axis.
- `axis.features.allowSrcChangeWhenEnabled` (optional) — Allow trajectory/encoder source change while enabled.
- `axis.features.allowedFunctions.homing` (optional) — Allow homing.
- `axis.features.allowedFunctions.constantVelocity` (optional) — Allow constant velocity mode.
- `axis.features.allowedFunctions.positioning` (optional) — Allow positioning.
- `axis.autoEnable` (optional) — Native ecmc auto enable/disable. Preferred over motor record auto-enable.
- `axis.autoEnable.enableTimeout` (optional) — Try auto-enable for at most this many seconds.
- `axis.autoEnable.disableTimeout` (optional) — Disable after being idle this many seconds.
- `axis.autoEnable.autoDisableLatchAtTarget` (optional) — After the first AtTarget assertion, allow the auto-disable timer to continue if AtTarget is later lost (default false).
- `axis.autoEnable.atStartup` (optional) — Auto-enable at IOC start (default false).
- `axis.tweakDist` (optional) — Tweak value for both ecmc and motor record.

## epics

- `epics.name` (required) — PV name.
- `epics.precision` (optional) — PREC; default 3.
- `epics.description` (optional) — Axis description.
- `epics.unit` (optional) — EGU; default mm.
- `epics.motorRecord` (optional) — Motor record block.
- `epics.motorRecord.enable` (optional) — Enable motor record.
- `epics.motorRecord.description` (optional) — Motor record description.
- `epics.motorRecord.fieldInit` (optional) — Additional motor record fields.
- `epics.motorRecord.syncSoftLimits` (optional) — Sync soft limits between motor record and ecmc (default false; `restoreMotorSoftLims=1` overrides this to enabled). When synchronization is disabled, motor record `HLM`/`LLM` and ecmc soft limits may differ. On false-to-true, ecmc soft limits are copied to the motor record; while true, later motor record soft-limit changes are written back to ecmc.
- `epics.motorRecord.pvt` (optional) — PVT/profile-move support.
- `epics.motorRecord.pvt.npoints` (optional) — Max number of target points.
- `epics.motorRecord.pvt.nreadback` (optional) — Max number of readback points.

## drive

- `drive.numerator` (required) — Fastest speed in engineering units.
- `drive.denominator` (required) — I/O range for `ECMC_EC_ALIAS_DRV_VELO_SET`.
- `drive.type` (required) — 0=stepper, 1=DS402 (servo/advanced stepper).
- `drive.control` (required) — Control word EtherCAT entry.
- `drive.enable` (required for non-DS402) — Enable bit index in control word.
- `drive.enabled` (required for non-DS402) — Enabled bit index in status word.
- `drive.status` (required) — Status word EtherCAT entry.
- `drive.setpoint` (required) — Velocity setpoint if CSV; position setpoint if CSP. `F32`/`F64` CSV setpoints are supported. `F32`/`F64` CSP setpoints require the selected CSP encoder actual-position entry to use the same datatype.
- `drive.reduceTorque` (optional) — Reduce torque bit in control word.
- `drive.reduceTorqueEnable` (optional) — Enable reduce torque handling.
- `drive.brake` (optional) — Brake control block.
- `drive.brake.enable` (optional) — Enable brake control.
- `drive.brake.output` (optional) — EtherCAT link to brake output.
- `drive.brake.openDelay` (optional) — Brake open delay in cycles.
- `drive.brake.closeAhead` (optional) — Brake close-ahead time in cycles.
- `drive.reset` (optional) — Reset bit.
- `drive.warning` (optional) — Warning bit.
- `drive.error` (optional, up to 3 entries) — Error bits.
- `drive.error[2]` (required) — Error 2 (if no drive error bit then leave empty)
- `drive.error[1]` (required) — Error 1 (if no drive error bit then leave empty)
- `drive.error[0]` (required) — Error 0 (if no drive error bit then leave empty)

## encoder

- `encoder.numerator` (required) — Scaling numerator (e.g. 360 deg/rev).
- `encoder.denominator` (required) — Scaling denominator (e.g. ticks per rev).
- `encoder.type` (required) — 0=incremental, 1=absolute.
- `encoder.bits` (required) — Bit count used for ecmc's encoder value; it does not alter the raw EtherCAT slave value.
- `encoder.absBits` (required) — Absolute bit count (LSBs of `bits`).
- `encoder.absOffset` (required) — Offset in engineering units for absolute encoders.
- `encoder.mask` (optional) — Mask applied to ecmc's encoder value, not the raw EtherCAT slave value. The original value remains visible in the EtherCAT hardware PVs.
- `encoder.position` (required) — EtherCAT entry for actual position. `F32`/`F64` actual-position entries are only valid for absolute encoders (`type: 1`). Keep `bits` and `absBits` aligned with the datatype width (`32`/`32` or `64`/`64`).
- `encoder.control` (optional; required if reset is used) — Encoder control word entry.
- `encoder.status` (optional; required if warning/error are used) — Encoder status word entry.
- `encoder.ready` (optional) — Status bit for encoder ready.
- `encoder.source` (optional) — 0=from EtherCAT hardware, 1=from PLC.
- `encoder.reset` (optional) — Reset bit.
- `encoder.warning` (optional) — Warning bit.
- `encoder.error` (optional, up to 3 entries) — Error bits.
- `encoder.filter` (optional) — Encoder-side filtering.
- `encoder.filter.velocity.size` (optional) — Velocity filter size.
- `encoder.filter.velocity.enable` (optional) — Enable velocity filter.
- `encoder.filter.position.size` (optional) — Position filter size.
- `encoder.filter.position.enable` (optional) — Enable position filter.
- `encoder.latch` (optional) — Homing latch settings. For EL7062/ED7062 touch-probe use outside homing, prefer the separate `touchProbe` section.
- `encoder.latch.position` (optional) — Latched value link.
- `encoder.latch.timestamp` (optional) — Optional DC timestamp for the same latch event.
- `encoder.latch.control` (optional) — Control bit to arm latch.
- `encoder.latch.status` (optional) — Status bit for latch triggered.
- `encoder.latch.armCmd` (optional) — Value written to `encoder.control` to arm latch.
- `encoder.latch.armBits` (optional) — Bit length of `armCmd`.
- `encoder.touchProbe` (optional) — Encoder touch-probe mapping separate from homing latch.
- `encoder.touchProbe.position` (optional) — Latched touch-probe position entry.
- `encoder.touchProbe.timestamp` (optional) — Optional 32- or 64-bit DC timestamp entry for the same edge.
- `encoder.touchProbe.control` (optional) — Touch-probe control word entry.
- `encoder.touchProbe.controlBit` (optional) — First bit to write in the control word (default `0`).
- `encoder.touchProbe.status` (optional) — Touch-probe status word entry.
- `encoder.touchProbe.statusBit` (optional) — Status bit that indicates a captured event (default `0`).
- `encoder.touchProbe.armCmd` (optional) — Value written to arm the touch probe (default `17`, EL7062/ED7062 TP1 positive edge).
- `encoder.touchProbe.armBits` (optional) — Number of bits written from `armCmd` (default `5`).
- `encoder.primary` (optional) — Use as primary encoder for control.
- `encoder.useAsCSPDrvEnc` (optional) — Use as CSP drive encoder when controller enabled in CSP.
- `encoder.allowOverUnderFlow` (optional) — Allow over/under flow of encoder raw counter (default true). Set to false for linear encoders.
- `encoder.homing` (optional) — Encoder homing settings.
- `encoder.homing.type` (optional) — Homing sequence type.
- `encoder.homing.position` (optional) — Referenced position.
- `encoder.homing.velocity.to` (optional) — Velocity to cam/sensor.
- `encoder.homing.velocity.from` (optional) — Velocity off cam/sensor.
- `encoder.homing.acceleration` (optional) — Homing acceleration.
- `encoder.homing.deceleration` (optional) — Homing deceleration.
- `encoder.homing.refToEncIDAtStartup` (optional) — Copy start value from another encoder id at startup.
- `encoder.homing.refAtHome` (optional) — Set position after homing.
- `encoder.homing.tolToPrim` (optional) — Max tolerance vs primary encoder.
- `encoder.homing.postMoveEnable` (optional) — Enable post-move after homing.
- `encoder.homing.postMovePosition` (optional) — Post-move target position.
- `encoder.homing.trigg` (optional) — EtherCAT entry to trigger drive internal homing sequence.
- `encoder.homing.ready` (optional) — Status entry for drive internal homing ready.
- `encoder.homing.latchCount` (optional) — Latch number to reference (1=first latch).
- `encoder.delayComp` (optional) — Delay compensation between set and act.
- `encoder.delayComp.time` (optional) — Delay time in cycles.
- `encoder.delayComp.enable` (optional) — Enable flag (defaults to true if set).
- `encoder.lookuptable` (optional) — Correction lookup table (applied when homed).
- `encoder.lookuptable.filename` (optional) — LUT file; value subtracted from encoder value.
- `encoder.lookuptable.enable` (optional) — Enable LUT (default true if loaded).
- `encoder.lookuptable.scale` (optional) — LUT scale; set to -1.0 to add instead of subtract.
- `encoder.lookuptable.range` (optional) — Modulo range the LUT covers.
- `encoder.error[1]` (optional) — Error 1
- `encoder.error[2]` (optional) — Error 2
- `encoder.error[0]` (optional) — Error 0

## controller

- `controller.Kp` (required) — Proportional gain.
- `controller.Ki` (optional) — Integral gain.
- `controller.Kd` (optional) — Derivative gain.
- `controller.Kff` (optional) — Feed-forward gain.
- `controller.resetIAtRmp` (optional) — Reset the integral part to zero while an internal trajectory is busy.
- `controller.freezeIAtRmp` (optional) — Freeze the integral part at its current value while an internal trajectory is busy.
- `controller.deadband.tol` (optional) — Stop control within this distance.
- `controller.deadband.time` (optional) — Deadband time filter.
- `controller.limits.minOutput` / `controller.limits.maxOutput` (optional) — Output clamps. Active only when `maxOutput > minOutput`; both `0` disables the limits.
- `controller.limits.minIntegral` / `controller.limits.maxIntegral` (optional) — Integral clamps. Active only when `maxIntegral > minIntegral`; both `0` disables the limits.
- `controller.inner.Kp` / `controller.inner.Ki` / `controller.inner.Kd` / `controller.inner.tol` (optional) — Inner PID used near target.

## trajectory

- `trajectory.type` (optional) — 0=trapezoidal, 1=s-curve (ruckig); defaults to trapezoidal.
- `trajectory.source` (optional) — 0=trajectory generator, 1=PLC source.
- `trajectory.axis.velocity` (required) — Default velocity.
- `trajectory.axis.acceleration` (required) — Default acceleration.
- `trajectory.axis.deceleration` (optional) — Default deceleration.
- `trajectory.axis.emergencyDeceleration` (optional) — Deceleration in error state.
- `trajectory.axis.jerk` (optional) — Default jerk.
- `trajectory.jog.velocity` (optional) — Default jog velocity (motor record).
- `trajectory.modulo.range` (optional) — Modulo range.
- `trajectory.modulo.type` (optional) — Modulo type.

## positionCompare

- `positionCompare.output` (required) — EtherCAT output entry to schedule, for example an EL2252 binary output.
- `positionCompare.activate` (required) — EtherCAT activation/control entry used by the timed-output terminal.
- `positionCompare.startTime` (required) — EtherCAT DC start-time entry. Use a 64-bit integer PV/entry for EL2252 start time.
- `positionCompare.minLeadMs` (optional) — Minimum allowed scheduling lead time in milliseconds (default `2.0`).
- `positionCompare.maxLeadMs` (optional) — Maximum allowed scheduling lead time in milliseconds (default `100.0`).
- `positionCompare.activateIdle` (optional) — Activation value written while idle (default `3` for EL2252).
- `positionCompare.activateSchedule` (optional) — Activation value written for one cycle to load a new schedule (default `0` for EL2252).
- `positionCompare.pulseWidthMs` (optional) — If greater than zero, schedule an automatic reset after this pulse width in milliseconds. Fractions such as `0.5` are allowed.
- `positionCompare.resetValue` (optional) — Output value used for the automatic reset (default `0`).

## input

- `input.limit.forward` (required) — Forward limit switch entry.
- `input.limit.forwardPolarity` (required) — Forward limit polarity.
- `input.limit.backward` (required) — Backward limit switch entry.
- `input.limit.backwardPolarity` (required) — Backward limit polarity.
- `input.home` (required) — Home switch entry.
- `input.homePolarity` (required) — Home switch polarity.
- `input.interlock` (required) — Interlock input entry.
- `input.interlockPolarity` (required) — Interlock polarity.
- `input.analog` (optional) — Analog interlock block.
- `input.analog.interlock` (optional) — Analog interlock entry.
- `input.analog.interlockPolarity` (optional) — 0: high is bad; 1: low is bad.
- `input.analog.rawLimit` (optional) — Raw analog limit.
- `input.analog.enable` (optional) — Enable analog interlock (default true if set).

## softlimits

- `softlimits.enable` (optional) — Global soft limit enable.
- `softlimits.forward` (optional) — Forward soft limit.
- `softlimits.forwardEnable` (optional) — Forward soft limit enable.
- `softlimits.backward` (optional) — Backward soft limit.
- `softlimits.backwardEnable` (optional) — Backward soft limit enable.

## monitoring

- `monitoring.lag.enable` / `monitoring.lag.tolerance` / `monitoring.lag.time` (optional) — Position lag (following error) monitoring.
- `monitoring.target.enable` / `monitoring.target.tolerance` / `monitoring.target.time` (optional) — At-target monitoring (mandatory when using motor record).
- `monitoring.target.slaveControlDeadband.tolerance` / `monitoring.target.slaveControlDeadband.time` (optional) — Live master-axis band forwarded to slaves for reduced-torque control. Applies to physical and virtual master axes and defaults to the AtTarget tolerance and time when omitted.
- `monitoring.velocity.enable` / `monitoring.velocity.max` / `monitoring.velocity.time.trajectory` / `monitoring.velocity.time.drive` (optional) — Velocity monitoring.
- `monitoring.velocityDifference.enable` / `monitoring.velocityDifference.max` / `monitoring.velocityDifference.time.trajectory` / `monitoring.velocityDifference.time.drive` (optional) — Velocity setpoint vs actual monitoring.
- `monitoring.stall.enable` / `monitoring.stall.time.timeout` / `monitoring.stall.time.factor` (optional) — Stall monitoring (requires target monitoring enabled).

## plc

- `plc.enable` (optional) — Enable axis PLC.
- `plc.externalCommands` (optional) — Allow external PLC commands.
- `plc.file` (optional) — PLC code file to include.
- `plc.code` (optional) — Inline PLC code list (appended after `plc.file` content); example shows enable logic and setpoint calculation.
- `plc.velocity_filter` (optional) — Velocity feedforward smoothing.
- `plc.velocity_filter.encoder.enable` / `plc.velocity_filter.encoder.size` (optional) — Filter PLC encoder velocity.
- `plc.velocity_filter.trajectory.enable` / `plc.velocity_filter.trajectory.size` (optional) — Filter PLC trajectory velocity.
- `plc.filter` (optional; deprecated alias) — Older naming for velocity filters with the same subkeys.

<!-- END GENERATED AXIS YAML REFERENCE -->
