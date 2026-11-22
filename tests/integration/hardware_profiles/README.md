# Hardware-profile integration: dedicated SIM IOC

This fixture exercises **axis hardware profile selection**, not physical EtherCAT
or motor characteristics. It is separate from the behavioural slit simulator:
`tests/integration/slit/`.

## Coverage

The 10 simulated axes combine 13 terminal configurations. The matrix in
[`matrix.json`](matrix.json) and `ioc/startup.cmd` covers:

| Axis | Drive | Encoder | Expected selection |
| --- | --- | --- | --- |
| S7031 | EL7031 | EL7031 | CSV open-loop |
| S7037 | EL7037 | EL5021 | CSV + Sin/Cos 1 Vpp |
| S7041 | EL7041-0052 | EL5042 ch 1 | CSV + BiSS-C |
| S7047 | EL7047 | EL5102 ch 2 | CSV + incremental |
| S7201 | EL7201 resolver | EL7201 resolver | CSV |
| S7211 | EL7211-9014 STD | Same terminal | CSV |
| S7221 | EL7221-9014 STD | EL5101 | CSV + incremental |
| S7062A | EL7062 ch 1 | Internal open-loop | CSV, normal limits |
| S7062B | EL7062 ch 2 | Secondary incremental | CSV, swapped limits |
| S7211C | EL7211-9014 CSP STD | Same terminal | CSP |

The test uses **the real `EcmcAxis` Jinja renderer and schema validator**,
not a replacement profile resolver. Offline assertions check the generated
ECMC configuration commands and PDO links, selected feedback, channels,
limit swapping, and rejection of inconsistent CSV/CSP settings.

Run these tests without an IOC or EtherCAT:

```sh
python3 tests/test_hardware_profile_sim.py -v
# or with the usual offline regressions:
python3 tests/run_tests.py --verbose
```

## Optional live simulation IOC

Only use the dedicated SIM IOC after installing the feature branch alongside
an ECMC build that supplies the simulation backend:

```sh
cd tests/integration/hardware_profiles/ioc
iocsh startup.cmd
```

`SIM=1` creates virtual EtherCAT slaves and axes with the private
`SIMPROFILES:` prefix; no physical bus is requested. Use `TEST_IOC`,
`ECMCCFG_TEST_VER` and `ECMC_TEST_VER` to select installed module versions.
The fixture only configures axes and a few simulated status values.
**No moves or motor enable requests are issued automatically.**

The standalone simulation IOC is a **startup/configuration smoke fixture**.
A live IOC execution and complete simulated motor/plant feedback tests have
not yet been performed. The existing slit test suite remains responsible
for limit-trigger, motion, brake and closed-loop behavioural scenarios.
The new offline test verifies generated links; it does **not** prove that a
particular EtherCAT firmware PDO layout or electrical input polarity is safe.

CSP, EL72xx OPT and EL7062 OPT have different PDO configurations. The
matrix deliberately includes one STD CSP variant and rejects incompatible
CSV-vs-CSP combinations. Option-driven layouts and real firmware still
need separate integration validation. EL7062 input mapping and limit polarity
must be checked before using any physical motor.

All scales and `ONE.0` limit sources in these samples are **simulation
placeholders** and are not a safe physical motion configuration. The
`axis_el7062.yaml` example uses registered `binaryInputsXX` entries;
a swap changes input assignment, not polarity.

## Updating coverage

Add terminals in `matrix.json`, configure them with `addSlave.cmd` in
`ioc/startup.cmd`, and load one of the axis YAML fixtures with the
appropriate `epicsEnvSet` selectors. Keep the offline test's
`component_type()` fixture map aligned with the hardware script's actual
`ECMC_EC_COMP_TYPE`. Add negative cases for unsupported channels, unavailable
input PDOs, and incompatible drive modes.
