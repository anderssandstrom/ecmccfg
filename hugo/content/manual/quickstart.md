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
- `hugo/Readme.md` steps completed (repo cloned, prerequisites installed)
- Working EtherCAT master and reachable slaves
- One YAML parser backend:
  - `jinja` (default): Python 3 with `jinja2` (auto-installed by the axis loader)
  - `ecb`: C++ backend (`ECMC_CFG_TOOL=ecb`, see [ecb](../motion_cfg/ecb/))

## Steps
1. Load the module version you want:
   ```bash
   require ecmccfg <optional VERSION>
   ```
2. Add the coupler and the relevant slaves (example: coupler + EL1018 + EL7062):
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EK1100"
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL1018"
   ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=EL7062"
   ```
3. Apply a component configuration to the drive terminal:
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000, I_STDBY_MA=100, U_NOM_MV=24000, R_COIL_MOHM=1230,L_COIL_UH=500'"
   ```
4. Load a YAML axis configuration (adapt paths/macros):
   ```bash
   ${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/ax1.yaml, DEV=${DEV}, DRV_SLAVE=4, ENC_SLAVE=3, ENC_CHANNEL=01, ECMC_TMPDIR=/tmp/"
   ```
5. Start the IOC and verify PVs:
   - Check motor record status (unless disabled in YAML)
   - Jog a small move and confirm encoder feedback

## Next steps
- See [motion cfg](../motion_cfg/) for scaling, direction, and homing
- See [PLC cfg]({{< relref "/manual/PLC_cfg/_index.md" >}}) for PLC hooks and synchronization
- See [examples]({{< relref "/manual/examples.md" >}}) for best-practice example trees
- See [troubleshooting](../knowledgebase/troubleshooting/) for common startup issues
