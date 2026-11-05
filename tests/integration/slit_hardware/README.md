# Real slit hardware acceptance tests

This suite uses the [hardware IOC](../slit/ioc_hardware/README.md), with TR_LO
using its drive counter and TR_HI using BiSS plus counter auto-power handover.
It does not run a simulated plant or write EtherCAT input images. Python 3 and
`pyepics` are required on the client for live runs.

From the ecmccfg root, list the tests without connecting:

```sh
python3 tests/integration/slit_hardware/run.py
```

Review `profile.json` against the commissioned mechanics and coordinate system.
By default, `reference_to_zero: true` references the current physical positions
to zero before motion tests. This sets encoder coordinates without seeking a
switch or moving the motors. Both drives must be disabled and stationary.
The suite powers and validates BiSS, writes zero to the physical axes' native
`TR_LO-SetEncPosCmd` and `TR_HI-SetEncPosCmd` PVs, synchronizes motor targets,
and verifies the tracking counter inherits zero
before BiSS powers down. Set `reference_to_zero: false` to retain existing
coordinates instead. The status-only group never changes references.
The initial defaults are **5 mm excursions around the zero reference (or captured starting
position when zero referencing is disabled)**, **1 mm/s**, **0.015 mm completion tolerance**, and a test
window of **−10…+10 mm relative to each blade's measured startup position**. Copy the profile and use
`--profile /path/to/profile.json` for different bounds/settings. Incremental
coordinates alone do not establish the physical travel range; verify the actual
positions and scaling before running motion tests.
For example, a physical axis starting at 35 mm gets a test window of 25…45 mm.
Each normal round trip commands origin +5 mm, origin −5 mm, then origin; the
middle leg therefore travels 10 mm. The move timeout is 30 seconds.

The IOC's absolute soft limits remain separate and are checked before every
motor target. The supplied hardware YAML currently sets −10…+10 mm; configure
these for the machine's actual absolute travel if its starting coordinate lies
elsewhere. The runner does not shift, disable or expand these limits. Zero referencing changes
encoder coordinates; it does not change the numerical soft-limit settings. An invalid
planned target fails preflight without a motor write. Existing custom profiles
without `relative_to_start: true` retain absolute-envelope interpretation.

Start with read-only status checks:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case status
```

Then run physical moves, or all groups:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case motion
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run
```

Use `--case virtual`, `--case encoder_power`, or `--test motor_stop` to narrow
execution. Multiple `--case` and `--test` arguments are supported. The suite
runs each case once in the configured feedback mode; it does not switch the
hardware to simulated open/closed-loop variants.

| Group | What is checked |
| --- | --- |
| `status` | Real backend, fixture identity, bus/application state, axis IDs, stopped motor/native status, no faults/warnings, coordinate agreement, virtual feedback kinematics |
| `motion` | Each physical axis moves both directions and returns; repeated motor targets; STOP while busy and no subsequent movement; motor/native completion, atTarget and faults |
| `virtual` | Center and gap move both directions and return; predicted blade targets stay in the test envelope; physical/virtual feedback agrees |
| `encoder_power` | A normal HI move settles, BiSS powers off and counter becomes primary; the next move restores power/readiness/BiSS primary and completes |
| `native` | LO and HI native absolute and relative moves using the execute PV, with native parameters restored |
| `target_write` | LO and HI absolute and repeated identical relative target writes; staging and mode selection do not move; direct writes auto-enable a disabled drive without an execute pulse |
| `motor` | LO and HI positive/negative OFF and both DIR values; user/dial/native positions and unchanged native limits; original fields and limit-sync policy restored |
| `brake` | LO/HI EL2008 brake outputs: amplifier/brake opening and closing order, release during motion and STOP deceleration, application after auto-disable |
| `no_sm` | Physical motor moves/STOP, native, target-write, OFF/DIR, encoder sleep/wake and PVT repeated with the master/slave state machine disabled; virtual axes remain disabled, uncommanded physical axes stay stationary |
| `pvt` | LO and HI profile Build/Execute/Readback, measured excursions both ways and return to start, controller success and fault checks |

Repeated targets use ordinary asynchronous writes while the first move
completion request remains active; the runner still checks motor/native idle,
atTarget and final position. It does not queue extra put-notify requests on
the same active motor record.

The hardware IOC must include `hardware-test.db` from this change. Restart that
IOC after updating its startup file so `HWSLIT:HardwareSlitTest:Schema` exists.
The runner rejects SIM IOCs, missing fixture identity, wrong axis counts/IDs,
active faults/limits, moving axes, nonzero motor OFF/DIR, and SPMG other than Go
before writing. Physical and virtual targets must respect native soft limits and
the profile's physical envelope. Native soft limits must be enabled. The state
machine must already be enabled. Zero-reference preparation and the encoder-power group require Auto power
mode with Force ON released and encoder power control enabled.

There are 49 live hardware cases (26 with state-machine management and 23 standalone repeats). Select the added groups independently:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case native --case target_write --case motor
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case pvt
```

The native groups use the axis command/target/enable PVs. `target_write` selects
`Cfg.SetAxisAutoExec`, checks its status bit, and triggers by writing the target
alone. Both native groups restore the original command fields, target-write mode
and MCU-Cmd transport settings, leaving their axes disabled on exit. Native
moves explicitly synchronize motor targets afterwards.

The motor coordinate cases treat requested positions and travel envelopes as
native dial coordinates. They derive user targets from `user = OFF + sign* dial`
and independently check user RBV/DVAL and native feedback. They temporarily turn
off motor/native soft-limit synchronization, then restore DIR, OFF, FOFF and that
policy after STOP; they do not alter numerical native soft limits.

PVT uses the existing asyn profile interface and requires the updated axis YAML
with `epics.motorRecord.pvt` on all four axes. **Restart the hardware IOC after
deploying those YAML files.** The shared controller is configured automatically
by the normal ecmccfg finalization path. Each test moves one physical axis through
a six-point, fixed-time profile with repeated endpoints, then reads the profile
back. Its default excursion is half the normal step (2.5 mm), with duration
chosen to respect configured velocity and motor ACCS. Cubic interpolation
extrema are checked against native/motor/travel limits before Build, not just the
supplied points. Trigger cases also check the linked EL2008 output. PVT selection, timing,
command fields and previously populated arrays are restored; empty input arrays
remain scratch buffers. Failures request profile Abort and motor STOP. Missing
PVT records are detected before zero-reference/setup writes.

The original `motion` and `virtual` groups use motor VAL, VELO and STOP. Before motion preflight, a sleeping
BiSS encoder is temporarily woken using the axis `EncForceOn` inspection hold,
with the drive disabled. The runner waits for ready/primary selection and
motor/native coordinate agreement, captures all starting positions, then restores
the previous hold. With zero referencing disabled, fixed counter-only feedback mode is respected. The read-only
`status` group does not wake the encoder or write any PVs. The suite uses the IOC's normal
auto-enable and brake policy. Tests do not reset faults, change numerical soft
limits or feedback selection, or power relays directly. Native target-write mode
and motor coordinate changes are confined to their cases and restored. The optional zero-reference preparation also writes the two physical
`-SetEncPosCmd` PVs and motor SYNC, and intentionally keeps the new references.
It does not write zero to the virtual axes; their feedback follows the PLC
kinematics, and their motor targets are synchronized afterwards.
It never starts a homing search or enables a drive. Successful
motion cases return to their captured origins; on failure/interruption it stops
all coupled axes and restores changed motor velocities without commanding a
return move. Amplifier disable and encoder power-off follow the existing IOC
configuration. A failed check stops the suite.

JSON and JUnit XML reports are written to `test-results/slit-hardware/` by
default; use `--report /path/report.json` to choose another location. Reports
include per-test status snapshots, failure details, completed move traces and
cleanup errors. These are client-side checks through EPICS; they cannot prove
real-time timing or independently measure physical motion of the counter-only
axis. They have not yet been run against the physical rack.


Run only the standalone cases with:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case no_sm
```

`no_sm` is included in the default full run. Use `--test pvt`, `--test native`,
`--test target_write`, or another name substring to narrow that group.
Each standalone case stops and disables all four axes, saves and disables
`SM00-EnaCmd`, and selects internal trajectories for both physical axes before
motion. During execution it verifies that management remains disabled/idle,
virtual axes remain disabled/idle, and the other physical axis stays stationary.
The PLC continues to calculate virtual feedback, which is checked as usual;
virtual motion is only tested with management enabled. On success, failure or
interruption, STOP and drive disable precede restoration of the physical
trajectory sources and state-machine enable. Failed restoration is retried by
runner cleanup and reported if it still fails. No automatic return move is made
after a failure. The suite still requires the state machine enabled at entry.


Brake output tests:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case brake
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case no_sm --test brake
```

Six cases run in each state-machine mode. They read `m0s005-BO01-RB` (LO)
and `m0s005-BO02-RB` (HI), where 1 releases the brake, together with the
EL7041/EL7031 amplifier command readbacks at slaves 14/12. These are the
existing hardware YAML mappings with 250-cycle opening and 200-cycle
close-ahead delays at 1 kHz. Enable-only cases observe amplifier-on/brake-applied
before release, and brake-applied/amplifier-on before switch-off. Motion and
STOP cases verify release while moving, normal auto-disable application and a
return to the origin. Missing output readbacks fail preflight before setup writes.
Tests command the axis enable, motor move and STOP interfaces; they never write
to brake output PVs directly. The checks verify commanded process-image outputs;
there is no independent mechanical brake or relay-contact feedback configured.


PVT trigger cases run on LO and HI, with and without state-machine management:

```sh
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case pvt --test triggers
python3 tests/integration/slit_hardware/run.py --prefix HWSLIT: --run --case no_sm --test triggers
```

These request three pulses at profile points 3, 4 and 5 and check
`PVT-SftTrg` resets to zero, increases without decreasing or exceeding the
request, and finishes at three. Profile readback must contain exactly three
pulse-latched encoder samples near the positive excursion, negative excursion
and return coordinate. Trigger parameters are restored on exit. Both fixtures
link `ec0.s5.binaryOutput05.0` (EL2008 slave 5, channel 05), active high with
400 ms pulses. The tests require `m0s005-BO05-RB` low before execution, observe
three high/low pulse pairs, and require low after completion or abort. Untriggered
profiles must keep it low. Edge observations are included in the JSON trace.
No direct output writes are made. These checks observe the EtherCAT output
process image; electrical pulse timing requires independent input/counter or
oscilloscope feedback. Brake channels 01/02 and simulation encoder supply
channels 03/04 retain their assignments.
Deploy the corrected `ecmcPVTTrigger.template` and restart the IOC for its
software-trigger forward link fix (`FLNK`, previously incorrectly written to `TSE`).
