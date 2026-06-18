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

Prefer the action-specific `Cfg.Seq*` commands when defining sequences in a
startup script.

## Startup Commands

Motion and waits:

```text
Cfg.SeqNop(seq,step)
Cfg.SeqWaitTime(seq,step,waitMs)
Cfg.SeqReset(seq,step,axis,timeoutMs)
Cfg.SeqPower(seq,step,axis,enable,timeoutMs)
Cfg.SeqHome(seq,step,axis,homeSeq,homePos,velToCam,velOffCam,acc,dec,timeoutMs)
Cfg.SeqMoveAbs(seq,step,axis,pos,vel,acc,dec,timeoutMs)
Cfg.SeqMoveRel(seq,step,axis,distance,vel,acc,dec,timeoutMs)
Cfg.SeqMoveVel(seq,step,axis,vel,acc,dec,timeoutMs)
Cfg.SeqMoveVel(seq,step,axis,vel,acc,dec,timeoutMs,wait,tolerance)
Cfg.SeqHalt(seq,step,axis,timeoutMs)
Cfg.SeqWaitInPos(seq,step,axis,timeoutMs)
```

Data items:

```text
Cfg.SeqSetItem(seq,step,item,value,timeoutMs)
Cfg.SeqWaitItem(seq,step,item,op,value,timeoutMs)
```

`SeqWaitItem` supports `==`, `!=`, `>`, `>=`, `<`, `<=`, `eq`, and `ne`.

Nested sequences:

```text
Cfg.SeqRunSeq(parentSeq,step,childSeq,timeoutMs)
```

Triggers:

```text
Cfg.SeqArmPosTrigger(seq,step,id,axis,item,startPos,period,count,value,pulseMs)
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
Cfg.SeqArmPosTrigger(0,0,0,1,ec0.s1.output01,10.0,1.0,20,1,5)
Cfg.SeqMoveAbs(0,1,1,50.0,10.0,20.0,20.0,10000)
Cfg.SeqWaitTriggerDone(0,2,0,1000)
```

This pulses the output at positions `10`, `11`, through `29`. A negative period
supports reverse motion.

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
Cfg.SeqArmPosTrigger(0,0,0,1,soft,10.0,1.0,20,1,0)
Cfg.SeqArmTimeTrigger(0,1,1,soft,10,5,100,1,0)
```

Each event increments:

```text
stat.soft_trigger_count
```

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

## Example: Reusable Scan Line

Define sequence 0 as one X scan line:

```text
Cfg.SeqArmPosTrigger(0,0,0,1,soft,10.0,1.0,100,1,0)
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
