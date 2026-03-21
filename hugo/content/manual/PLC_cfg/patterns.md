+++
title = "patterns"
weight = 15
chapter = false
+++

Reference companion to [syntax]({{< relref "/manual/PLC_cfg/syntax.md" >}}),
[variables]({{< relref "/manual/PLC_cfg/variables.md" >}}), and
[best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}}).

These examples are intentionally short and focus on the most common building blocks.

When both a helper function and a direct variable are available, prefer the
helper function in PLC logic. For example, use `mc_get_busy(1)` instead of
reading `ax1.traj.busy` directly when the function already expresses the intent.
This also avoids confusion about PLC variable timing, since the variables are
refreshed before and after each PLC scan, while the function calls read current
values directly.

## common PLC patterns

### 1. Use `static` for local PLC state

```text
if(plc0.firstscan) {
  static.step := 0;
  static.startCmd := 0;
};

if(static.startCmd and static.step = 0) {
  static.step := 1;
};
```

Use `static.<name>` for state that belongs to one PLC only, for example steps,
internal command bits, counters, or latched values.

### 2. Use `global` to share data between PLCs

```text
if(plc0.firstscan) {
  global.mode := 0;
};

if(static.requestAuto) {
  global.mode := 1;
};
```

Use `global.<name>` when several PLCs need to read or write the same value.

### 3. Trigger one absolute move from a PLC

```text
if(plc0.firstscan) {
  static.moveReq := 0;   # Set by other PLC logic or from EPICS
  static.execute := 0;
};

static.execute := 0;

if(static.moveReq and not(mc_get_busy(1))) {
  static.execute := 1;   # One-scan pulse
  static.moveReq := 0;   # Consume request
};

mc_move_abs(1, static.execute, 10.0, 5.0, 10.0, 10.0);
```

`mc_move_abs()` is edge-triggered on its `execute` input. Do not hold `execute=1`,
and do not derive it directly from `not(mc_get_busy(1))`, or the move will be
retriggered every time the axis becomes idle again.

### 4. Start homing from a PLC

```text
if(plc0.firstscan) {
  static.homeReq := 0;       # Set by other PLC logic or from EPICS
  static.homeExecute := 0;
};

static.homeExecute := 0;

if(static.homeReq and not(mc_get_busy(1)) and not(mc_get_homed(1))) {
  static.homeExecute := 1;   # One-scan pulse
  static.homeReq := 0;       # Consume request
};

mc_home(1, static.homeExecute, 11, 2.0, 1.0);
```

Use `mc_get_homed()`, `mc_get_busy()`, and `ax<id>.seq.state` together when
building homing-related PLC logic. As for the motion example, keep the execute
signal as a one-scan pulse triggered from a separate request bit.

### 5. Append values to a data-storage buffer

```text
if(mc_get_busy(1)) {
  ds_append_data(0, ax1.enc.actpos);
};
```

This is the simplest pattern for buffered capture from PLC logic.

### 6. Push data-storage values to EPICS immediately

```text
if(static.pushNow) {
  ds_push_asyn(0);
  static.pushNow := 0;
};
```

This is mainly useful when the data-storage records are configured with
`T_SMP_MS=-1`.

### 7. Expose a PLC variable to EPICS

After `loadPLCFile.cmd`, a PLC-local static variable can be exposed with:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd "NAME=Counter,PLC_VAR=counter,EGU=counts,PREC=0"
```

A shared global variable can be exposed with:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd "NAME=Mode,PLC_VAR=mode,SCOPE=global,ONAM=Remote,ZNAM=Local"
```

For the naming details and more EPICS examples, see
[best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}}).
