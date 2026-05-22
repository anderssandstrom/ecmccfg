+++
title = "homing"
weight = 21
chapter = false
+++

# homing

## Start here

Use this page when you need to choose or understand a homing sequence.

For new configurations:

- prefer YAML-based homing configuration under `encoder.homing`
- use this page to choose the homing sequence type and supporting encoder or
  switch wiring
- start from a best-practice example when possible

Legacy `epicsEnvSet(...)` examples are still shown in some sections because many
older IOCs still use them, but YAML is preferred for new setups.

## Common choices

The most common homing cases are:

- trusted absolute encoder, no active homing move:
  sequence `0`
- limit switch plus home switch:
  sequence `3` or `4`
- index homing with EL5101 / EL5102 latch objects:
  sequence `11` or `12`
- index homing with EL7062 touch probe:
  sequence `11` or `12`
- drive-internal homing triggered by ecmc:
  sequence `26`
- custom homing implemented in PLC or C++ logic:
  sequence `27`
- absolute encoder with one overflow in range:
  see the dedicated section later on this page

## Before choosing a sequence

- verify whether the drive is in `CSV`, `CSP`, or a special homing mode
- verify whether home and limit signals are wired into EtherCAT or handled in
  the drive
- verify whether index reference uses encoder latch PDOs or touch-probe PDOs
- decide whether a post-move after homing is needed

This page describes the homing sequences supported by ecmc.
The following sequences are available:

```c
ECMC_SEQ_HOME_NOT_VALID                = 0,
ECMC_SEQ_HOME_LOW_LIM                  = 1,
ECMC_SEQ_HOME_HIGH_LIM                 = 2,
ECMC_SEQ_HOME_LOW_LIM_HOME             = 3,
ECMC_SEQ_HOME_HIGH_LIM_HOME            = 4,
ECMC_SEQ_HOME_LOW_LIM_HOME_HOME        = 5,
ECMC_SEQ_HOME_HIGH_LIM_HOME_HOME       = 6,
ECMC_SEQ_HOME_BWD_HOME                 = 7,
ECMC_SEQ_HOME_FWD_HOME                 = 8,
ECMC_SEQ_HOME_BWD_HOME_HOME            = 9,
ECMC_SEQ_HOME_FWD_HOME_HOME            = 10,
ECMC_SEQ_HOME_LOW_LIM_INDEX            = 11,
ECMC_SEQ_HOME_HIGH_LIM_INDEX           = 12,
ECMC_SEQ_HOME_SET_POS                  = 15,
ECMC_SEQ_HOME_LOW_LIM_SINGLE_TURN_ABS  = 21,
ECMC_SEQ_HOME_HIGH_LIM_SINGLE_TURN_ABS = 22,
ECMC_SEQ_HOME_SET_POS_2                = 25,
ECMC_SEQ_HOME_TRIGG_EXTERN             = 26,
ECMC_SEQ_HOME_PLC                      = 27,
```

Additionally, for homing of absolute encoder with **ONE** overflow in the range, please check [here](#homing-of-absolute-encoder-with-one-overflow-in-the-range).

`ECMC_HOME_POS` is the position written when homing is finalized.
Low limit means backward limit switch. High limit means forward limit switch.
Home switch edge means a change of the home switch state, with the effective edge depending on switch polarity.

## Related pages

- [yaml configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [motion best practice]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
- [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}})

## Post move after homing

After a homing sequence has finalized the reference position, ecmc can optionally execute one absolute positioning move.
This is useful when the reference point is at a switch edge or at an index mark, but the desired final parked position is somewhere else.

If post move is enabled:
1. The homing sequence first writes the new reference position (`ECMC_HOME_POS`).
2. ecmc then issues one absolute move to the configured post-move target position.
3. The homing sequence is not considered complete until this move has finished.

If the current position already equals the configured post-move target, then no extra move is started.

Command interface:

```bash
ecmcConfigOrDie "Cfg.SetAxisHomePostMoveEnable(${ECMC_AXIS_NO}, 1)"
ecmcConfigOrDie "Cfg.SetAxisHomePostMoveTargetPosition(${ECMC_AXIS_NO}, 10.0)"
```

The same functionality is available in YAML through the homing configuration:

```yaml
homing:
  type: 3
  position: 0
  postMoveEnable: 1
  postMovePosition: 10.0
```

The post-move settings can also be stored in the encoder homing configuration and then reused when the homing sequence is read from encoder settings.

### ECMC_SEQ_HOME_NOT_VALID = 0

Not a valid homing sequence. This value can be used when no active homing sequence is required, for example with a trusted absolute encoder setup.

### ECMC_SEQ_HOME_LOW_LIM = 1

1. Move backward until the low limit switch is reached.
2. Reverse direction and move forward until the low limit switch changes state.
3. Latch the position at that limit-switch edge.
4. Stop and set the reference position so that the latched point becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_HIGH_LIM = 2

1. Move forward until the high limit switch is reached.
2. Reverse direction and move backward until the high limit switch changes state.
3. Latch the position at that limit-switch edge.
4. Stop and set the reference position so that the latched point becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_LOW_LIM_HOME = 3

1. Move backward until the low limit switch is reached.
2. Reverse direction and move forward until the home switch changes state.
3. Latch the position at that home-switch edge.
4. Stop and set the reference position so that the latched point becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_HIGH_LIM_HOME = 4

1. Move forward until the high limit switch is reached.
2. Reverse direction and move backward until the home switch changes state.
3. Latch the position at that home-switch edge.
4. Stop and set the reference position so that the latched point becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_LOW_LIM_HOME_HOME = 5

1. Move backward until the low limit switch is reached.
2. Reverse direction and move forward until the first home-switch edge is detected. Latch that position.
3. Continue forward until the second home-switch edge is detected, then stop.
4. Reverse direction and move backward until the next home-switch edge is detected. Latch that position.
5. Set the reference position so that the midpoint between the two latched positions becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_HIGH_LIM_HOME_HOME = 6

1. Move forward until the high limit switch is reached.
2. Reverse direction and move backward until the first home-switch edge is detected. Latch that position.
3. Continue backward until the second home-switch edge is detected, then stop.
4. Reverse direction and move forward until the next home-switch edge is detected. Latch that position.
5. Set the reference position so that the midpoint between the two latched positions becomes `ECMC_HOME_POS`.

### ECMC_SEQ_HOME_BWD_HOME = 7

1. Move backward until the home switch changes to the active state. Latch that position.
2. Stop.
3. Set the reference position so that the latched point becomes `ECMC_HOME_POS`.

The effective edge depends on the configured home-switch polarity.

### ECMC_SEQ_HOME_FWD_HOME = 8

1. Move forward until the home switch changes to the active state. Latch that position.
2. Stop.
3. Set the reference position so that the latched point becomes `ECMC_HOME_POS`.

The effective edge depends on the configured home-switch polarity.

### ECMC_SEQ_HOME_BWD_HOME_HOME = 9

1. Move backward until the first active home-switch edge is detected. Latch that position.
2. Continue moving backward until the home switch returns to the inactive state, then stop.
3. Reverse direction and move forward until the next active home-switch edge is detected. Latch that position.
4. Set the reference position so that the midpoint between the two latched positions becomes `ECMC_HOME_POS`.

The effective active/inactive edges depend on the configured home-switch polarity.

### ECMC_SEQ_HOME_FWD_HOME_HOME = 10

1. Move forward until the first active home-switch edge is detected. Latch that position.
2. Continue moving forward until the home switch returns to the inactive state, then stop.
3. Reverse direction and move backward until the next active home-switch edge is detected. Latch that position.
4. Set the reference position so that the midpoint between the two latched positions becomes `ECMC_HOME_POS`.

The effective active/inactive edges depend on the configured home-switch polarity.

### ECMC_SEQ_HOME_LOW_LIM_INDEX = 11

1. Move backward until the low limit switch is reached.
2. Reverse direction and move forward until the low limit switch changes state.
3. Arm the encoder latch.
4. Continue moving forward until the configured latch count is reached.
5. Stop and set the reference position so that the selected latched index position becomes `ECMC_HOME_POS`.

This sequence requires encoder latch support. `ECMC_HOME_LATCH_COUNT_OFFSET` selects which index/latch event to use.

Two common hardware patterns are used for this:

- EL51xx encoder terminals such as EL5101 and EL5102 expose dedicated encoder latch objects. In that case, `encoder.control` and `encoder.status` are the encoder latch control/status PDOs, and `encoder.latch.position` is the latched encoder position PDO.
- EL7062 does not use the EL51xx latch objects for index homing. Instead it uses the touch-probe objects, so `encoder.control` and `encoder.status` map to touch-probe control/status PDOs, and `encoder.latch.position` maps to the touch-probe latched position PDO.

Legacy `epicsEnvSet(...)` configuration still works:

```bash
epicsEnvSet("ECMC_EC_ENC_LATCHPOS",        "ec0.s3.encoderLatchPostion01") # Latch position entry
epicsEnvSet("ECMC_EC_ENC_LATCH_CONTROL",   "ec0.s3.encoderControl01.0")    # Latch arm bit
epicsEnvSet("ECMC_EC_ENC_LATCH_STATUS",    "ec0.s3.encoderStatus01.0")     # Latch occurred bit
epicsEnvSet("ECMC_HOME_LATCH_COUNT_OFFSET","2")                            # 1 = first latch, 2 = second latch, ...
```

For new configs, prefer the YAML-based encoder configuration used in the
EL7047 + EL5102 best-practice example:

YAML-based EL51xx example from the EL7047 + EL5102 best-practice config:

```yaml
encoder:
  desc: Incremental RS422
  unit: mm
  numerator: 1
  denominator: 4096
  type: 0
  bits: 32
  absBits: 0
  position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}
  status: ec0.s$(ENC_SID).encoderStatus${ENC_CH=01}
  control: ec0.s$(ENC_SID).encoderControl${ENC_CH=01}
  primary: True
  latch:
    position: ec0.s$(ENC_SID).encoderLatchPostion$(ENC_CH=01)
    control: 0
    status: 0
  homing:
    type: 11
    position: 0
    velocity:
      to: 2
      from: 1
    acceleration: 1
    deceleration: 1
    latchCount: 1
```

Latch bit mapping:

- Control word bit 0: `0x7000:01`, enable latch on index
- Status word bit 0: `0x6000:01`, latch occurred

### ECMC_SEQ_HOME_HIGH_LIM_INDEX = 12

1. Move forward until the high limit switch is reached.
2. Reverse direction and move backward until the high limit switch changes state.
3. Arm the encoder latch.
4. Continue moving backward until the configured latch count is reached.
5. Stop and set the reference position so that the selected latched index position becomes `ECMC_HOME_POS`.

This sequence requires encoder latch support. `ECMC_HOME_LATCH_COUNT_OFFSET` selects which index/latch event to use.

The same EL51xx versus EL7062 distinction applies here as for sequence `11`:

- EL5101/EL5102 use encoder latch PDOs.
- EL7062 uses touch-probe PDOs.

Legacy `epicsEnvSet(...)` configuration still works:

```bash
epicsEnvSet("ECMC_EC_ENC_LATCHPOS",        "ec0.s3.encoderLatchPostion01") # Latch position entry
epicsEnvSet("ECMC_EC_ENC_LATCH_CONTROL",   "ec0.s3.encoderControl01.0")    # Latch arm bit
epicsEnvSet("ECMC_EC_ENC_LATCH_STATUS",    "ec0.s3.encoderStatus01.0")     # Latch occurred bit
epicsEnvSet("ECMC_HOME_LATCH_COUNT_OFFSET","2")                            # 1 = first latch, 2 = second latch, ...
```

For new configs, prefer the YAML-based encoder configuration used in the
EL7047 + EL5102 best-practice example:

YAML-based EL51xx example from the EL7047 + EL5102 best-practice config:

```yaml
encoder:
  desc: Incremental RS422
  unit: mm
  numerator: 1
  denominator: 4096
  type: 0
  bits: 32
  absBits: 0
  position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}
  status: ec0.s$(ENC_SID).encoderStatus${ENC_CH=01}
  control: ec0.s$(ENC_SID).encoderControl${ENC_CH=01}
  primary: True
  latch:
    position: ec0.s$(ENC_SID).encoderLatchPostion$(ENC_CH=01)
    control: 0
    status: 0
  homing:
    type: 12
    position: 0
    velocity:
      to: 2
      from: 1
    acceleration: 1
    deceleration: 1
    latchCount: 1
```

Latch bit mapping:

- Control word bit 0: `0x7000:01`, enable latch on index
- Status word bit 0: `0x6000:01`, latch occurred

#### EL7062 touch-probe based index homing

For EL7062, index homing is configured through the touch probe objects, not through the EL51xx-style latch bits.

The basic setup is:
1. Configure the EL7062 touch probe to trigger on encoder index.
2. Select the secondary encoder as the touch probe source.
3. Use the touch-probe control and status objects in the encoder configuration.
4. Configure the homing sequence as type `11` or `12`.

In `startup.cmd`, the best-practice example configures the drive like this:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=3,HW_DESC=EL7062_CSP"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-Generic-INC, CH_ID=1, MACROS='ST_ENC_RES=4000,TP1_POS_SRC=SEC,TP1_TRG=INDEX'"
```

The matching encoder YAML uses the EL7062 touch-probe PDOs:

```yaml
encoder:
  position: ec0.s$(ENC_SID).positionActual${ENC_CH=01}_2
  status: ec0.s$(ENC_SID).touchProbeStatus${ENC_CH=01}
  control: ec0.s$(ENC_SID).touchProbeControl${ENC_CH=01}
  primary: True
  latch:
    position: ec0.s$(ENC_SID).touchProbePositionPos$(ENC_CH=01)_1
    control: 0
    status: 1
    armCmd: 21
    armBits: 5
  homing:
    type: 11
    position: 0
    latchCount: 1
```

Meaning of the EL7062-specific latch settings:

- `encoder.control`: touch-probe control word.
- `encoder.status`: touch-probe status word.
- `encoder.latch.position`: latched touch-probe position.
- `encoder.latch.control`: start bit in the touch-probe control word where the arm command is written.
- `encoder.latch.armCmd`: value written to arm the touch probe. `21` means `0b10101`, which enables touch probe 1, selects trigger mode B1, and enables latching on positive edge.
- `encoder.latch.armBits`: number of bits written from `armCmd`. For the EL7062 touch-probe example this is `5`.

Use homing sequence `11` for low-limit plus index homing and `12` for high-limit plus index homing.

See also:
- [EL7047 + EL5102 best-practice example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/el7047_el5102)
- [EX7062 CSV best-practice example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/ex7062_CSV)
- [EL7062 CSP best-practice example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/ex7062_CSP)
- [EL7062 hardware notes]({{< relref "/manual/knowledgebase/hardware/EL7062.md" >}})

### ECMC_SEQ_HOME_SET_POS = 15, (setPosition)

Sequence 15 is reserved for save/restore functionality.
Use `ECMC_SEQ_HOME_SET_POS_2` instead if you need the same behavior from normal motion interfaces.

Sequence 15 can still be triggered manually, for example:

```bash
# Turn off amplifier
caput IOC_TEST:Axis1.CNEN 0

# Homing using seq 15
caput IOC_TEST:Axis1.FOFF 1
caput IOC_TEST:Axis1.SET 1
caput IOC_TEST:Axis1.VAL <new position value>
caput IOC_TEST:Axis1.FOFF 0
caput IOC_TEST:Axis1.SET 0
```

### ECMC_SEQ_HOME_LOW_LIM_SINGLE_TURN_ABS = 21

Intended for single-turn absolute encoders such as resolvers.

1. Move backward until the low limit switch is reached.
2. Reverse direction and move forward until the low limit switch changes state.
3. Stop close to the limit reference point.
4. Set the reference position by keeping the absolute single-turn part and adjusting the turn count so that the resulting position matches `ECMC_HOME_POS`, including the turn offset defined by `ECMC_HOME_LATCH_COUNT_OFFSET`.

Only the multi-turn part is adjusted. The single-turn absolute bits are preserved.

Important parameters:

```bash
epicsEnvSet("ECMC_ENC_BITS",               "25") # Total encoder raw bit count
epicsEnvSet("ECMC_ENC_ABS_BITS",           "12") # Absolute single-turn bit count
epicsEnvSet("ECMC_HOME_LATCH_COUNT_OFFSET","2")  # Turn offset for homing
```

### ECMC_SEQ_HOME_HIGH_LIM_SINGLE_TURN_ABS = 22

1. Move forward until the high limit switch is reached.
2. Reverse direction and move backward until the high limit switch changes state.
3. Stop close to the limit reference point.
4. Set the reference position by keeping the absolute single-turn part and adjusting the turn count so that the resulting position matches `ECMC_HOME_POS`, including the turn offset defined by `ECMC_HOME_LATCH_COUNT_OFFSET`.

Only the multi-turn part is adjusted. The single-turn absolute bits are preserved.

Important parameters:

```bash
epicsEnvSet("ECMC_ENC_BITS",               "25") # Total encoder raw bit count
epicsEnvSet("ECMC_ENC_ABS_BITS",           "12") # Absolute single-turn bit count
epicsEnvSet("ECMC_HOME_LATCH_COUNT_OFFSET","2")  # Turn offset for homing
```

### ECMC_SEQ_HOME_SET_POS_2 = 25, (setPosition)

Sequence 25 is the same as sequence 15, but it is not blocked by the motor record.
It writes a new encoder position without any motion.

### ECMC_SEQ_HOME_TRIGG_EXTERN = 26

Trigger a homing sequence in the drive itself.

1. Optional: switch the drive to homing mode and wait for mode readback.
2. Trigger homing in the drive.
3. Wait for the drive homing-ready status.
4. On the rising edge of the homing-ready status, reference the ecmc encoder object to `ECMC_HOME_POS`.
5. Optional: switch the drive back to normal motion mode and wait for mode readback.
6. Optional: execute the configured post-home move.

For drives such as SmarAct MCS2, this sequence is normally used together with
automatic drive-mode switching. In YAML-based axis configuration this is done
with `autoMode`, where `modeSet` and `modeAct` point to the drive mode process
data, and `modeCmdHome`/`modeCmdMotion` define the drive-specific mode values.

Example:

```yaml
axis:
  mode: CSP
  autoMode:
    modeSet: ec0.s${MCS2_SLAVE_NUM}.mode0${MCS2_CHID}
    modeAct: ec0.s${MCS2_SLAVE_NUM}.modeActual0${MCS2_CHID}
    modeCmdMotion: 8
    modeCmdHome: 6

encoder:
  homing:
    type: 26
    trigg: ec0.s${MCS2_SLAVE_NUM}.driveCmdExe0${MCS2_CHID}.0
    ready: ec0.s${MCS2_SLAVE_NUM}.driveStatus0${MCS2_CHID}.10
    refAtHome: 1
```

Notes:

- `trigg` shall point to the bit that starts homing in the drive.
- `ready` shall point to the homing-done or homing-ready status bit from the drive.
- The mode values are drive-specific. For SmarAct MCS2, normal CSP motion uses
  `8` and homing uses `6`.
- Homing velocity and acceleration can also be drive-specific. For SmarAct,
  these are often configured in the actuator component setup rather than in the
  generic YAML homing block.

Example:

- [SmarAct MCS2 best-practice example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/smaract/mcs2)

### ECMC_SEQ_HOME_PLC = 27

Sequence 27 lets PLC code or C++ logic plugins implement the actual homing
procedure. ecmc keeps the request/done/error handshake and homed-state
bookkeeping, but the custom logic owns the motion.

The sequencer and the custom homing logic use these axis variables:

| Variable | Direction | Meaning |
| --- | --- | --- |
| `ax<id>.homing.request` | read-only | Set to `1` by ecmc while custom homing shall run. |
| `ax<id>.homing.state` | read/write | Custom homing progress state. Logic writes `0..999`; ecmc publishes `1000` when homing is finalized. |
| `ax<id>.homing.done` | read/write | Logic sets this to `1` when the custom homing procedure succeeded. |
| `ax<id>.homing.error` | read/write | Logic sets this to `1` when the custom homing procedure failed. |

When sequence 27 starts, ecmc sets `homing.request=1`, `homing.state=1`,
`homing.done=0`, and `homing.error=0`. The sequence remains active like the
other homing sequences, so the normal axis busy flag stays high until custom
homing finishes. PLC code or C++ logic must not use the ordinary motion commands
for homing moves while sequence 27 is active. Use the dedicated custom-homing
motion helpers instead.

The custom logic owns the reference position for this sequence. When the logic
sets `homing.done=1`, ecmc does not write encoder positions. It waits until any
custom-homing helper move is no longer busy, marks the configured homing encoders
as homed, aligns the internal trajectory/controller setpoints to the current
primary encoder position, and sets `homing.state=1000`. If the logic sets
`homing.error=1`, the homing sequence fails.

Sequence 27 does not run the configured ecmc post-home move. If a final
post-home move is needed, perform it in the PLC or C++ logic before setting
`homing.done=1`.

PLC writes to `homing.state` are clamped to `0..999`; completion is reported
with `homing.done`, not by writing a large state value.

The PLC custom-homing motion helpers are only valid while sequence 27 is active:

| Function | Meaning |
| --- | --- |
| `mc_home_move_abs(axIndex, execute, pos, vel, acc, dec)` | Trigger an absolute move through the active homing sequence. |
| `mc_home_move_rel(axIndex, execute, distance, vel, acc, dec)` | Trigger a relative move through the active homing sequence. |
| `mc_home_move_vel(axIndex, execute, vel, acc, dec)` | Trigger a constant-velocity move through the active homing sequence. |
| `mc_home_halt(axIndex, execute)` | Stop the active custom-homing helper move. |
| `mc_home_get_busy(axIndex)` | Returns `1` while custom homing sequence 27 is active, without including global axis busy. |
| `mc_home_move_busy(axIndex)` | Returns `1` while a custom-homing helper move is busy. |

C++ logic plugins can use the equivalent helpers
`ecmcCpp::axisHomeMoveAbs()`, `ecmcCpp::axisHomeMoveRel()`,
`ecmcCpp::axisHomeMoveVel()`, `ecmcCpp::axisHomeHalt()`,
`ecmcCpp::axisHomeBusy()`, and `ecmcCpp::axisHomeMoveBusy()`.

The move and halt helpers are edge triggered on `execute`. Setting `execute=0`
resets the edge state; it does not stop an active helper move. Use
`mc_home_halt()` or `ecmcCpp::axisHomeHalt()` to stop a helper move explicitly.

If PLC homing logic needs to adjust a specific encoder position before reporting
done, use `mc_set_act_pos(axIndex, encIndex, actpos)`. From C++ logic, use
`ecmcCpp::axisSetEncoderActualPos(axisIndex, encoderIndex, value)`. In both
helpers, `encoderIndex` is 1-based. For sequence 27, ecmc does not force any
encoder to `ECMC_HOME_POS` when `homing.done` is set, so the custom logic can
set one or several encoder positions as needed.

Minimal PLC pattern:

```text
if(plc0.firstscan) {
  static.plcHomeActive := 0;
  static.plcHomeExecute := 0;
  static.plcHomeMoveExecute := 0;
};

static.plcHomeExecute := 0;

if(ax1.homing.request and not(static.plcHomeActive)) {
  static.plcHomeActive := 1;
  ax1.homing.state := 10;
  ax1.homing.done := 0;
  ax1.homing.error := 0;
};

if(static.plcHomeActive) {
  # Example placeholder for custom homing logic.
  # Replace this with sensor checks and homing helper moves as needed.
  # If a post-home move is needed, run that move here before setting done.
  ax1.homing.state := 100;

  if(<move shall start>) {
    static.plcHomeMoveExecute := 1;
  };

  mc_home_move_abs(1, static.plcHomeMoveExecute, 10.0, 2.0, 10.0, 10.0);

  if(not(mc_home_move_busy(1))) {
    static.plcHomeMoveExecute := 0;
  };

  if(<custom homing condition is fulfilled>) {
    # Optional: set an encoder position explicitly before reporting done.
    # mc_set_act_pos(1, 1, 0.0);
    ax1.homing.done := 1;
    static.plcHomeActive := 0;
  };

  if(<custom homing failure condition>) {
    ax1.homing.error := 1;
    static.plcHomeActive := 0;
  };
};
```

To start this homing sequence from PLC code, trigger normal homing with sequence
`27`:

```text
if(plc0.firstscan) {
  static.homeReq := 0;
  static.homeExecute := 0;
};

static.homeExecute := 0;

if(static.homeReq and not(mc_get_busy(1))) {
  static.homeExecute := 1;
  static.homeReq := 0;
};

mc_home(1, static.homeExecute, 27, 1.0, 1.0);
```

In this example, the PLC logic decides the reference position. Set it with
`mc_set_act_pos()` before writing `ax1.homing.done=1`.

## Setting polarity of the home sensor

For several sequences it is useful to invert the effective home-switch polarity.
Use:

```cpp
"Cfg.SetAxisMonHomeSwitchPolarity(int axisIndex, int polarity)";
# polarity == 0: NC (default)
# polarity == 1: NO
```

## Homing of absolute encoder with **ONE** overflow in the range

**Always** adjust the absolute encoder so that no overflow occurs within the usable motion range if possible.

If that is not possible, homing can be handled in PLC code. No dedicated ecmc homing sequence exists for this case.

Example:

```c
/*
  PLC code to home an axis with an absolute encoder which has ONE overflow in the range
  If actual encoder value is higher than ${THRESHOLD} it will be referenced to current actual position - ${RANGE}.

  NOTE: Make sure the default axis encoder scaling offset is correct for the lower part of the raw values.

  macros:
    AX_ID     : ID of axis
    ENC_ID    : ID of encoder (starts from 1)
    THRESHOLD : Threshold to identify overflow (in EGU)
    RANGE     : Total encoder range, both single-turn and multi-turn (in EGU)
    DBG       : Print debug messages, or leave empty (DBG='')
*/

if(${SELF}.firstscan) {
  var plc := ${SELF_ID};
  ${DBG=#}println('PLC ', plc, ' Initiating homing seq for abs. encoder with overflow');
};

if(mc_get_enc_ready(${AX_ID=1}, ${ENC_ID=1}) and not(static.encoderHomed)) {
  ${DBG=#}println('Checking if homing encoder is needed');

  if(mc_get_act_pos(${AX_ID=1}, ${ENC_ID=1}) > ${THRESHOLD=0}) {
    ${DBG=#}println('Homing encoder to: ', mc_get_act_pos(${AX_ID=1}, ${ENC_ID=1}) - ${RANGE=0});
    mc_set_act_pos(${AX_ID=1}, ${ENC_ID=1}, mc_get_act_pos(${AX_ID=1}, ${ENC_ID=1}) - ${RANGE=0});
  } else {
    ${DBG=#}println('Homing not needed!');
  };

  static.encoderHomed${AX_ID=1}_${ENC_ID=1} := 1;
}

/* Do not allow power on axis if encoder is not homed */
if(not(static.encoderHomed${AX_ID=1}_${ENC_ID=1})) {
  ${DBG=#}println('Waiting for encoder ready and homing...');
  mc_power(${AX_ID=1}, 0);
};
```

The code is available in:
[home_abs_enc_overflow.plc_inc](https://github.com/paulscherrerinstitute/ecmccfg/plc_lib/home_abs_enc_overflow.plc_inc)

It is installed with `ecmccfg` and can be loaded from `ecmccfg_DIR`:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "FILE=${ecmccfg_DIR}home_abs_enc_overflow.plc_inc, SAMPLE_RATE_MS=1000, PLC_MACROS='DBG='"
```

The file can also be included from another PLC file.

Example `main.plc`:

```text
# macros here or in PLC_MACROS in call to loadPLCFile.cmd:
substitute(AX_ID=1,ENC_ID=1,RANGE=360,THRESHOLD=240)
include "home_abs_enc_overflow.plc_inc"
```

Load the file with an include directory:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "FILE=./cfg/main.plc, INC=${ecmccfg_DIR}, SAMPLE_RATE_MS=1000, PLC_MACROS='DBG='"
```
