# Hardware-free regression tests

Run from the repository root:

```sh
python3 tests/run_tests.py --verbose
```

The runner collects the configuration tests here and the startup-validator
tests in `scripts/startup_validator/tests`. The existing Jinja pytest suite
remains in its separate workflow.

## Dependencies

Python runs the basic checks without EPICS. For all checks, install EPICS Base
(`msi`, `softIoc`, and `libCom`) and Qt's `uic`. No EPICS source checkout,
ecmc build, EtherCAT master, or connected hardware is required.

With Conda (or equivalent Micromamba commands):

```sh
conda env create -f tests/environment.yml
conda activate ecmccfg-tests
```

Activation adds the EPICS tools to PATH. On Ubuntu, install Qt tools with:

```sh
sudo apt-get install qtbase5-dev-tools
export PATH="/usr/lib/qt5/bin:$PATH"
python3 tests/run_tests.py --verbose --strict
```

On other systems, put the installed Qt `uic` (or `uic-qt5`) on PATH. An existing
EPICS installation also works; the environment file is optional locally.
The tests support both Linux `libCom.so` and macOS `libCom.dylib`.

Without `--strict`, checks with missing external tools are reported as skipped.
With `--strict`, any skip fails the run, so missing dependencies cannot silently
reduce CI coverage.

## GitHub Actions

`.github/workflows/hardware-free-tests.yml` runs on pushes, pull requests and
manual dispatch. It installs cached, prebuilt
[conda-forge EPICS Base packages](https://anaconda.org/conda-forge/epics-base)
using [setup-micromamba](https://github.com/mamba-org/setup-micromamba), installs
Qt tools, then runs the strict suite. Python and EPICS versions are specified
in `environment.yml`; transitive dependencies are resolved by Conda.

## Coverage and limits

- Optional PDO mappings and rejected option combinations for Ex72xx, Ex7411
  and Ex7062 hardware configurations.
- EPICS macro expansion, record names and references, scaling and setpoints.
- DS402 state decoding across all 65,536 statusword values using EPICS libCom.
- Database loading in softIoc, panel subscriptions and Qt UI compilation.
- Sequential slave loading: 98 combinations check that previous CSTCA/CSV
  configurations do not leak options into the next slave's defaults.
- Startup-validator regression cases.

The configuration harness interprets the supported IOC-shell commands; it is
not a complete IOC-shell or ecmc implementation. Database checks do not start
hardware communication or prove real-time behavior.

## Suggested next tests

1. Run representative configurations through a real ecmc IOC in simulation
   mode to catch command syntax or API changes missed by the Python harness.
   This would be a separate integration job with prebuilt ecmc dependencies.
2. Generate representative axis configurations from the PSI YAML examples and
   validate the resulting startup scripts and databases end to end.
3. Check the installed configuration tree, including referenced scripts,
   templates and panels, to catch files omitted from packaging.
4. Compare selected PDO layouts against versioned vendor ESI fixtures to catch
   incorrect indices, sizes and channel offsets independently of the scripts.
