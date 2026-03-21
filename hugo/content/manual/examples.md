+++
title = "Examples"
weight = 50
chapter = false
+++

## Reference scenarios (PSI best practice)
- **Motion** (`examples/PSI/best_practice/motion/`)
  - [Stepper BiSS-C](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_bissc) (EL7041/EL5042 and EL7062/EL5042)
  - [Stepper incremental, EL7047 + EL5102](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/el7047_el5102)
  - [Stepper incremental, EL7062](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/el7062)
  - [SmarAct MCS2](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/smaract/mcs2)
  - [Stepper open loop + autosave restore](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_openloop_asr)
  - [Stepper open loop + retries](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_openloop_mr_rtry_bissc)
  - [Stepper without motor record](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_bissc_no_mr)
  - [Servo CSV](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/servo/csv)
  - [Hardware substitution template](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_bissc_hw_subst)
- **Synchronization** (`examples/PSI/best_practice/motion/syncs/`)
  - [Slit synchronization](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/syncs/slit)
  - [Mirror synchronization](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/syncs/mirror)
- **PLC examples** (`examples/PSI/best_practice/plcs/`)
  - [Basic PLC examples](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/plcs/basic)
  - [Motion sequence PLC example](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/plcs/motion/stepper_bissc_forw_back_seq)

## Common scripts
- `addSlave.cmd`, `applyComponent.cmd`: add slaves and apply drive/encoder components
- `loadYamlAxis.cmd`: load axis YAML (physical/virtual)
- `configureVirtualAxis.cmd`: classic virtual axis config (legacy)
- `loadPLCFile.cmd`: load PLC from file; `loadYamlPlc.cmd` for YAML-defined PLCs

## Tips
- Prefer `examples/PSI/best_practice/` when you want a reusable starting point, and use `examples/test/` when you need lower-level or experimental reference setups.
- Keep drive SDO verification enabled; configure unused channels with `Generic-Ch-Not-Used`.
