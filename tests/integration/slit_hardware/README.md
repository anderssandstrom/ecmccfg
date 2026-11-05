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

The hardware IOC must include `hardware-test.db` from this change. Restart that
IOC after updating its startup file so `HWSLIT:HardwareSlitTest:Schema` exists.
The runner rejects SIM IOCs, missing fixture identity, wrong axis counts/IDs,
active faults/limits, moving axes, nonzero motor OFF/DIR, and SPMG other than Go
before writing. Physical and virtual targets must respect native soft limits and
the profile's physical envelope. Native soft limits must be enabled. The state
machine must already be enabled. Zero-reference preparation and the encoder-power group require Auto power
mode with Force ON released and encoder power control enabled.

Motion uses only motor VAL, VELO and STOP. Before motion preflight, a sleeping
BiSS encoder is temporarily woken using the axis `EncForceOn` inspection hold,
with the drive disabled. The runner waits for ready/primary selection and
motor/native coordinate agreement, captures all starting positions, then restores
the previous hold. With zero referencing disabled, fixed counter-only feedback mode is respected. The read-only
`status` group does not wake the encoder or write any PVs. The suite uses the IOC's normal
auto-enable and brake policy, without resetting faults, changing soft limits or feedback modes, or powering
relays directly. The optional zero-reference preparation also writes the two physical
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
