# Dedicated slit simulation acceptance configuration

This directory is separate from `../slit_matrix` and never loads its startup
script. It retains physical axes TR_LO/TR_HI (5/6), virtual CENTERY/GAPY (12/13),
slit kinematics and the master/slave state machine, while declaring only the
terminals needed by those axes. Both blades have a second EL5042 encoder and
injectable status-word hardware limits. Soft limits are +/-1 mm. Original
`slit_matrix` files are unchanged.

Run from this directory with your usual launcher:

```sh
iocsh startup.cmd
```

Defaults: IOC/PV namespace SIMSLIT:, SIM=1, ENG_MODE=1, 1000 Hz. The environment
macros TEST_IOC, ECMCCFG_TEST_VER and ECMC_TEST_VER can override IOC name/versions;
versions default to sandst_a. Use current ecmccfg/ECMC with simulation records and
the MCU-Cfg-Sim-Mode metadata PV installed. No real EtherCAT master is claimed.

In the ECMC repository, list or execute modular tests:

```sh
python3 tools/simulation/slit_test/run.py --config /path/to/this/directory
python3 tools/simulation/slit_test/run.py --prefix SIMSLIT: --run --case feedback --loop closed
python3 tools/simulation/slit_test/run.py --prefix SIMSLIT: --run --case limits
python3 tools/simulation/slit_test/run.py --prefix SIMSLIT: --run
```

Pass --config if the two repositories are not siblings in the normal workspace.
The runner owns the drive/EL5042 model and checks this configuration's schema
marker before issuing writes. Do not run another simulator on slaves 9/12/14.
Full test semantics, scaling, fault injection and JSON/JUnit report instructions
are in ECMC `tools/simulation/slit_test/README.md`.

The plant/testing infrastructure was checked offline; this configuration and
its acceptance scenarios still need their first live IOC run. Real distributed
clock timing and physical motor dynamics are not represented.

Brake tests are a separate selectable module:

```sh
python3 tools/simulation/slit_test/run.py --prefix SIMSLIT: --run --case brake
```

Restart the test IOC after this configuration update. Simulated EL2008 slave 5
output 01 controls the LO brake and output 02 controls the HI brake. Output 0
means applied, 1 released. Both axes enable the production brake state machine;
opening delay is 250 cycles and close-ahead delay is 200 cycles at 1000 Hz.
The runner observes these native output PVs; it never writes brake values to
manufacture a pass. CA checks functional sequence windows, while the existing
ECMC C++ brake tests cover exact cycle boundaries. The plant does not model
brake mechanics or coil/armature feedback.

Configuration schema 2 adds the EL70xx drive alarm/reset links: drive status
bit 3 is alarm 0, control bit 1 is reset. A drive-fault injection is expected
to latch ERROR_DRV_HW_ALARM_0 (0x1460e). Restart this IOC after updating the
configuration; the runner rejects an older schema marker before issuing writes.
