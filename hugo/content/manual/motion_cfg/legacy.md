+++
title = "legacy motion"
weight = 29
chapter = false
+++

## Scope

This page covers the older classic motion configuration flow that is still used
in many existing IOCs and in the `examples/ESS/` tree.

For new configurations, prefer the YAML-based workflow with
`loadYamlAxis.cmd`. The legacy flow is mainly relevant when:

- maintaining an existing IOC based on `.ax`, `.vax`, and `.sax` files
- reading or reusing older ESS examples
- migrating a classic configuration step by step instead of rewriting
  everything at once

## Main legacy entry points

- `configureAxis.cmd`
  configure one physical axis from a classic axis file
- `configureVirtualAxis.cmd`
  configure one virtual axis from a classic virtual-axis file
- `applyAxisSynchronization.cmd`
  apply synchronization logic from a classic sync file
- `configureSlave.cmd`
  older combined slave setup path
- `applySlaveConfig.cmd`
  apply a predefined slave configuration

## Classic file types

- `.ax`
  physical axis configuration
- `.vax`
  virtual axis configuration
- `.sax`
  synchronization between axes, often used for slit, mirror, or simple gear
  structures

Typical startup pattern:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}configureAxis.cmd, "CONFIG=./cfg/linear_1.ax"
${SCRIPTEXEC} ${ecmccfg_DIR}configureVirtualAxis.cmd, "CONFIG=./cfg/center.vax"
${SCRIPTEXEC} ${ecmccfg_DIR}applyAxisSynchronization.cmd, "CONFIG=./cfg/center.sax"
```

## ESS examples that use this flow

The `examples/ESS/` tree is the main reference for classic motion startup.
Typical patterns there include:

- standalone physical axes with `configureAxis.cmd`
- slit and mirror structures using `.ax + .vax + .sax`
- simple gear and synchronization examples using `applyAxisSynchronization.cmd`
- older combined slave setup with `configureSlave.cmd` and
  `applySlaveConfig.cmd`

Representative examples:

- `examples/ESS/mcu1025.script`
- `examples/ESS/mcu1024_slit/mcu1024.script`
- `examples/ESS/mcu1025_slit/mcu1025.script`
- `examples/ESS/mcu1021_coupler_simplegear/mcu1021_coupler.script`
- `examples/ESS/mcu1025_slitdemo/mcu1025.script`

## Relationship to the current YAML flow

The current preferred workflow is:

- slave setup with `addSlave.cmd` and `applyComponent.cmd`
- axis setup with `loadYamlAxis.cmd`
- PLC setup with `loadYamlPlc.cmd` or `loadPLCFile.cmd`

The legacy motion flow is still valid, but compared to YAML it has these
limitations:

- less structured validation
- less consistency between physical axes, virtual axes, and synchronization
- harder reuse across projects

## Practical migration advice

When updating an older IOC, do not try to migrate everything at once.

A practical order is:

1. keep the existing classic motion files running unchanged
2. replace old slave-specific setup with `applyComponent.cmd` where possible
3. migrate one axis at a time from `.ax` to YAML
4. migrate virtual/synchronized structures after the physical axes are stable

If the IOC is stable and there is no strong need for migration, it is often
better to keep the classic motion part as-is and only document that it is a
legacy configuration.
