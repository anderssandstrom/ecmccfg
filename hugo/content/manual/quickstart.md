+++
title = "Quickstart"
weight = 2
chapter = false
+++

## Goal
Bring up an IOC with a single axis using the YAML-based configuration.

This page is intentionally short. For a more detailed walkthrough of the full
startup structure, see [introduction]({{< relref "/manual/introduction.md" >}}).
For reusable public examples, see [examples]({{< relref "/manual/examples.md" >}}).

## Prerequisites
- An EPICS IOC environment with compatible installed `ecmc`, `ecmccfg` and component-library modules; see [Build at PSI]({{< relref "/manual/build.md" >}}) for the PSI workflow.
- A local IOC configuration directory containing the startup script and its YAML files. Copy a complete [example]({{< relref "/manual/examples.md" >}}) that matches your hardware.
- For hardware operation: a working EtherCAT master, reachable slaves and the actual terminal positions. For a hardware-free start, use [SIM=1]({{< relref "/manual/general_cfg/ethercat/simulation.md" >}}).
- One YAML parser backend:
  - `jinja` (default): Python 3 with venv support. The loader creates a venv and installs PyYAML, Jinja2 CLI, yamllint and Cerberus on first use; package access must be available then.
  - `ecb`: C++ backend (`ECMC_CFG_TOOL=ecb`, see [ecb](../motion_cfg/ecb/))

## Steps
1. Load the module version you want:
   ```bash
   epicsEnvSet("IOC", "MYIOC")
   require ecmccfg <VERSION>
   ```
2. Add the coupler and the relevant slaves (example: coupler + EL1018 + EL7031):
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EK1100"
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL1018"
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL7031"
   ```
3. Apply a component configuration to the drive terminal:
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000, I_STDBY_MA=100, U_NOM_MV=24000, R_COIL_MOHM=1230'"
   ```
4. Load the axis YAML from your copied example. For the terminal order above the drive is slave 2. If the YAML uses `DRV_SLAVE`, `ENC_SLAVE` and `ENC_CHANNEL`, pass:
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/ax1.yaml, DEV=${IOC}, DRV_SLAVE=2, ENC_SLAVE=2, ENC_CHANNEL=01"
   ```
   Match the macro names to the YAML: some examples use `DRV_SID`/`ENC_SID`
   instead. Using the drive counter as feedback gives open-loop load control;
   an external encoder needs its own configured terminal and link. The
   [complete YAML reference]({{< relref "/manual/motion_cfg/axisYamlExample.md" >}})
   includes alternatives and is not a minimal file to run unchanged.
5. Start the IOC from the directory containing its startup file, using the local launcher, for example:
   ```bash
   iocsh startup.cmd
   ```
   Check for `iocRun: All initialization complete`, the master OK PV and
   `MCU-AppMode=1`. If the shell prompt appears without initialization, check
   whether the launcher invoked `iocInit`; `finalize.cmd` is registered at init.
6. Inspect native axis errors, limits and motor status before a small move.
   Verify feedback scaling/direction and motion completion. Motor-record target
   writes start motion; the optional [native target-write mode]({{< relref "/manual/motion_cfg/native_target_write.md" >}})
   can also start motion without a separate EXECUTE command.

## Next steps
- See [motion cfg](../motion_cfg/) for scaling, direction, and homing
- See [PLC cfg]({{< relref "/manual/plc_cfg/_index.md" >}}) for PLC hooks and synchronization
- See [examples]({{< relref "/manual/examples.md" >}}) for best-practice example trees
- See [troubleshooting](../knowledgebase/troubleshooting/) for common startup issues

## Try the simulation fixture

The dedicated slit fixture keeps the IOC, external plant and integration cases
in `tests/integration/slit/`. From the repository root, start its IOC in one
terminal:

```bash
cd tests/integration/slit/ioc
iocsh startup.cmd
```

Then run the plant and tests from the repository root in another terminal:

```bash
python3 tests/integration/slit/run.py --prefix SIMSLIT: --run
```

Install the runner's PyEPICS dependency and use compatible installed modules;
see `tests/integration/slit/README.md` for its full setup. `SIM=1` provides
memory I/O, while the Python plant supplies drive and encoder dynamics.
`MASTER_ID=-1` alone does not create that simulated I/O.
