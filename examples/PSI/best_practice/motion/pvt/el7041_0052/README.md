# PVT Example for EL7041-0052

This example shows a minimal PSI-style PVT/profile-move setup with one
stepper axis on an EL7041-0052 terminal.

It is reduced to the parts that are useful as a reusable best-practice
reference:

- one motion axis
- YAML-based axis configuration
- explicit `pvtControllerConfig.cmd` in startup
- motor-record PVT enabled through `epics.motorRecord.pvt`

## Files

- `startup.cmd`: loads the EL7041-0052, applies the motor component, loads the
  axis, and configures the PVT controller
- `cfg/axis.yaml`: axis configuration with `epics.motorRecord.pvt`

## Startup flow

```cmd
require ecmccfg "MASTER_ID=0,ENG_MODE=1"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230,STEPS=400'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,  "FILE=./cfg/axis.yaml, DEV=${IOC}, DRV_SLAVE=${ECMC_EC_SLAVE_NUM}"
${SCRIPTEXEC} ${ecmccfg_DIR}pvtControllerConfig.cmd
```

## PVT-specific notes

- PVT is enabled in YAML through:
  - `epics.motorRecord.pvt.npoints`
  - `epics.motorRecord.pvt.nreadback`
- The controller-level PVs are created with the `PVT-` prefix.
- Axis-specific PVs are created with the `<Axis>-PVT-` prefix, for example
  `Axis1-PVT-UseAxis` and `Axis1-PVT-Positions`.
- Calling `pvtControllerConfig.cmd` explicitly is recommended in startup files,
  even though `setAppMode.cmd` can auto-configure the controller if PVT-enabled
  axes are present.

## Running

Run from this directory:

```sh
iocsh.bash startup.cmd
```

Minimal example sequence:

```sh
caput <IOC>:PVT-NumPoints 7
caput <IOC>:PVT-NumPulses 5
caput <IOC>:PVT-MoveMode 0
caput <IOC>:Axis1-PVT-UseAxis 1
caput -a <IOC>:Axis1-PVT-Positions "0 1 2 3 4 3 2"
caput -a <IOC>:PVT-Times "1 1 1 1 1 1 1"
caput <IOC>:PVT-Build 1
caput <IOC>:PVT-Execute 1
```

Use fixed-time mode instead of `PVT-Times` if you want a constant point time
for the entire profile.
