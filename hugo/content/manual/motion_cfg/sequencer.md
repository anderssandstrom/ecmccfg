+++
title = "Motion sequencer"
weight = 25
chapter = false
+++

## Scope

The motion sequencer defines and executes short deterministic workflows inside
the ecmc realtime loop. Sequences may be defined from IOC startup commands or
edited at runtime through a dedicated asyn port and EPICS records.

This implementation is experimental. It is intended for workflows such as:

- move, wait for an input, then halt
- reusable scan-line sequences
- nested sequences for raster scans
- position-based output triggers
- time-based output triggers
- software triggers exposed as an EPICS counter

Existing axis behavior is unchanged unless a sequence is explicitly created,
compiled, armed, and started.

## Adding a Sequence

Use `addMotionSequence.cmd` to create an empty sequence and its EPICS interface before defining steps:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}scripts/addMotionSequence.cmd, \
  "SEQ_ID=0,MAX_STEPS=32,DB_PREFIX=$(IOC):,RECORD_PREFIX=Seq0-"
```

Defaults:

- `SEQ_ID=0`
- `MAX_STEPS=32`
- `ASYN_PORT=ECMC_SEQ<SEQ_ID>`
- `DB_PREFIX=$(IOC):`
- `RECORD_PREFIX=Seq<SEQ_ID>-`
- `SCAN=.1 second`
- `PREC=3`
- `LOAD_PVS=1`
- `REPORT=0`

`SOFT_TRG_FLNK` optionally defines a forward link from the soft-trigger counter.

The wrapper first executes:

```text
Cfg.CreateMotionSeq(seqIndex,maxSteps,portName)
```

and then loads `ecmcMotionSequence.template`. Creation must happen before the
records connect to the dedicated sequence port.

Each call also registers the sequence in the IOC configuration namespace:

```text
$(IOC):MCU-Cfg-SEQ-Cnt
$(IOC):MCU-Cfg-SEQ-FrstObjId
$(IOC):MCU-Cfg-SEQ<ID>-Pfx
$(IOC):MCU-Cfg-SEQ<ID>-NxtObjId
$(IOC):MCU-Cfg-SEQ<ID>-PrvObjId
```

The linked list preserves creation order and supports sparse sequence IDs.
The caQtDM overview follows this list, so it only includes configured
sequences. Open it through `ecmcMain.ui` or directly with:

```sh
python3 /ioc/modules/qt/ecmc_start_motion_sequence_overview.py <IOC>
```

## Lifecycle

A sequence follows this lifecycle:

```text
create -> define/edit -> compile -> arm -> start
```

Typical startup definition:

```text
Cfg.SeqMoveAbs(0,0,1,10.0,5.0,20.0,20.0,5000)
Cfg.SeqWaitInPos(0,1,1,2000)
Cfg.CompileMotionSeq(0)
Cfg.ArmMotionSeq(0)
```

The sequence can then be started through:

```text
Cfg.StartMotionSeq(0)
```

or the `Seq0-Cmd-Start` record.

Compile validates steps and resolves data-item bindings in a low-priority EPICS
thread. Arm copies the compiled plan into the active realtime plan.

## Runtime PV Editing

Steps can also be inspected and changed through records. Select a step for
readback with `Read-Index` and process `Read-Cmd`, or use `Read-Prev` and
`Read-Next`:

```sh
caput IOC:Seq0-Read-Index 3
caput IOC:Seq0-Read-Cmd 1
caget IOC:Seq0-Read-Action IOC:Seq0-Read-Axis IOC:Seq0-Read-Name
```

`Read-Prev` and `Read-Next` skip disabled/unconfigured step slots. Direct
`Read-Index` plus `Read-Cmd` can still inspect any slot, including empty gaps
left for sparse step numbering.

`Read-CmdLine` exposes the selected step as a one-line text row. It is a
read-only waveform so navigating with `Read-Prev` and `Read-Next` does not
overwrite the editable command buffer. Process `Read-ToCmdLine` to copy the
selected row into `CmdLine` and the editable step fields:

```sh
caget -S IOC:Seq0-Read-CmdLine
caput IOC:Seq0-Read-ToCmdLine 1
```

To edit a step, write the `Edit-*` fields and then process `Edit-Apply`.
Recompile and arm the sequence before starting it:

```sh
caput IOC:Seq0-Edit-Index 3
caput IOC:Seq0-Edit-Enable 1
caput IOC:Seq0-Edit-Action 5
caput IOC:Seq0-Edit-Axis 1
caput IOC:Seq0-Edit-Position 0.2
caput IOC:Seq0-Edit-Velocity 0.5
caput IOC:Seq0-Edit-Acceleration 2
caput IOC:Seq0-Edit-Deceleration 2
caput IOC:Seq0-Edit-TimeoutMs 5000
caput -S IOC:Seq0-Edit-Name "rel +0.2"
caput IOC:Seq0-Edit-Apply 1
caput IOC:Seq0-Cmd-Compile 1
caput IOC:Seq0-Cmd-Arm 1
```

To insert or delete a configured step at `Edit-Index`, process `Edit-Insert`
or `Edit-Delete`:

```sh
caput IOC:Seq0-Edit-Index 4
caput IOC:Seq0-Edit-Insert 1
caput IOC:Seq0-Edit-Delete 1
```

Insert shifts steps at and after the index up by one and clears the inserted
step. Delete shifts later steps down by one. Both operations invalidate the
compiled/armed plan. Branch and goto targets are updated automatically when
they are shifted. Delete fails if another step targets the deleted step.

The caQtDM sequence detail panel exposes the same readback and edit records.
`Edit-Action`, `Read-Action`, and the runtime `Action` record are numeric
action IDs. Use `Read-CmdLine` or `CmdLine` when a decoded text representation
is more useful.

For common edits, use the one-line command waveform instead of writing every
field manually:

```sh
caput -S IOC:Seq0-CmdLine "4: wait_item ec.s2.ai01 gt 10.5 timeout=5000 name='wait ai01'"
caput IOC:Seq0-CmdLine-Apply 1
caget -S IOC:Seq0-CmdLine-Result
caget -S IOC:Seq0-Read-CmdLine
```

`CmdLine-Result` reports parse/apply feedback. `Read-CmdLine` exposes the
selected readback row in the same one-line syntax.

The command line syntax is:

```text
<step>: <action> key=value key=value ...
```

Use `enabled=0` to define a disabled step. For `power`, `enable=0|1`
controls the axis power state.

Supported initial actions include:

```text
nop
reset axis=<id> timeout=<ms> wait=<0|1>
power axis=<id> enable=<0|1> timeout=<ms> wait=<0|1>
home axis=<id> timeout=<ms> wait=<0|1>
move_abs axis=<id> pos=<pos> vel=<vel> acc=<acc> dec=<dec> timeout=<ms> wait=<0|1>
move_rel axis=<id> dist=<dist> vel=<vel> acc=<acc> dec=<dec> timeout=<ms> wait=<0|1>
move_vel axis=<id> vel=<vel> acc=<acc> dec=<dec>
halt axis=<id> timeout=<ms> wait=<0|1>
wait_inpos axis=<id> timeout=<ms>
set_enc_homed axis=<id> homed=<0|1>
wait_time ms=<ms>
run_seq seq=<childSeq> timeout=<ms>
set_item item=<dataItem> value=<value>
wait_item item=<dataItem> op=<eq|ne|gt|gte|lt|lte> value=<value> timeout=<ms>
exit_item item=<dataItem> op=<eq|ne|gt|gte|lt|lte> value=<value> timeout=<ms>
branch_item item=<dataItem> op=<eq|ne|gt|gte|lt|lte> value=<value> true_step=<step> [false_step=<step>]
goto_step target=<step>
```

## Supported Actions

| ID | Action |
|---:|---|
| 0 | NOP |
| 1 | MC_Reset |
| 2 | MC_Power |
| 3 | MC_Home |
| 4 | MC_MoveAbsolute |
| 5 | MC_MoveRelative |
| 6 | WaitInPosition |
| 7 | SetItem |
| 8 | WaitItem |
| 9 | WaitTime |
| 10 | RunSequence |
| 11 | ArmPositionTrigger |
| 12 | WaitTriggerDone |
| 13 | ArmTimeTrigger |
| 14 | MC_MoveVelocity |
| 15 | MC_Halt |
| 16 | ExitItem |
| 17 | SetEncHomed |
| 18 | BranchItem |
| 19 | GotoStep |

Prefer the action-specific `Cfg.Seq*` commands when defining sequences in a
startup script.

## Startup Commands

Motion and waits:

```text
Cfg.SeqNop(seq,step)
Cfg.SeqWaitTime(seq,step,waitMs)
Cfg.SeqReset(seq,step,axis,timeoutMs)
Cfg.SeqReset(seq,step,axis,timeoutMs,wait)
Cfg.SeqPower(seq,step,axis,enable,timeoutMs)
Cfg.SeqPower(seq,step,axis,enable,timeoutMs,wait)
Cfg.SeqHome(seq,step,axis,homeSeq,homePos,velToCam,velOffCam,acc,dec,timeoutMs)
Cfg.SeqHome(seq,step,axis,homeSeq,homePos,velToCam,velOffCam,acc,dec,timeoutMs,wait)
Cfg.SeqMoveAbs(seq,step,axis,pos,vel,acc,dec,timeoutMs)
Cfg.SeqMoveAbs(seq,step,axis,pos,vel,acc,dec,timeoutMs,wait)
Cfg.SeqMoveRel(seq,step,axis,distance,vel,acc,dec,timeoutMs)
Cfg.SeqMoveRel(seq,step,axis,distance,vel,acc,dec,timeoutMs,wait)
Cfg.SeqMoveVel(seq,step,axis,vel,acc,dec,timeoutMs)
Cfg.SeqMoveVel(seq,step,axis,vel,acc,dec,timeoutMs,wait,tolerance)
Cfg.SeqHalt(seq,step,axis,timeoutMs)
Cfg.SeqHalt(seq,step,axis,timeoutMs,wait)
Cfg.SeqWaitInPos(seq,step,axis,timeoutMs)
Cfg.SeqSetEncHomed(seq,step,axis,homed)
```

`SeqSetEncHomed` sets the homed flag on the axis primary/current encoder and
then advances immediately.

Data items:

```text
Cfg.SeqSetItem(seq,step,item,value,timeoutMs)
Cfg.SeqWaitItem(seq,step,item,op,value,timeoutMs)
Cfg.SeqExitItem(seq,step,item,op,value,timeoutMs)
Cfg.SeqBranchItem(seq,step,item,op,value,trueStep)
Cfg.SeqBranchItem(seq,step,item,op,value,trueStep,falseStep)
Cfg.SeqGotoStep(seq,step,targetStep)
Cfg.InsertMotionSeqStep(seq,step)
Cfg.DeleteMotionSeqStep(seq,step)
```

`SeqWaitItem` and `SeqExitItem` support `==`, `!=`, `>`, `>=`, `<`, `<=`,
`eq`, and `ne`. `SeqExitItem` exits the current sequence as `Done` when the
condition is fulfilled; if the condition is false, the sequence continues with
the next step.

`SeqBranchItem` uses the same operators. It jumps to `trueStep` when the
condition is fulfilled. In one-line commands these targets are named
`true_step` and `false_step`. If `falseStep`/`false_step` is omitted, a false
condition continues with the next enabled step; otherwise it jumps to the false
target. Branch and goto targets are configured step IDs and must point to
enabled steps.

Nested sequences:

```text
Cfg.SeqRunSeq(parentSeq,step,childSeq,timeoutMs)
```

Triggers:

```text
Cfg.SeqArmPosTrigger(seq,step,id,axis,item,startPos,interval,endPos,value,pulseMs)
Cfg.SeqArmTimeTrigger(seq,step,id,item,delayMs,periodMs,count,value,pulseMs)
Cfg.SeqWaitTriggerDone(seq,step,id,timeoutMs)
```

Control and inspection:

```text
Cfg.CompileMotionSeq(seq)
Cfg.ArmMotionSeq(seq)
Cfg.StartMotionSeq(seq)
Cfg.StopMotionSeq(seq)
Cfg.ResetMotionSeq(seq)
Cfg.ReportMotionSeq(seq)
Cfg.ReportMotionSeq(seq,step)
```

## Velocity Move and Halt

The short `SeqMoveVel` form is nonblocking. It issues the velocity command and
advances immediately:

```text
Cfg.SeqMoveVel(0,0,1,10.0,20.0,20.0,1000)
Cfg.SeqWaitItem(0,1,ec0.s1.stopInput,==,1,30000)
Cfg.SeqHalt(0,2,1,5000)
```

The extended form optionally waits for actual velocity:

```text
Cfg.SeqMoveVel(0,0,1,10.0,20.0,20.0,5000,1,0.1)
```

This waits until actual velocity is within `10.0 +/- 0.1`. Internally the generic
step arguments are:

```text
wait=1;tol=0.1
```

This representation is also available through the `Edit-Args` record.

## Blocking and Nonblocking Motion

All motion helpers support an optional final `wait` argument. The short forms
keep their existing defaults:

- reset, power, home, absolute move, relative move, and halt default to `wait=1`
- velocity move defaults to `wait=0`

With `wait=0`, the command is issued and the sequence advances immediately. This
allows multiple axes to be started in consecutive realtime cycles:

```text
Cfg.SeqMoveAbs(0,0,1,100.0,10.0,20.0,20.0,1000,0)
Cfg.SeqMoveAbs(0,1,2,50.0,5.0,10.0,10.0,1000,0)
Cfg.SeqWaitInPos(0,2,1,15000)
Cfg.SeqWaitInPos(0,3,2,15000)
```

The generic step representation stores this as:

```text
wait=0
```

It can therefore also be configured through `Edit-Args`. A later wait step
should be used when completion must be synchronized.

## Nested Sequences

Sequence `1` can execute sequence `0`, wait, and execute it again:

```text
Cfg.SeqRunSeq(1,0,0,10000)
Cfg.SeqWaitTime(1,1,500)
Cfg.SeqRunSeq(1,2,0,10000)
```

`step` is the step position in the parent sequence. `childSeq` selects the
sequence being called.

The child must reach `DONE` before the parent step timeout. Child errors and
stops propagate to the parent. Direct self-call is rejected during compile.

## Position Triggers

Position triggers are armed before a later motion step and execute in the
background:

```text
Cfg.SeqArmPosTrigger(0,0,0,1,ec0.s1.output01,10.0,1.0,29.0,1,5)
Cfg.SeqMoveAbs(0,1,1,50.0,10.0,20.0,20.0,10000)
Cfg.SeqWaitTriggerDone(0,2,0,1000)
```

This pulses the output at positions `10`, `11`, through `29`. The range is `startPos:interval:endPos`; negative intervals support reverse motion, for example `80,-1,20` fires at `80,79,...,20`.

## Time Triggers

Time triggers use elapsed time after the arm step:

```text
Cfg.SeqArmTimeTrigger(0,0,0,ec0.s1.output01,10,5,100,1,1)
```

This fires first after 10 ms, then every 5 ms, for 100 pulses. Each pulse remains
high for 1 ms.

## Soft Triggers

Use `soft` instead of a data-item name:

```text
Cfg.SeqArmPosTrigger(0,0,0,1,soft,10.0,1.0,29.0,1,0)
Cfg.SeqArmTimeTrigger(0,1,1,soft,10,5,100,1,0)
```

Each event increments:

```text
stat.soft_trigger_count
```

Trigger IDs `0..7` also expose dedicated counters and pulse-active status:

```text
stat.soft_trigger.<id>.count
stat.soft_trigger.<id>.pulse
```

The ecmccfg database maps these to `SoftTrig0Count`/`SoftTrig0Pulse` through
`SoftTrig7Count`/`SoftTrig7Pulse`. Use the counters as the reliable EPICS event
source. The pulse flags are only high while a soft trigger pulse is active and
therefore require a nonzero `pulseMs`.

and updates:

```text
stat.soft_trigger_id
```

The corresponding records are `SoftTriggerCount` and `SoftTriggerId`.
`SoftTriggerEvent` is processed through a `CP` link when the counter posts a
changed value. `SOFT_TRG_FLNK` can forward-link that event to another record.
The counter value should still be used to detect the number of new events.

## EPICS Record Interface

With defaults for sequence 0, records use prefix `$(IOC):Seq0-`.

Editing:

```text
Edit-Index
Edit-Enable
Edit-Action
Edit-Axis
Edit-Position
Edit-Velocity
Edit-Acceleration
Edit-Deceleration
Edit-TimeoutMs
Edit-Name
Edit-Transition
Edit-OnError
Edit-Args
Edit-Apply
CmdLine
CmdLine-Apply
CmdLine-Result
```

Readback navigation:

```text
Read-Index
Read-Cmd
Read-Prev
Read-Next
Read-Enable
Read-Action
Read-Axis
Read-Position
Read-Velocity
Read-Acceleration
Read-Deceleration
Read-TimeoutMs
Read-Name
Read-Transition
Read-OnError
Read-Args
```

Commands and status:

```text
Cmd-Compile
Cmd-Arm
Cmd-Start
Cmd-Stop
Cmd-Reset
State
Valid
Armed
Running
CompileBusy
StepIndex
Action
ErrorId
StepCount
ElapsedMs
StepName
ErrorText
ValidationText
SoftTriggerId
SoftTriggerCount
SoftTriggerEvent
```

Status and readback records poll at `SCAN` because realtime sequence updates do
not currently generate asyn callbacks.

## PLC Functions

The ecmc PLC library exposes sequence control and status helpers. Command-style
functions are rising-edge triggered on the `execute` argument.

```text
seq_arm(seq,execute)
seq_set_step(seq,execute,step_id)
```

`seq_arm` arms an already compiled sequence. `seq_set_step` requests a jump to a
configured step ID. The sequence must be armed or running; missing target steps
put the sequence in error.

Status getters:

```text
seq_get_state(seq)
seq_get_valid(seq)
seq_get_armed(seq)
seq_get_running(seq)
seq_get_compile_busy(seq)
seq_get_step(seq)
seq_get_action(seq)
seq_get_error(seq)
seq_get_step_count(seq)
seq_get_elapsed_ms(seq)
```

`seq_get_step` returns the configured step ID of the active step. It returns
`-1` when no step is active.

Example:

```text
arm_err := seq_arm(0, arm_exec);
jump_err := seq_set_step(0, jump_exec, 20);
seq_running := seq_get_running(0);
seq_step := seq_get_step(0);
```

## Example: Reusable Scan Line

Define sequence 0 as one X scan line:

```text
Cfg.SeqArmPosTrigger(0,0,0,1,soft,10.0,1.0,109.0,1,0)
Cfg.SeqMoveAbs(0,1,1,110.0,20.0,50.0,50.0,20000)
Cfg.SeqWaitTriggerDone(0,2,0,2000)
Cfg.CompileMotionSeq(0)
Cfg.ArmMotionSeq(0)
```

Sequence 1 composes scan lines with Y steps:

```text
Cfg.SeqRunSeq(1,0,0,25000)
Cfg.SeqMoveRel(1,1,2,0.1,2.0,10.0,10.0,5000)
Cfg.SeqRunSeq(1,2,0,25000)
```

Separate forward and backward child sequences can implement a snake/raster scan
without an extra return move.

## Current Limitations

- This implementation still needs build and target-system testing.
- Status records use polling rather than realtime asyn callbacks.
- The EPICS records expose the generic step structure; action-specific operator
  screens can be added in the EPICS layer.
- Compile currently uses one low-priority worker thread per sequence.
- Recursive call validation rejects direct self-call, not complete recursive
  sequence graphs.
- Soft triggers expose a shared counter and last trigger ID rather than an event
  FIFO.
- Trigger timing resolution is one ecmc realtime cycle.
