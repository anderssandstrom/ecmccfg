+++
title = "Axis YAML settings table"
slug = "axisyaml-table"
weight = 16
chapter = false
+++

Reference companion to [yaml configuration](../axisyaml/).
Use this page when you need the exact YAML key name quickly.

Use the table view when:

- you already know roughly which section you need
- you want to confirm whether a key exists
- you want a fast mandatory/optional check

Use the heading view when:

- you want grouped navigation by section
- you want to browse related settings together

See also: [Axis YAML settings (heading view)](../axisyaml-headings/).

Notes:

- Requirements describe configuration guidance in the relevant context. Optional
  sections can contain required keys; defaults and dependencies also affect what
  must be supplied. Consult the configuration guide and the selected loader's
  validation messages for your axis type.
- Both reference views use the same requirements and descriptions source.
- “Optional” means the key can be omitted in the stated context; conditional
  requirements are shown explicitly.

<!-- BEGIN GENERATED AXIS YAML REFERENCE -->

| Key | Description | Requirement |
| --- | --- | --- |
| `axis.id` | Axis id | required |
| `axis.type` | Axis type | optional |
| `axis.mode` | Supported mode, CSV and CSP, defaults CSV | optional |
| `axis.parameters` | Additional motor driver options. `restoreMotorSoftLims=1;` lets initialized/autosave-restored motor dial limits override ECMC at startup and also enables ongoing synchronization. See [autosave]({{< relref "/manual/motion_cfg/autosave.md" >}}). | optional |
| `axis.healthOutput` | EtherCAT entry for health output | optional |
| `axis.feedSwitchesOutput` | EtherCAT entry for fed switches | optional |
| `axis.feedSwitchesValue` | Value to write to axis.feedSwitchesOutput. Defaults to 1 | optional |
| `axis.group` | Add axis to group (group will be created if it does not exist) | optional |
| `axis.autoMode.modeSet` | EtherCAT entry drive mode write (set CSV,CSP,homing) | optional |
| `axis.autoMode.modeAct` | EtherCAT entry drive mode reading (set CSV,CSP,homing) | optional |
| `axis.autoMode.modeCmdMotion` | Drive mode value for normal motion (written to axis.drvMode.modeSet when normal motion) | optional |
| `axis.autoMode.modeCmdHome` | Drive mode value for when homing (written to axis.drvMode.modeSet when homing) | optional |
| `axis.features.blockCom` | Block communication to axis | optional |
| `axis.features.allowSrcChangeWhenEnabled` | Allow traj/enc source change when axis is enabled | optional |
| `axis.features.allowedFunctions.homing` | Allow homing | optional |
| `axis.features.allowedFunctions.constantVelocity` | Allow constant velocity | optional |
| `axis.features.allowedFunctions.positioning` | Allow positioning | optional |
| `axis.autoEnable.enableTimeout` | If defined, ecmc tries to auto-enable for a maximum enableTimeout seconds. | optional |
| `axis.autoEnable.disableTimeout` | If defined, ecmc disables axis after idle (non busy) in disableTime seconds | optional |
| `axis.autoEnable.autoDisableLatchAtTarget` | Keep the auto-disable timer active after AtTarget has been asserted once | optional |
| `axis.autoEnable.atStartup` | Auto enable axis at ioc start, default False | optional |
| `axis.tweakDist` | Tweak value (both ecmc interface and motor record tweak value) | optional |
| `epics.name` | Axis name | required |
| `epics.precision` | Decimal count | optional |
| `epics.description` | Axis description | optional |
| `epics.unit` | Unit | optional |
| `epics.motorRecord.enable` | Enable motor record | optional |
| `epics.motorRecord.description` | This is MR | optional |
| `epics.motorRecord.fieldInit` | Extra config for motor record | optional |
| `epics.motorRecord.syncSoftLimits` | Sync softlimits between motor and ecmc (default false; `restoreMotorSoftLims=1` overrides this to enabled). When synchronization is disabled, motor record HLM/LLM and ecmc soft limits may differ. On false->true, ecmc soft limits are copied to the motor record; while true, later motor record soft-limit changes are written back to ecmc. | optional |
| `epics.motorRecord.pvt.npoints` | Max number of target points for PVT/profile move | optional |
| `epics.motorRecord.pvt.nreadback` | Max number of readback points for PVT/profile move | optional |
| `drive.numerator` | Fastest speed in engineering units | required |
| `drive.denominator` | I/O range for ECMC_EC_ALIAS_DRV_VELO_SET | required |
| `drive.type` | Stepper: 0. DS402: 1 (DS402 = servos and advanced stepper drives) | required |
| `drive.control` | Control word EtherCAT entry | required |
| `drive.enable` | Enable bit index in control word (not used if DS402) | required for non-DS402 |
| `drive.enabled` | Enabled bit index in status word (not used if DS402) | required for non-DS402 |
| `drive.status` | Status word EtherCAT entry | required |
| `drive.setpoint` | Velocity setpoint if CSV. Position setpoint if CSP. `F32`/`F64` CSV setpoints are supported; `F32`/`F64` CSP setpoints require the selected CSP encoder actual-position entry to use the same datatype. | required |
| `drive.reduceTorque` | Reduce torque bit in drive control word | optional |
| `drive.reduceTorqueEnable` | Enable reduce torque functionality | optional |
| `drive.brake.enable` | Enable brake control. | optional |
| `drive.brake.output` | EtherCAT link to brake output | optional |
| `drive.brake.openDelay` | Brake timing parameter in cycles (default 1kHz) | optional |
| `drive.brake.closeAhead` | Brake timing parameter in cycles (default 1kHz) | optional |
| `drive.reset` | Reset (if no drive reset bit then leave empty) | optional |
| `drive.warning` | Warning (if no drive warning bit then leave empty) | optional |
| `drive.error[2]` | Error 2 (if no drive error bit then leave empty) | required |
| `drive.error[1]` | Error 1 (if no drive error bit then leave empty) | required |
| `drive.error[0]` | Error 0 (if no drive error bit then leave empty) | required |
| `encoder.numerator` | Scaling numerator example 360 deg/rev | required |
| `encoder.denominator` | Scaling denominator example 4096 ticks per 360 degree | required |
| `encoder.type` | Type: 0=Incremental, 1=Absolute | required |
| `encoder.bits` | Bit count used for ecmc's encoder value; does not alter the raw EtherCAT slave value | required |
| `encoder.absBits` | Absolute bit count (for absolute encoders) always least significant part of 'bits' | required |
| `encoder.absOffset` | Encoder offset in eng units (for absolute encoders) | required |
| `encoder.mask` | Mask applied to ecmc's encoder value; the original EtherCAT value remains visible in the hardware PVs | optional |
| `encoder.position` | EtherCAT entry for actual position input (encoder). `F32`/`F64` actual-position entries are only valid for absolute encoders (`encoder.type: 1`). Keep `encoder.bits` and `encoder.absBits` aligned with the datatype width (`32`/`32` or `64`/`64`). | required |
| `encoder.control` | Mandatory only if 'reset' is used | optional; required if reset is used |
| `encoder.status` | Mandatory only if 'warning' or 'error' are used | optional; required if warning/error are used |
| `encoder.ready` | Bit in encoder status word for encoder ready | optional |
| `encoder.source` | 0 = Encoder value from EtherCAT hardware, 1 = Encoder value from PLC | optional |
| `encoder.reset` | Reset | optional |
| `encoder.warning` | Warning | optional |
| `encoder.filter.velocity.size` | Filter size for velocity | optional |
| `encoder.filter.velocity.enable` | enable velocity filter | optional |
| `encoder.filter.position.size` | Filter size for encoder value | optional |
| `encoder.filter.position.enable` | enable encoder value filter | optional |
| `encoder.latch.position` | Link to latched value. Used for some homing seqs | optional |
| `encoder.latch.timestamp` | Optional 32/64-bit DC timestamp for the same latch event | optional |
| `encoder.latch.control` | Bit in encoder control word to arm latch. Used for some homing seqs | optional |
| `encoder.latch.status` | Bit in encoder status word for latch triggered status. Used for some homing seqs | optional |
| `encoder.latch.armCmd` | Value in dec to arm latch to write to encoder.control | optional |
| `encoder.latch.armBits` | Bit size of encoder.latch.armCmd | optional |
| `encoder.touchProbe.position` | Link to touch-probe latched position. Used for touch-probe functionality separate from homing latch. | optional |
| `encoder.touchProbe.timestamp` | Optional 32/64-bit DC timestamp for the same touch-probe edge | optional |
| `encoder.touchProbe.control` | Touch-probe control word entry | optional |
| `encoder.touchProbe.controlBit` | First bit in touch-probe control word to write `armBits` bits from `armCmd`; default 0 | optional |
| `encoder.touchProbe.status` | Touch-probe status word entry | optional |
| `encoder.touchProbe.statusBit` | Status bit for captured touch-probe event; default 0 | optional |
| `encoder.touchProbe.armCmd` | Value in dec to arm touch probe; default 17 for EL7062/ED7062 TP1 positive edge | optional |
| `encoder.touchProbe.armBits` | Bit size of encoder.touchProbe.armCmd; default 5 | optional |
| `encoder.primary` | Use this encoder as primary (for control) | optional |
| `encoder.useAsCSPDrvEnc` | Use this encoder as CSP drive encoder (ecmc controller enabled in CSP) | optional |
| `encoder.allowOverUnderFlow` | Allow over/under flow of encoder raw counter (default true). Set to false for linear encoders. | optional |
| `encoder.homing.type` | Homing sequence type | optional |
| `encoder.homing.position` | Position to reference encoder to | optional |
| `encoder.homing.velocity.to` | Velocity to cam/sensor (used for some homing seqs) | optional |
| `encoder.homing.velocity.from` | Velocity from cam/sensor (used for some homing seqs) | optional |
| `encoder.homing.acceleration` | Acceleration during homing | optional |
| `encoder.homing.deceleration` | Deceleration during homing | optional |
| `encoder.homing.refToEncIDAtStartup` | At startup then set the start value of this encoder to actpos of this encoder id | optional |
| `encoder.homing.refAtHome` | If homing is executed then set position of this encoder | optional |
| `encoder.homing.tolToPrim` | If set then this is the max allowed tolerance between prim encoder and this encoder | optional |
| `encoder.homing.postMoveEnable` | Enable move after successful homing | optional |
| `encoder.homing.postMovePosition` | Position to move to after successful homing | optional |
| `encoder.homing.trigg` | EtherCAT entry for triggering drive internal homing seq (seq id 26) | optional |
| `encoder.homing.ready` | EtherCAT entry for reading drive internal homing seq ready (seq id 26) | optional |
| `encoder.homing.latchCount` | latch number to reference on (1=ref on first latch) | optional |
| `encoder.delayComp.time` | Delay time between set and act [cycles] | optional |
| `encoder.delayComp.enable` | enable (defaults to 1 if not set) | optional |
| `encoder.lookuptable.filename` | Load correction lookup table file. Value will be subtracted from encoder value. | optional |
| `encoder.lookuptable.enable` | Enable correction table (default enabled if loaded). | optional |
| `encoder.lookuptable.scale` | Scale applied to LUT (if you want value to be added then set scale to -1.0) | optional |
| `encoder.lookuptable.range` | LUT modulo value (LUT should cover the range 0..range) | optional |
| `encoder.error[1]` | Error 1 | optional |
| `encoder.error[2]` | Error 2 | optional |
| `encoder.error[0]` | Error 0 | optional |
| `controller.Kp` | Kp proportional gain | required |
| `controller.Ki` | Ki integral gain | optional |
| `controller.Kd` | Kd derivative gain | optional |
| `controller.Kff` | Feed forward gain | optional |
| `controller.resetIAtRmp` | Reset the integral part to zero while an internal trajectory is busy. Reset takes precedence over freeze. | optional |
| `controller.freezeIAtRmp` | Keep the current integral part unchanged while an internal trajectory is busy. | optional |
| `controller.deadband.tol` | Stop control if within this distance from target for the below time | optional |
| `controller.deadband.time` | Deadband time filter | optional |
| `controller.limits.minOutput` | Minimum controller output. Output limiting is active only when `maxOutput > minOutput`; `minOutput=0` and `maxOutput=0` disables it. | optional |
| `controller.limits.maxOutput` | Maximum controller output. Output limiting is active only when `maxOutput > minOutput`; `minOutput=0` and `maxOutput=0` disables it. | optional |
| `controller.limits.minIntegral` | Minimum integral output. Integral limiting is active only when `maxIntegral > minIntegral`; `minIntegral=0` and `maxIntegral=0` disables it. | optional |
| `controller.limits.maxIntegral` | Maximum integral output. Integral limiting is active only when `maxIntegral > minIntegral`; `minIntegral=0` and `maxIntegral=0` disables it. | optional |
| `controller.inner.Kp` | Kp for when close to target | optional |
| `controller.inner.Ki` | Ki for when close to target | optional |
| `controller.inner.Kd` | Kd for when close to target | optional |
| `controller.inner.tol` | Distance from target for when inner PID params will be used, defaults to atTarget tol | optional |
| `trajectory.type` | Default 0 = trapezoidal, 1 = S-curve (ruckig) | optional |
| `trajectory.source` | 0 = take trajectory setpoint from axis traj object, 1 = trajectory setpoint from plc | optional |
| `trajectory.axis.velocity` | Default velocity for axis | required |
| `trajectory.axis.acceleration` | Default acceleration for axis | required |
| `trajectory.axis.deceleration` | Default deceleration for axis | optional |
| `trajectory.axis.emergencyDeceleration` | Deceleration when axis in error state | optional |
| `trajectory.axis.jerk` | Default jerk for axis | optional |
| `trajectory.jog.velocity` | Default velocity for JOG (motor record) | optional |
| `trajectory.modulo.range` | Modulo range 0..360 | optional |
| `trajectory.modulo.type` | Modulo type | optional |
| `positionCompare.output` | EtherCAT output entry to schedule, for example an EL2252 binary output | required |
| `positionCompare.activate` | EtherCAT activation/control entry used by the timed-output terminal | required |
| `positionCompare.startTime` | EtherCAT DC start-time entry; use a 64-bit integer entry/PV for EL2252 | required |
| `positionCompare.minLeadMs` | Minimum scheduling lead time [ms], default 2.0 | optional |
| `positionCompare.maxLeadMs` | Maximum scheduling lead time [ms], default 100.0 | optional |
| `positionCompare.activateIdle` | Activation value written while idle, default 3 for EL2252 | optional |
| `positionCompare.activateSchedule` | Activation value written for one cycle to load a schedule, default 0 for EL2252 | optional |
| `positionCompare.pulseWidthMs` | Optional automatic reset pulse width [ms], default 0. Fractions such as 0.5 are allowed. | optional |
| `positionCompare.resetValue` | Output value for automatic reset after pulseWidthMs, default 0 | optional |
| `input.limit.forward` | EtherCAT entry for low limit switch input | required |
| `input.limit.forwardPolarity` | Polarity of forward limit switch | required |
| `input.limit.backward` | EtherCAT entry for high limit switch input | required |
| `input.limit.backwardPolarity` | Polarity of backward limit switch | required |
| `input.home` | EtherCAT entry for home switch | required |
| `input.homePolarity` | Polarity of home switch | required |
| `input.interlock` | EtherCAT entry for interlock switch input | required |
| `input.interlockPolarity` | Polarity of interlock switch | required |
| `input.analog.interlock` | EtherCAT entry for analog interlock | optional |
| `input.analog.interlockPolarity` | 0: High value is bad, 1 = Low value is bad | optional |
| `input.analog.rawLimit` | Analog raw limit | optional |
| `input.analog.enable` | Enable analog interlock default true if analog.interlock is set | optional |
| `softlimits.enable` | Enable soft limits | optional |
| `softlimits.forward` | Soft limit position fwd | optional |
| `softlimits.forwardEnable` | Soft limit position fwd enable | optional |
| `softlimits.backward` | Soft limit position bwd | optional |
| `softlimits.backwardEnable` | Soft limit position bwd enable | optional |
| `monitoring.lag.enable` | Enable position lag monitoring (following error) | optional |
| `monitoring.lag.tolerance` | Allowed tolerance | optional |
| `monitoring.lag.time` | Allowed time outside tolerance | optional |
| `monitoring.target.enable` | Enable at target monitoring (needs to be enabled and configured if using motor record) | optional |
| `monitoring.target.tolerance` | Allowed tolerance | optional |
| `monitoring.target.time` | Filter time inside tolerance to be at target | optional |
| `monitoring.target.slaveControlDeadband.tolerance` | Master-axis tolerance forwarded to slaves for reduced-torque control; defaults to AtTarget tolerance | optional |
| `monitoring.target.slaveControlDeadband.time` | Filter time inside slave-control deadband; defaults to AtTarget time | optional |
| `monitoring.velocity.enable` | Enable velocity monitoring | optional |
| `monitoring.velocity.max` | Allowed max velocity | optional |
| `monitoring.velocity.time.trajectory` | Time allowed outside max velocity before system init halt | optional |
| `monitoring.velocity.time.drive` | Time allowed outside max velocity before system disables drive | optional |
| `monitoring.velocityDifference.enable` | Enable velocity difference monitoring (velocity set vs velocity actual) | optional |
| `monitoring.velocityDifference.max` | Allowed max difference | optional |
| `monitoring.velocityDifference.time.trajectory` | Time allowed outside max diff velo before system init halt | optional |
| `monitoring.velocityDifference.time.drive` | Time allowed outside max diff velo before system disables drive | optional |
| `monitoring.stall.enable` | Enable stall monitoring. At target must be enabled for this functionality | optional |
| `monitoring.stall.time.timeout` | If not at target after "timeout" cycles after trajectory generator is ready then drive will disable | optional |
| `monitoring.stall.time.factor` | Measures duration of last motion command (busy high edge to busy low edge). The new timeout will be defined as this duration multiplied by this factor. The timeout finally used for stall detection will be the longest (of time.timeout and calculated from time.factor). | optional |
| `plc.enable` | Enable axis plc | optional |
| `plc.externalCommands` | Allow axis input from PLC | optional |
| `plc.file` | File with plc code | optional |
| `plc.code[0]` | Enable axis if one of master axes is enabled | optional |
| `plc.code[1]` | Calculate set position for physical axis | optional |
| `plc.velocity_filter.encoder.enable` | Filter enable | optional |
| `plc.velocity_filter.encoder.size` | Filter size | optional |
| `plc.velocity_filter.trajectory.enable` | Filter enable | optional |
| `plc.velocity_filter.trajectory.size` | Filter size | optional |
| `plc.filter.velocity.enable` | Filter enable | optional; deprecated alias |
| `plc.filter.velocity.size` | Filter size | optional; deprecated alias |
| `plc.filter.trajectory.enable` | Filter enable | optional; deprecated alias |
| `plc.filter.trajectory.size` | Filter size | optional; deprecated alias |

<!-- END GENERATED AXIS YAML REFERENCE -->
