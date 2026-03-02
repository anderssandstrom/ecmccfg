+++
title = "ecmccomp"
weight = 25
chapter = false
+++

`ecmccomp` is the component library for ecmc.
It provides reusable component definitions (motors, encoders, and slave-specific configs) that are applied to EtherCAT slaves at IOC startup.

## What It Is Good For
- Reusing validated motor/encoder/slave configuration blocks across installations.
- Keeping component parameters in engineering units, then converting to slave-specific SDO values.
- Applying configuration consistently with built-in compatibility and macro validation.

## Main Entry Point: `applyComponent.cmd`
The standard entry script is:

```iocsh
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP=<component-name>"
```

Typical arguments:
- `COMP`: Component file name (required).
- `EC_COMP_TYPE`: Hardware descriptor (for example `EL7037`); defaults from `addSlave.cmd` context.
- `COMP_S_ID`: Slave bus position; defaults from `addSlave.cmd` context.
- `CH_ID`: Channel index (default `1`).
- `MACROS`: Optional component/slave macros.

## What `applyComponent.cmd` Does
`applyComponent.cmd` executes a fixed pipeline:
1. Loads component data (`${ecmccomp_DIR}${COMP}.cmd`).
2. Loads slave/type support data (`${ecmccomp_DIR}${EC_COMP_TYPE}_${COMP_TYPE}.cmd`).
3. Runs generic validation (`validateGeneric.cmd`).
4. Validates custom macros (`validateMacros.cmd`).
5. Runs component-type validation (`validate<COMP_TYPE>.cmd`).
6. Applies SDO/config script (`${SLAVE_SCRIPT}_${COMP_TYPE}.cmd`).
7. Runs cleanup scripts.

## Typical Usage With `ecmccfg`
Use `ecmccomp` directly after `addSlave.cmd`:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=8, HW_DESC=EL7037"
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP=Motor-OrientalMotor-PK267JB-Parallel"
```

Explicit call variant:

```iocsh
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP_S_ID=12,EC_COMP_TYPE=EL7037,COMP=Motor-OrientalMotor-PK267JB-Parallel,CH_ID=1,MACROS='I_MAX_MA=500,I_STDBY_MA=100'"
```

## Notes
- `ecmccomp` complements `ecmccfg`: use `ecmccfg` for system/axis startup flow and `ecmccomp` for reusable component-level slave configuration.
- Supported macro sets are component/slave-type dependent; check each component/slave `.cmd` file in the `ecmccomp` repository.
