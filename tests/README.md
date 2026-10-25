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

YAML comparison tests also require standalone ECB and the Python packages in
`environment.yml`. Build ECB with its standalone Makefile, then put `bin/ecb`
on PATH or set `ECB=/absolute/path/to/ecb`. CI pins ECB to commit
`79a9ef6c2c292efeb52adf7c45dbb30b114456b0` (1.6.0) and builds it with GCC;
this build does not require EPICS sources. On macOS, use `make -f Makefile LDLIBS=`
because Apple's standard library does not provide Linux's `libstdc++fs`.
ECB's Makefile calculates its build number from a local `main` branch. CI fetches
the history and names the pinned checkout `main` before compiling; without that
branch, ECB can build with an empty build number and abort when reading YAML.

Run only the generator comparisons with:

```sh
python3 -m unittest discover -s tests -p test_yaml_parity.py -v
```

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
- Database integrity across 31 configurations: unresolved macros, CALC/OCAL
  string limits and local record links (including shared master EcTool records).
- DS402 state decoding across all 65,536 statusword values using EPICS libCom.
- Database loading in softIoc, panel subscriptions and Qt UI compilation.
- Sequential slave loading: 98 combinations check that previous CSTCA/CSV
  configurations do not leak options into the next slave's defaults.
- Startup-validator regression cases.
- ECB versus Python/Jinja command generation for physical CSV, PSI CSP,
  virtual axes, macros, monitoring, optional defaults, homing, axis PLC files and settings
  and additional encoder configuration. Both must reject missing required
  trajectory settings and invalid velocity types.

Generator comparisons preserve command order, macros and string values. They
ignore comments and line indentation and normalize complete numeric arguments
to configuration commands (for example `20` and `20.0`). They do not execute
the generated IOC-shell scripts or prove identical runtime axis state.
Unknown-key handling deliberately differs: Python purges unknown keys while
ECB rejects them. A separate test records that policy difference.
Another test records that ECB 1.6.0 includes PLC-file `#` comments in appended
PLC expressions while Python removes them. These are explicit compatibility
differences, not evidence of full loader equivalence.

The three fixtures in `fixtures/yaml_parity` are taken from the pinned ECB
repository's `scripts/yaml/{pax1,vax1,vax2}.yaml`. The CSP test reads the PSI
example directly, so edits to that example are also checked.

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
