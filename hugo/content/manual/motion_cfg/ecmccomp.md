+++
title = "ecmccomp"
weight = 25
chapter = false
+++

`ecmccomp` is the component library for ecmc.
It provides reusable component definitions (motors, encoders, and slave-specific configs) that are applied to EtherCAT slaves at IOC startup.

## What it is for
- Reusing validated motor, encoder, and slave configuration blocks across installations
- Keeping component parameters in engineering units and converting them to slave-specific SDO values
- Applying configuration consistently with built-in compatibility and macro validation

## Main entry point: `applyComponent.cmd`
The standard entry script is:

```bash
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP=<component-name>"
```

Typical arguments:
- `COMP`: component file name (required)
- `EC_COMP_TYPE`: hardware descriptor (for example `EL7037`); defaults from `addSlave.cmd` context
- `COMP_S_ID`: slave bus position; defaults from `addSlave.cmd` context
- `CH_ID`: channel index (default `1`)
- `MACROS`: optional component or slave macros

## What `applyComponent.cmd` does
`applyComponent.cmd` executes a fixed pipeline:
1. Loads component data (`${ecmccomp_DIR}${COMP}.cmd`).
2. Loads slave/type support data (`${ecmccomp_DIR}${EC_COMP_TYPE}_${COMP_TYPE}.cmd`).
3. Runs generic validation (`validateGeneric.cmd`).
4. Validates custom macros (`validateMacros.cmd`).
5. Runs component-type validation (`validate<COMP_TYPE>.cmd`).
6. Applies SDO/config script (`${SLAVE_SCRIPT}_${COMP_TYPE}.cmd`).
7. Runs cleanup scripts.

## Typical usage with `ecmccfg`
Use `ecmccomp` directly after `addSlave.cmd`:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=8, HW_DESC=EL7037"
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP=Motor-OrientalMotor-PK267JB-Parallel"
```

Explicit call variant:

```bash
${SCRIPTEXEC} ${ecmccomp_DIR}applyComponent.cmd, "COMP_S_ID=12,EC_COMP_TYPE=EL7037,COMP=Motor-OrientalMotor-PK267JB-Parallel,CH_ID=1,MACROS='I_MAX_MA=500,I_STDBY_MA=100'"
```

## Notes
- `ecmccomp` complements `ecmccfg`: use `ecmccfg` for system and axis startup flow, and `ecmccomp` for reusable component-level slave configuration.
- Supported macro sets depend on component and slave type; check the corresponding `.cmd` files in the `ecmccomp` repository.
