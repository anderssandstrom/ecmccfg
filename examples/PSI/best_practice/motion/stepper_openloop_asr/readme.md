# Open-loop stepper with motor position and soft-limit autosave

This example uses the PSI `ioc install` workflow and an incremental encoder
(`encoder.type: 0`). Position counter restoration is handled by the motor record.
Soft-limit restoration is a separate feature and can also be used without saving
position.

## Axis and startup configuration

`cfg/openloop.yaml` contains:

```yaml
axis:
  parameters: "restoreMotorSoftLims=1;"
epics:
  name: Axis1
  motorRecord:
    syncSoftLimits: true
```

The option belongs in `axis.parameters`, not in `epics.motorRecord`.
`restoreMotorSoftLims=1` also enables ongoing synchronization, even if the
`syncSoftLimits` YAML line is commented out or false. Writing that line explicitly
as `true` documents the intended behavior; it is not required by the restore
option. Keep other driver options in the same semicolon-separated string.

The startup script explicitly sets `ECMC_STARTUP_GATE=1`. Use an ECMC build with
the motor-record restore and complete startup gate implementation. Ordinary PLCs,
plugin cyclic execution and other motion producers must remain held until native
axis initialization and loaded motor-record restoration complete. Drives stay
disabled during the hold; early motion/enable requests are rejected. STOP,
disable, coordinate loading and status polling remain available. Axes with no
loaded motor record do not wait for one. The dedicated safety plugin continues
operating, and configuration/enter-RT initialization hooks still prepare runtime.

## Request file and restore passes

`cfg/MTEST04-MTN-ASM_pos.req` saves:

```text
MTEST04-MTN-ASM:Axis1.DVAL
MTEST04-MTN-ASM:Axis1.DLLM
MTEST04-MTN-ASM:Axis1.DHLM
```

Do not also restore `Axis1-CfgDLLM`/`Axis1-CfgDHLM` for this axis. They are another
writable interface to the same limits. The two dial fields do not preserve
independent soft-limit enable flags.

The PSI tool selects the two-pass setup for a filename ending in `_pos.req`.
For another filename, add `#ENABLE-PASS=2` to the request file. Verify that the
generated `saveRestore.script_restore` registers both actual autosave passes
**0 and 1** before `iocInit`:

```iocsh
set_pass0_restoreFile "MTEST04-MTN-ASM_pos.sav"
set_pass1_restoreFile "MTEST04-MTN-ASM_pos.sav"
```

The PSI directive's `2` means two-pass setup; there is no autosave pass 2 here.

## YAML versus saved limits

YAML initializes the motor's `.DLLM`/`.DHLM`; autosave overwrites them when those
fields are configured for restore. ECMC then uses that initialized pair:

- With saved dial limits: the restored limits override YAML.
- Without autosave restoring the dial limits: the standard generated motor fields
  keep their YAML-derived values, which are used by ECMC.
- Without `restoreMotorSoftLims=1`: ECMC seeds its configured limits into the motor
  at startup; saving the dial fields alone does not make them authoritative.

For example, YAML `-100, 100` and saved `-123, 123` should yield `-123, 123` after
startup. Inspect the `.sav`, not just the `.req`, to see the values to restore.
Autosave may have saved incorrect live values during an earlier failed test.

## Position policy and engineering units

`.DVAL` and the motor's `RSTM` control position restoration independently of
`restoreMotorSoftLims`. The `NearZero` default restores a nonzero saved position
when the initial readback is near zero according to the deadband; it does not
request restoration of a saved zero. An incremental encoder can independently
start at zero even when no position restore was requested.

The ECMC-specific motor template should set the engineering-unit flag from
loading, for example `field(MFLG, "$(MFLG=8)")`. The compatibility init hook also
sets that flag before motor-record initialization. MFLG mask 8 does not force
position zero or select a restore policy. Keep the real MRES value; do not replace
it with 1 to hide a units mismatch.

The ECMC startup compatibility workaround handles a stale motor `COMM_ALARM`
which otherwise prevents a deferred position load from reaching asyn. It acts
once on verified healthy startup status, under the record lock, preserving other
alarms and later runtime communication faults. It does not modify motorECMC.

## Startup check and temporary diagnostics

Test with a known nonzero saved position, for example `.DVAL 5`, and limits that
differ from YAML defaults. Confirm both restored values before the startup log
announces release of PLCs and motion command producers. Also verify startup with
no motor record and that an incomplete restore keeps motion held.

For initialization diagnostics, the example's `fieldInit: "SPAM=8"` enables motor
restore messages at record creation. This is temporary diagnostic verbosity;
remove it or set `SPAM=0` when no longer needed. Append `,SPAM=8` if other
`fieldInit` macro values are already present. Motor templates can instead expose
`field(SPAM, "$(SPAM=8)")` during investigation.

After loading the axis, before `iocInit`, temporarily enable both asyn ports:

```iocsh
asynSetTraceMask("MC_CPU1", -1, 0x41)
asynSetTraceMask("MCU1", 1, 0x51)
```

`MC_CPU1` carries ECMC's `SET_POSITION` messages; `MCU1` carries motor command
queueing. Enabling SPAM only with an `afterInit dbpf` misses initialization.
Return the trace masks to `0x1` after testing.

The Hugo manual has the complete guide at
`hugo/content/manual/motion_cfg/autosave.md`.
