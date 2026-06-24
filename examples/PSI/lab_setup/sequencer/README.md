# Motion sequencer lab test

This example contains a local copy of the EL7041 and EL5042 BiSS-C axis
configuration under `cfg/`.

`startup_local_hw.cmd` creates axis 1 and sequence 0. The sequence is compiled
and armed but deliberately not started during IOC startup.

The test sequence:

1. resets axis 1
2. powers axis 1
3. executes an explicitly blocking absolute move to 10 mm
4. arms trigger ID 0 on `ec0.s14.ZERO` for positions `15:1:35`
5. starts a nonblocking absolute move to 40 mm
6. waits until trigger ID 0 has fired at all trigger points
7. waits until axis 1 is in position

The explicit trigger wait and final `SeqWaitInPos` after the nonblocking move
test that command issue, trigger completion, and motion completion can be
separated into different sequence steps.

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

This example writes the hard trigger item `ec0.s14.ZERO`; it does not increment
the sequencer soft-trigger counters. To test soft trigger PVs instead, replace
`ec0.s14.ZERO` with `soft` in the `SeqArmPosTrigger` command.

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
