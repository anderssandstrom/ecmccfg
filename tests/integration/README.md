# IOC integration tests

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
