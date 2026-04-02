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

## axis
- `id` (required) — Axis id.
- `type` (optional) — Future selection of axis type; see type mapping in the axis section.
- `mode` (optional) — Supported modes CSV or CSP; defaults to CSV.
- `parameters` (optional) — Additional parameters for the motor record driver (e.g. powerAutoOnOff, powerOffDelay, powerOnDelay).
- `healthOutput` (optional) — EtherCAT entry for health output.
- `feedSwitchesOutput` (optional) — EtherCAT entry for fed switches.
- `feedSwitchesValue` (optional) — Value written to `axis.feedSwitchesOutput`; defaults to 1.
- `group` (optional) — Group name; creates/uses a group and stores its id in `GRP_<axis.group>_ID`. See [Axis Groups]({{< relref "/manual/general_cfg/axis_groups.md" >}}).
- `autoMode` (optional) — Auto-switch drive modes for motion/homing.
  - `modeSet` — EtherCAT entry to write drive mode (CSV/CSP/homing).
  - `modeAct` — EtherCAT entry reading drive mode.
  - `modeCmdMotion` — Drive mode value used during normal motion.
  - `modeCmdHome` — Drive mode value used during homing.
- `features` (optional) — Feature switches.
  - `blockCom` — Block communication to axis.
  - `allowSrcChangeWhenEnabled` — Allow trajectory/encoder source change while enabled.
  - `allowedFunctions.homing` — Allow homing.
  - `allowedFunctions.constantVelocity` — Allow constant velocity mode.
  - `allowedFunctions.positioning` — Allow positioning.
- `autoEnable` (preferred over motor record auto-enable) — Native ecmc auto enable/disable.
  - `enableTimeout` — Try auto-enable for at most this many seconds.
  - `disableTimeout` — Disable after being idle this many seconds.
  - `atStartup` — Auto-enable at IOC start (default false).
- `tweakDist` (optional) — Tweak value for both ecmc and motor record.

## epics
- `name` (required) — PV name.
- `precision` (optional) — PREC; default 3.
- `description` (optional) — Axis description.
- `unit` (optional) — EGU; default mm.
- `motorRecord` (optional) — Motor record block.
  - `enable` — Enable motor record.
  - `description` — Motor record description.
  - `fieldInit` — Additional motor record fields.
  - `syncSoftLimits` — Sync soft limits between motor record and ecmc (default false).
  - `pvt` — PVT/profile-move support.
    - `npoints` — Max number of target points.
    - `nreadback` — Max number of readback points.

## drive
- `numerator` (required) — Fastest speed in engineering units.
- `denominator` (required) — I/O range for `ECMC_EC_ALIAS_DRV_VELO_SET`.
- `type` (required) — 0=stepper, 1=DS402 (servo/advanced stepper).
- `control` (required) — Control word EtherCAT entry.
- `enable` (required for non-DS402) — Enable bit index in control word.
- `enabled` (required for non-DS402) — Enabled bit index in status word.
- `status` (required) — Status word EtherCAT entry.
- `setpoint` (required) — Velocity setpoint if CSV; position setpoint if CSP. `F32`/`F64` CSV setpoints are supported. `F32`/`F64` CSP setpoints require the selected CSP encoder actual-position entry to use the same datatype.
- `reduceTorque` (optional) — Reduce torque bit in control word.
- `reduceTorqueEnable` (optional) — Enable reduce torque handling.
- `brake` (optional) — Brake control block.
  - `enable` — Enable brake control.
  - `output` — EtherCAT link to brake output.
  - `openDelay` — Brake open delay in cycles.
  - `closeAhead` — Brake close-ahead time in cycles.
- `reset` (optional) — Reset bit.
- `warning` (optional) — Warning bit.
- `error` (optional, up to 3 entries) — Error bits.

## encoder
- `numerator` (required) — Scaling numerator (e.g. 360 deg/rev).
- `denominator` (required) — Scaling denominator (e.g. ticks per rev).
- `type` (required) — 0=incremental, 1=absolute.
- `bits` (required) — Raw data bit count.
- `absBits` (required) — Absolute bit count (LSBs of `bits`).
- `absOffset` (required) — Offset in engineering units for absolute encoders.
- `mask` (optional) — Mask applied to raw encoder value.
- `position` (required) — EtherCAT entry for actual position. `F32`/`F64` actual-position entries are only valid for absolute encoders (`type: 1`). Keep `bits` and `absBits` aligned with the datatype width (`32`/`32` or `64`/`64`).
- `control` (optional; required if reset is used) — Encoder control word entry.
- `status` (optional; required if warning/error are used) — Encoder status word entry.
- `ready` (optional) — Status bit for encoder ready.
- `source` (optional) — 0=from EtherCAT hardware, 1=from PLC.
- `reset` (optional) — Reset bit.
- `warning` (optional) — Warning bit.
- `error` (optional, up to 3 entries) — Error bits.
- `filter` (optional) — Encoder-side filtering.
  - `velocity.size` — Velocity filter size.
  - `velocity.enable` — Enable velocity filter.
  - `position.size` — Position filter size.
  - `position.enable` — Enable position filter.
- `latch` (optional) — Latch/touch probe settings.
  - `position` — Latched value link.
  - `control` — Control bit to arm latch.
  - `status` — Status bit for latch triggered.
  - `armCmd` — Value written to `encoder.control` to arm latch.
  - `armBits` — Bit length of `armCmd`.
- `primary` (optional) — Use as primary encoder for control.
- `useAsCSPDrvEnc` (optional) — Use as CSP drive encoder when controller enabled in CSP.
- `allowOverUnderFlow` (optional) — Allow over/under flow of encoder raw counter (default true). Set to false for linear encoders.
- `homing` (optional) — Encoder homing settings.
  - `type` — Homing sequence type.
  - `position` — Referenced position.
  - `velocity.to` — Velocity to cam/sensor.
  - `velocity.from` — Velocity off cam/sensor.
  - `acceleration` — Homing acceleration.
  - `deceleration` — Homing deceleration.
  - `refToEncIDAtStartup` — Copy start value from another encoder id at startup.
  - `refAtHome` — Set position after homing.
  - `tolToPrim` — Max tolerance vs primary encoder.
  - `postMoveEnable` — Enable post-move after homing.
  - `postMovePosition` — Post-move target position.
  - `trigg` — EtherCAT entry to trigger drive internal homing sequence.
  - `ready` — Status entry for drive internal homing ready.
  - `latchCount` — Latch number to reference (1=first latch).
- `delayComp` (optional) — Delay compensation between set and act.
  - `time` — Delay time in cycles.
  - `enable` — Enable flag (defaults to true if set).
- `lookuptable` (optional) — Correction lookup table (applied when homed).
  - `filename` — LUT file; value subtracted from encoder value.
  - `enable` — Enable LUT (default true if loaded).
  - `scale` — LUT scale; set to -1.0 to add instead of subtract.
  - `range` — Modulo range the LUT covers.

## controller
- `Kp` (required) — Proportional gain.
- `Ki` (optional) — Integral gain.
- `Kd` (optional) — Derivative gain.
- `Kff` (optional) — Feed-forward gain.
- `deadband.tol` (optional) — Stop control within this distance.
- `deadband.time` (optional) — Deadband time filter.
- `limits.minOutput` / `maxOutput` (optional) — Output clamps. Active only when `maxOutput > minOutput`; both `0` disables the limits.
- `limits.minIntegral` / `maxIntegral` (optional) — Integral clamps. Active only when `maxIntegral > minIntegral`; both `0` disables the limits.
- `inner.Kp` / `inner.Ki` / `inner.Kd` / `inner.tol` (optional) — Inner PID used near target.

## trajectory
- `type` (optional) — 0=trapezoidal, 1=s-curve (ruckig); defaults to trapezoidal.
- `source` (optional) — 0=trajectory generator, 1=PLC source.
- `axis.velocity` (required) — Default velocity.
- `axis.acceleration` (required) — Default acceleration.
- `axis.deceleration` (optional) — Default deceleration.
- `axis.emergencyDeceleration` (optional) — Deceleration in error state.
- `axis.jerk` (optional) — Default jerk.
- `jog.velocity` (optional) — Default jog velocity (motor record).
- `modulo.range` (optional) — Modulo range.
- `modulo.type` (optional) — Modulo type.

## input
- `limit.forward` (required) — Forward limit switch entry.
- `limit.forwardPolarity` (required) — Forward limit polarity.
- `limit.backward` (required) — Backward limit switch entry.
- `limit.backwardPolarity` (required) — Backward limit polarity.
- `home` (required) — Home switch entry.
- `homePolarity` (required) — Home switch polarity.
- `interlock` (required) — Interlock input entry.
- `interlockPolarity` (required) — Interlock polarity.
- `analog` (optional) — Analog interlock block.
  - `interlock` — Analog interlock entry.
  - `interlockPolarity` — 0: high is bad; 1: low is bad.
  - `rawLimit` — Raw analog limit.
  - `enable` — Enable analog interlock (default true if set).

## softlimits
- `enable` (optional) — Global soft limit enable.
- `forward` (optional) — Forward soft limit.
- `forwardEnable` (optional) — Forward soft limit enable.
- `backward` (optional) — Backward soft limit.
- `backwardEnable` (optional) — Backward soft limit enable.

## monitoring
- `lag.enable` / `lag.tolerance` / `lag.time` (optional) — Position lag (following error) monitoring.
- `target.enable` / `target.tolerance` / `target.time` (optional) — At-target monitoring (mandatory when using motor record).
- `velocity.enable` / `velocity.max` / `velocity.time.trajectory` / `velocity.time.drive` (optional) — Velocity monitoring.
- `velocityDifference.enable` / `velocityDifference.max` / `velocityDifference.time.trajectory` / `velocityDifference.time.drive` (optional) — Velocity setpoint vs actual monitoring.
- `stall.enable` / `stall.time.timeout` / `stall.time.factor` (optional) — Stall monitoring (requires target monitoring enabled).

## plc
- `enable` (optional) — Enable axis PLC.
- `externalCommands` (optional) — Allow external PLC commands.
- `file` (optional) — PLC code file to include.
- `code` (optional) — Inline PLC code list (appended after `plc.file` content); example shows enable logic and setpoint calculation.
- `velocity_filter` (optional) — Velocity feedforward smoothing.
  - `encoder.enable` / `encoder.size` — Filter PLC encoder velocity.
  - `trajectory.enable` / `trajectory.size` — Filter PLC trajectory velocity.
- `filter` (optional; deprecated alias) — Older naming for velocity filters with the same subkeys.
