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
The initial defaults are **0.05 mm excursions around the recorded starting
position**, **0.1 mm/s**, **0.015 mm completion tolerance**, and an absolute test
envelope of **−10…+10 mm per physical blade**. Copy the profile and use
`--profile /path/to/profile.json` for different bounds/settings. Incremental
coordinates alone do not establish the physical travel range; verify the actual
positions and scaling before running motion tests.
The test envelope does not expand the IOC soft limits: the supplied hardware
configuration currently limits physical axes to −1…+1 mm, and those limits
continue to apply.

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
machine must already be enabled. The encoder-power group requires Auto power
mode with Force ON released and encoder power control enabled.

Only motor VAL, VELO and STOP are written. The suite uses the IOC's normal
auto-enable and brake policy, without resetting faults, homing, referencing,
changing soft limits, feedback modes, or powering relays directly. Successful
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
