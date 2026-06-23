# Motion sequencer lab test

This example reuses the EL7041 and EL5042 BiSS-C axis configuration from
`../stepper_bissc`.

`startup_local_hw.cmd` creates axis 1 and sequence 0. The sequence is compiled
and armed but deliberately not started during IOC startup.

The test sequence:

1. resets axis 1
2. powers axis 1
3. starts a nonblocking +0.2 mm relative move
4. waits until axis 1 is in position
5. waits 500 ms
6. executes a blocking -0.2 mm relative move

The explicit `SeqWaitInPos` after the nonblocking move tests that command issue
and motion completion can be separated into different sequence steps.

After verifying that the stage has sufficient travel in both directions, start
the sequence with:

```text
Cfg.StartMotionSeq(0)
```

or through EPICS:

```bash
caput "$(IOC):Seq0-Cmd-Start" 1
```

Inspect status with:

```bash
caget "$(IOC):Seq0-State"
caget "$(IOC):Seq0-StepIndex"
caget "$(IOC):Seq0-ErrorId"
```

Before another run, arm the sequence again:

```text
Cfg.ArmMotionSeq(0)
Cfg.StartMotionSeq(0)
```

or use:

```bash
caput "$(IOC):Seq0-Cmd-Arm" 1
caput "$(IOC):Seq0-Cmd-Start" 1
```
