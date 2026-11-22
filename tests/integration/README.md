# IOC integration tests

The [hardware-profile SIM IOC](hardware_profiles/README.md) adds a separate
10-axis simulated startup matrix covering EL5021, EL5042, EL5101/5102,
EL7031/7037/7041/7047, EL7062, and EL7201/7211/7221. It also runs
hardware-free tests through the real Jinja axis renderer and schema validator:

```sh
python3 tests/test_hardware_profile_sim.py -v
```

A live `SIM=1` IOC startup is optional; the offline checks do not access
EPICS or EtherCAT. The standalone fixture does not issue motion commands.

The [slit suite](slit/README.md) includes its own simulation IOC in `slit/ioc/`.
Shared external hardware models are in `tools/simulation/`. The standalone N6
integration scripts remain here as well.

From the ecmccfg root, inspect the plan without connecting to EPICS:

```sh
python3 tests/integration/slit/run.py
```

With the dedicated IOC already running, add `--prefix SIMSLIT: --run`.
`tests/run_tests.py` and `tests/run_simulation_checks.py` never run live cases.

For manual real-hardware commissioning, see [the hardware slit IOC](slit/ioc_hardware/README.md).

The separate [real-hardware slit suite](slit_hardware/README.md) supports bounded
normal moves and status checks against that hardware IOC. It is plan-only unless
`--run` is supplied and is never executed by the offline regression runners.

The slit homing module includes `test_ignore_disabled_motion_commands`: it
starts a home, injects disabled absolute/relative/velocity requests, checks
that homing finishes without an axis error, and verifies stop and kill.
It requires an ECMC build with `SetAxisIgnoreDisabledMotionCommands` and
runtime configuration commands permitted. Run only against the dedicated
simulation IOC (plan-only without `--run`):

```sh
python3 tests/integration/slit/run.py --help
```

The test restores all motion permissions and switches silent rejection off
before the homing fixture restores its reference. Live execution is separate
from offline test discovery.
