# SmarAct MCS2 in CSP Mode

This example shows a simple PSI-style startup for a SmarAct MCS2 EtherCAT slave
using YAML axis configuration.

It is based on the existing `examples/test/smaract/mcs2` setup, but reduced to
the parts that are useful as a reusable motion example:

- one linear axis on channel 1
- one rotary axis on channel 3
- CSP motion with `autoMode` switching between motion mode and drive homing
- homing sequence `26`, where the homing action is triggered inside the drive

## Files

- `startup.cmd`: loads the MCS2 slave, applies the actuator components, and
  loads two YAML axes
- `cfg/axis_lin.yaml`: linear stage example in `um`
- `cfg/axis_rot.yaml`: rotary stage example in `mdeg`

## Startup flow

```cmd
require ecmccfg "MASTER_ID=0,ENG_MODE=1"
${SCRIPTEXEC} ${ecmccfg_DIR}setRecordUpdateRate.cmd "RATE_MS=1"

epicsEnvSet(MCS2_SLAVE_NUM,15)
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=${MCS2_SLAVE_NUM}, HW_DESC=MCS2"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=SmarAct-SLC1750ds, CH_ID=1, MACROS='HOME_VELO=1000,HOME_ACC=1000'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=SmarAct-SR2013s,   CH_ID=2"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=SmarAct-SR2013s,   CH_ID=3, MACROS='HOME_VELO=10000,HOME_ACC=1000'"
```

Then the YAML axis files are loaded for channels 1 and 3.

## SmarAct-specific notes

- The example uses `autoMode` because SmarAct changes mode between normal CSP
  motion and homing.
- Homing uses `type: 26`, so ecmc triggers the drive-internal homing sequence
  and waits on the configured `ready` bit.
- The homing velocity and acceleration are actuator-specific and are configured
  through `applyComponent.cmd`, not in the axis YAML.
- `setRecordUpdateRate.cmd "RATE_MS=1"` is included because the MCS2 is usually
  commissioned with fast record updates.

## Running

Run from this directory:

```sh
iocsh.bash startup.cmd
```

Adjust `MCS2_SLAVE_NUM` and the actuator components if your EtherCAT topology
or connected positioners differ.
