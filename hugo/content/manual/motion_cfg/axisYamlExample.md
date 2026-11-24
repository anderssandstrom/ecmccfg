+++
title = "Complete axis YAML example"
slug = "axisyaml-example"
weight = 18
chapter = false
+++

This annotated example collects the available settings in one place. Adapt the
hardware entries, macros, values, and enabled features to your configuration.
Use the [axis YAML configuration guide]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
for explanations and the [settings reference]({{< relref "/manual/motion_cfg/axisYamlSettingsTable.md" >}})
for key lookup. This example includes optional and alternative settings; it is
not a minimal configuration to run unchanged.

**Reading the example:** uncommented settings form the recommended baseline for a
physical axis with EtherCAT feedback and an EPICS motor record. This includes
loader-required fields, explicit hardware scaling/type/bit count, axis identity
and target monitoring needed for reliable motor-record completion. Optional
settings and optional feature blocks are commented out, even when the example
value equals the default. Uncomment the relevant block and its required children
together. Inline `default:` notes describe omission behavior where documented;
other displayed values are examples, not defaults. Verify all hardware links,
limit polarity, scaling and monitoring before enabling motion. Do not use this
illustration directly as a commissioned configuration.

The example uses the Python loader's boolean syntax for `monitoring.stall.enable`.
With ECB, change that value to integer `1` (or `0` to disable): the current ECB
schema uses an integer for this field while the Python schema uses a boolean.

## All YAML settings
```yaml
axis:
  id: 1                                                         # Axis id; default: next id from ECMC_AXIS_NO; explicit recommended baseline
  type: joint                                                   # physical axis (1); virtual/end_effector is 2; default: joint; explicit recommended baseline
  mode: CSV                                                     # CSV, CSP or CSP_PC; default CSV; explicit recommended baseline
#  parameters: ''                                               # Optional semicolon-terminated motor driver options
                                                                # "powerAutoOnOff=<value>;"  # Legacy motor-record auto-power: 2 for automatic, 0 to disable; prefer axis.autoEnable
                                                                # "powerOffDelay=<value>;"
                                                                # "powerOnDelay=<value>;"
#  healthOutput: ec0...                                         # EtherCAT entry for health output
#  feedSwitchesOutput: ec0...                                   # EtherCAT entry for fed switches
#  feedSwitchesValue: 1                                         # Value to write to axis.feedSwitchesOutput. Defaults to 1; default: 1
#  group: testGroup                                             # Add axis to group (group will be created if it does not exist),
                                                                # group id will be stored in GRP_<axis.group>_ID for later use.
#  autoMode:                                                    # Switch drive modes automatically for normal motion and homing (smaract for instance)
#    modeSet: ec0..                                             # EtherCAT entry drive mode write (set CSV,CSP,homing)
#    modeAct: ec0..                                             # EtherCAT entry drive mode reading (set CSV,CSP,homing)
#    modeCmdMotion: 9                                           # Drive-specific normal-motion mode (CiA 402 CSV = 9)
#    modeCmdHome: 6                                             # Drive-specific homing mode (CiA 402 homing = 6; check device)
#  features:
#    blockCom: false                                            # Block communication to axis
#    allowSrcChangeWhenEnabled: false                           # Allow traj/enc source change when axis is enabled
#    disableOnReset: false                                      # Disable the axis when an error is reset
#    alarmAtHardLimits: false                                   # Raise an axis error when a hard limit activates
#    allowedFunctions:
#      homing: true                                             # Allow homing
#      constantVelocity: true                                   # Allow constant velocity
#      positioning: true                                        # Allow positioning
  # Prefer native ECMC auto-enable/disable over motor-record auto-power settings.
#  autoEnable:                                                  # Automatic drive enabling and disabling
#    enableTimeout: 5.0                                         # If defined, ecmc tries to auto-enable for a maximum enableTimeout seconds.; default: -1.0
#    disableTimeout:   5.0                                      # If defined, ecmc disables axis after the configured idle timeout in seconds; default: -1.0
#    autoDisableLatchAtTarget: false                            # Continue auto-disable timing after AtTarget has been reached once; default: false
#    atStartup: True                                            # Auto enable axis at ioc start, default False
#  tweakDist: 2.0                                               # Tweak value (both ecmc interface and motor record tweak value); default: 1.0

epics:
  name: M1                                                      # Axis name; default: axis; explicit recommended baseline
#  precision: 3                                                 # Decimal count; default: 3
#  description: very important motor axis                       # Axis description
#  unit: mm                                                     # Unit; default: mm
#  motorRecord:
#    enable: true                                               # Create an EPICS motor record (default true)
#    description: This is MR                                    # Motor record description
    # Extra config for Motor record
#    fieldInit: 'RRES=1.0,RTRY=2,RMOD=1,UEIP=0,RDBD=0.1,URIP=1,RDBL=$(IOC):$(ECMC_MOTOR_NAME)-PosActSim'
#    syncSoftLimits: false                                      # Optional: Sync softlimits between motor and ecmc (default false).
                                                                # On false->true, ecmc soft limits are copied to the motor record.
                                                                # While true, later motor record soft-limit changes are written back to ecmc.
#    restoreSoftLimits: false                                   # Startup-only: restore motor dial limits DLLM/DHLM; syncSoftLimits decides whether they also replace ECMC limits; default: false
#    pvt:
#      npoints: 1000                                            # Maximum PVT target points; default: 0
#      nreadback: 1000                                          # Maximum PVT readback points; default: 0

drive:
  numerator: 360                                                # Engineering-unit scaling numerator (velocity in CSV, position in CSP); default: 0; explicit recommended baseline
  denominator: 4096                                             # Raw drive-unit scaling denominator; scale = numerator / denominator; default: 1; explicit recommended baseline
  type: 0                                                       # 0: simple bit-controlled drive; 1: CiA 402 drive; default: 0; explicit recommended baseline
  control: ec0.s$(DRV_SLAVE).driveControl01                     # Control word EtherCAT entry
#  enable: 0                                                    # Enable bit index in control word (not used if DS402); default: 0
#  enabled: 1                                                   # Enabled bit index in status word (not used if DS402); default: 1
  status: ec0.s$(DRV_SLAVE).driveStatus01                       # Status word EtherCAT entry
  setpoint: ec0.s$(DRV_SLAVE).velocitySetpoint01                # Velocity setpoint if CSV. Position setpoint if CSP
#  reduceTorque: 2                                              # Reduce torque bit in drive control word
#  reduceTorqueEnable: True                                     # Enable reduce torque functionality
#  brake:
#    enable: false
#    output: ec0...                                             # Ethercat link to brake output
#    openDelay: 0                                               # Brake timing in EtherCAT cycles; default 0
#    closeAhead: 0                                              # Brake timing in EtherCAT cycles; default 0
#  reset: 1                                                     # Reset bit; omit key if unused
#  warning: 2                                                   # Warning bit; omit key if unused
#  error:                                                       # max 3
#    - 3                                                        # Error bit 0; omit unused list items
#    - 7                                                        # Error bit 1
#    - 14                                                       # Error bit 2
  # Optional position-dependent CSV drive-output compensation (not encoder correction).
#  lookuptable:
#    filename: ./cfg/drive.corr                                 # Compensation table file
#    enable: true                                               # Enable compensation
#    scale: 1.0                                                 # Scale or invert compensation
#    range: 360.0                                               # Optional modulo range [axis engineering units]

encoder:
  numerator: 360                                                # Scaling numerator example 360 deg/rev; default: 0.0; explicit recommended baseline
  denominator: 4096                                             # Scaling denominator example 4096 ticks per 360 degree; default: 1; explicit recommended baseline
  type: 0                                                       # Type: 0=Incremental, 1=Absolute; default: 0; explicit recommended baseline
  bits: 16                                                      # Total bit count of encoder raw data; default: 16; explicit recommended baseline
#  absBits: 0                                                   # Absolute bit count (for absolute encoders) always least significant part of 'bits'; default: 25
#  absOffset: 0                                                 # Encoder offset in eng units (for absolute encoders); default: 0.0
#  mask: '0xFFF00'                                              # Select raw encoder position bits; match mask and bit count to hardware
  position: ec0.s$(ENC_SLAVE).positionActual01                  # EtherCAT entry for actual position input (encoder)
#  control: ec0.s$(ENC_SLAVE).encoderControl01                  # Control word required for reset or control-word-based latch
#  status: ec0.s$(ENC_SLAVE).encoderStatus01                    # Required for ready, warning, error or status-word-based latch
#  ready: 10                                                    # Bit in encoder status word for encoder ready
#  source: 0                                                    # 0 = Encoder value from EtherCAT hardware, 1 = Encoder value from PLC; default: 0
#  reset: 1                                                     # Reset   (optional)
#  warning: 2                                                   # Warning (optional)
#  error:                                                       # max 3 (optional)
#    - 5                                                        # Error 0
#    - 9                                                        # Error 1
#    - 11                                                       # Error 2
#  filter:
#    velocity:
#      size: 100                                                # Velocity filter window in EtherCAT samples; default: 100
#      enable: true                                             # Enable encoder velocity filter; default: true
#    position:
#      size: 100                                                # Position filter window in EtherCAT samples (default 10)
#      enable: true                                             # Enable encoder position filter; default: true
#  latch:
#    position: ''                                               # Link to latched value. Used for some homing seqs
#    timestamp: ''                                              # Optional 32/64-bit DC timestamp for the same latch event
#    control: 0                                                 # Bit in encoder control word to arm latch. Used for some homing seqs; default: 0
#    status: 0                                                  # Bit in encoder status word for latch triggered status. Used for some homing seqs; default: 0
#    armCmd: 1                                                  # Value written to encoder.control; default 1
#    armBits: 1                                                 # Bit length of armCmd; default 1
#  touchProbe:                                                  # Optional touch-probe mapping, separate from homing latch
#    position: ec0.s$(ENC_SLAVE).touchProbePositionPos01_1      # Latched touch-probe position
#    timestamp: ec0.s$(ENC_SLAVE).touchProbeTimestampPos01_1    # Optional 32/64-bit DC timestamp for same edge
#    control: ec0.s$(ENC_SLAVE).touchProbeControl01             # Touch-probe control word
#    controlBit: 0                                              # First control bit to write; default: 0
#    status: ec0.s$(ENC_SLAVE).touchProbeStatus01               # Touch-probe status word
#    statusBit: 0                                               # Captured-event status bit; default: 0
#    armCmd: 17                                                 # EL7062/ED7062 TP1 positive-edge arm command; default: 17
#    armBits: 5                                                 # Number of bits written from armCmd; default: 5
#  primary: True                                                # Use this encoder as primary (for control)
#  useAsCSPDrvEnc: True                                         # Select encoder used for CSP drive position mapping (especially CSP_PC)
#  unit: mm                                                     # Optional encoder engineering unit
#  desc: Main encoder                                           # Optional encoder description
#  allowOverUnderFlow: True                                     # Allow over/under flow of encoder raw counter (default true). Set to false for linear encoders.
#  homing:
#    type: 3                                                    # Homing sequence type
#    position: -30                                              # Position to reference encoder to
#    velocity:
#      to: 10                                                   # Velocity to cam/sensor (used for some homing seqs)
#      from: 5                                                  # Velocity from cam/sensor (used for some homing seqs)
#    acceleration: 20                                           # Acceleration during homing
#    deceleration: 100                                          # Deceleration during homing
#    refToEncIDAtStartup: 1                                     # Reference this encoder at startup to the actual position of the specified encoder ID
#    refAtHome: 1                                               # If homing is executed then set position of this encoder
#    tolToPrim: 0                                               # If set then this is the max allowed tolerance between prim encoder and this encoder
#    postMoveEnable: true                                       # Enable move after successful homing
#    postMovePosition: 10                                       # Position to move to after successful homing
#    trigg: ec0..                                               # EtherCAT entry for triggering drive internal homing seq (seq id 26)
#    ready: ec0..                                               # EtherCAT entry for reading drive internal homing seq ready (seq id 26)
#    latchCount: 1                                              # Latch number to reference on (1 = first latch)
#    timeout: 30                                                # Homing sequence timeout [s]
#  delayComp:                                                   # Delay compensation for time between application of setpoint to reading of encoder (normally at least 1 cycle)
#    time: 1.5                                                  # Delay time between set and act [cycles]
#    enable: true                                               # enable (defaults to 1 if not set)
#  lookuptable:                                                 # Lookup tables are only applied when encoder is homed
#    filename: ./cfg/enc.corr                                   # Load correction lookup table file. Value will be subtracted from encoder value.
#    enable: true                                               # Enable correction table (default enabled if loaded).
#    scale: 1                                                   # Scale applied to LUT (if you want value to be added then set scale to -1.0)
#    range: 360                                                 # LUT modulo value (Lut should cover the range 0..range)
#  power:                                                       # Optional relay-controlled absolute encoder power
#    enable: false
#    output: ec0.s$(PWR_SLAVE).binaryOutput01
#    activeHigh: true
#    idleDelay: 5.0                                             # Continuous at-target / required deadband dwell before power-off [s]
#    startupDelay: 0.5                                          # Minimum encoder warm-up time after power-on [s]
#    startupTimeout: 5.0                                        # Maximum wake-up time [s]; must exceed startupDelay
#    backup:
#      encoder: 1                                               # Always-powered incremental backup encoder index (1–8)
#      maxPositionDifference: 0.1                               # Maximum accepted wake-up position difference [engineering units]

#controller:
#  Kp: 1                                                        # Kp proportional gain; default: 1
#  Ki: 0.001                                                    # Ki integral gain; default: 0
#  Kd: 0                                                        # Kd derivative gain; default: 0
#  Kff: 1                                                       # Feed forward gain; default: 1
#  resetIAtRmp: false                                           # Reset I-part while an internal trajectory is busy; default: no command if omitted
#  freezeIAtRmp: false                                          # Freeze I-part while an internal trajectory is busy; default: no command if omitted
#  deadband:
#    tol: 0.01                                                  # Stop control if within this distance from target for the below time
#    time: 100                                                  # Time inside controller deadband [EtherCAT cycles]
#  limits:
#    minOutput: -100                                            # Minimum controller output
#    maxOutput: 100                                             # Maximum controller output
#    minIntegral: -100                                          # Minimum integral output
#    maxIntegral: 100                                           # Maximum integral output
#  inner:
#    Kp: 0.1                                                    # Kp for when close to target; default: 1.0
#    Ki: 0.1                                                    # Ki for when close to target; default: 0
#    Kd: 0.1                                                    # Kd for when close to target; default: 0
#    tol: 0.1                                                   # Distance band for inner PID; schema default 0

trajectory:
#  type: 1                                                      # Default 0 = trapezoidal, 1 = S-curve (ruckig)
#  source: 0                                                    # 0 = take trajectory setpoint from axis traj object, 1 = trajectory setpoint from plc; default: 0
  axis:
    velocity: 10                                                # Default velo for axis
    acceleration: 0.1                                           # Default acc for axis
#    deceleration: 0.1                                          # Default dec for axis
#    emergencyDeceleration: 0.05                                # Deceleration when axis in error state; default: 10 × max(acceleration, deceleration)
#    jerk: 10                                                   # Default jerk for axis
#  jog:
#    velocity: 5                                                # Default velocity for JOG (motor record)
#    acceleration: 1                                            # Optional jog acceleration; default: trajectory.axis.acceleration (motor record only)
#  modulo:
#    range: 360                                                 # Modulo range 0..360; default: 0.0
#    type: 0                                                    # Modulo motion type; select the mode required by the application; default: 0

#positionCompare:                                               # Optional timed output at a position crossing
#  output: ec0.s$(OUT_SLAVE).binaryOutput01                     # Output value entry, for example EL2252 BO1
#  activate: ec0.s$(OUT_SLAVE).activate                         # Timed-output activation/control entry
#  startTime: ec0.s$(OUT_SLAVE).startTime                       # 64-bit DC start-time entry
#  minLeadMs: 2.0                                               # Minimum scheduling lead time [ms]; default: 2.0
#  maxLeadMs: 100.0                                             # Maximum scheduling lead time [ms]; default: 100.0
#  activateIdle: 3                                              # EL2252 idle/no-new-schedule value; default: 3
#  activateSchedule: 0                                          # EL2252 schedule/load value, written for one cycle; default: 0
#  pulseWidthMs: 10.0                                           # Optional auto-reset pulse width [ms], 0 disables; default: 0.0
#  resetValue: 0                                                # Output value for auto reset; default: 0

#  Limits can be overridden with plc-code by setting input.limit.forward or input.limit.backward to 'plcOverride', then 'ax<id>.mon.lowlim' and/or 'ax<id>.mon.highlim' needs to be written to in plc code (1 means limit OK).

input:
  limit:
    forward: ec0.s$(LIMIT_SLAVE).binaryInputs01.0               # Example forward (high) limit switch input; verify actual wiring
#    forwardPolarity: 0                                         # Polarity of forward limit switch
    backward: ec0.s$(LIMIT_SLAVE).binaryInputs01.1              # Example backward (low) limit switch input; verify actual wiring
#    backwardPolarity: 0                                        # Polarity of backward limit switch
#    latchInput: false                                          # Latch limit input activation when supported
#  home: 'ec0.s$(MCS2_SLAVE_NUM).ONE.0'                         # EtherCAT entry for home switch
#  homePolarity: 0                                              # Polarity of home switch
#  interlock: 'ec0.s$(ENC_SLAVE).ONE.0'                         # EtherCAT entry for interlock switch input
#  interlockPolarity: 0                                         # Polarity of interlock switch
#  analog:
#    interlock: 'ec0.s$(ENC_SLAVE).ONE'                         # EtherCAT entry for analog interlock
#    interlockPolarity: 1                                       # 0: High value is bad, 1 = Low value is bad
#    rawLimit: 2000                                             # Analog raw limit
#    enable: true                                               # Enable analog interlock default true if analog.interlock is set

#softlimits:
#  enable: false                                                # Enable soft limits; default: Python: not supplied; ECB: false
#  forward: 100                                                 # Soft limit position fwd
#  forwardEnable: false                                         # Enable forward soft limit
#  backward: -100                                               # Soft limit position bwd
#  backwardEnable: false                                        # Enable backward soft limit

monitoring:
#  lag:
#    enable: false                                              # Enable position lag monitoring (following error); default: false when lag block omitted
#    tolerance: 0.5                                             # Allowed tolerance; default: 0 when lag block omitted
#    time: 10                                                   # Allowed time outside tolerance [cycles]; default: 100 when lag block omitted
  target:
    enable: true                                                # Enable at target monitoring (needs to be enabled and configured if using motor record); default: Python: required in block; ECB: false; explicit recommended baseline
    tolerance: 0.5                                              # Allowed tolerance; explicit recommended baseline
    time: 10                                                    # Filter time inside tolerance to be at target [cycles]; explicit recommended baseline
#    slaveControlDeadband:                                      # Optional independent master-axis band forwarded to slaves
#      tolerance: 0.01                                          # Master error tolerance for slave control decisions; default: monitoring.target.tolerance (ecmc)
#      time: 100                                                # Qualification time inside tolerance [cycles]; default: monitoring.target.time (ecmc)
#  velocity:
#    enable: false                                              # Enable velocity monitoring; default: Python: required in block; ECB: false
#    max: 100                                                   # Allowed max velocity
#    time:
#      trajectory: 100                                          # Time allowed outside max velo before trajectory halt [cycles]
#      drive: 200                                               # Time allowed outside max velo before system disables drive [cycles]
#  velocityDifference:
#    enable: true                                               # Enable velocity diff monitoring (velo set vs velo act); default: Python: required in block; ECB: false
#    max: 100                                                   # Allowed max difference
#    time:
#      trajectory: 100                                          # Time allowed outside max diff velo before system init halt [cycles]
#      drive: 200                                               # Time allowed outside max diff velo before system disables drive [cycles]
#  stall:
#    enable: True                                               # Enable stall monitoring. At target must be enabled for this functionality
#    time:
#      timeout: 10000                                           # If not at target after "timeout" cycles after trajectory generator is ready then drive will disable
#      factor: 5.0                                              # Measures duration of last motion command (busy high edge to busy low edge). The new timeout will be defined as this duration multiplied by this factor. The timeout finally used for stall detection will be the longest (of time.timeout and calculated from time.factor).

#plc:
#  enable: true                                                 # Enable axis plc
#  externalCommands: true                                       # Allow PLC to influence axis commands and setpoints (default false)
#  file: myplcfile.plc                                          # File with plc code
#  macros: 'MY_MACRO=1'                                         # Optional macros passed while loading plc.file
#  code:                                                        # Sync code (appended after code in plc.file)
    # Enable axis if one of master axes is enabled
#    - if(ax2.traj.source){ax2.drv.enable:=(ax10.drv.enable or ax11.drv.enable)};
#    - ax2.traj.setpos:=ax10.traj.setpos-ax11.traj.setpos/2;    # calculate set pos for physical axis
#  velocity_filter:                                             # Preferred filters for PLC-derived velocity feedforward
#    encoder:                                                   # Filter velocity derived from external encoder position
#      enable: false                                            # Filter enable; default: false
#      size: 100                                                # Filter size; default: 1
#    trajectory:                                                # Filter velocity derived from external trajectory position
#      enable: false                                            # Filter enable; default: false
#      size: 100                                                # Filter size; default: 1
#  filter:                                                      # Use "velocity_filter" instead since this naming is misleading and should be phased out
#    velocity:                                                  # Filter plc enc velo
#      enable: false
#      size: 100
#    trajectory:                                                # Filter plc traj velo
#      enable: false
#      size: 100
#    position:                                                  # Legacy filter option
#      enable: false
#      size: 100

```

## Compatibility and alternative settings

Prefer the nested `encoder.homing` and `encoder.touchProbe` blocks shown above. Top-level `homing` and `touchProbe` are alternative forms; see the [settings reference]({{< relref "/manual/motion_cfg/axisYamlSettingsTable.md" >}}) and do not configure competing mappings for the same function.

Use `encoder.filter.position` rather than the deprecated alias `encoder.filter.trajectory` (same `enable` and `size` keys). The older flat keys `encoder.velocityFilterSize`, `encoder.positionFilterSize` and `encoder.positionFilterEnable` are not effective filter configuration: Python discards them, while ECB still accepts them in its schema. Use the nested filter blocks instead.
