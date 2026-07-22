+++
title = "Startup Validator"
weight = 17
chapter = false
+++

## Purpose

The startup validator checks an existing ecmc IOC startup file before the IOC
executes it. It does not generate configuration, replace IOC shell, or limit
which ecmc features can be used.

The validator is an optional development and deployment aid. It is not needed
at IOC runtime.

## Run The Validator

From the root of the `ecmccfg` source tree:

```bash
./scripts/validate-startup startup.cmd
```

To validate a startup file elsewhere in the repository:

```bash
./scripts/validate-startup path/to/startup.cmd
```

Successful validation produces a summary similar to:

```text
0 error(s), 0 warning(s), 5 script call(s)
```

The exit status is:

- `0` when validation succeeds
- `1` when validation errors are found

This allows the validator to be used from a local build or deployment script:

```bash
if ! ./scripts/validate-startup ioc/startup.cmd; then
    echo "Startup validation failed"
    exit 1
fi
```

## Available Options

Show command help:

```bash
./scripts/validate-startup --help
```

Generate machine-readable JSON diagnostics:

```bash
./scripts/validate-startup startup.cmd --format json
```

Treat warnings as validation failures:

```bash
./scripts/validate-startup startup.cmd --warnings-as-errors
```

## Checks

The initial validator checks:

- balanced EPICS macro expressions such as `${NAME}` and `$(NAME)`
- unterminated quoted strings
- malformed and invalid script macro items
- duplicate macros in one script call
- missing locally referenced configuration files
- use of the legacy `configureSlave.cmd` workflow

Every diagnostic contains the startup filename, line, column, severity, and a
stable diagnostic code. For example:

```text
/path/startup.cmd:12:46: error E301: referenced file does not exist: cfg/missing.yaml
```

## Supported Startup Syntax

The validator recognizes the normal ecmccfg script-execution forms, including:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=2,HW_DESC=EL7047"
```

and:

```bash
iocshLoad("./custom.cmd", "DEV=${IOC}")
```

Arbitrary IOC shell commands remain valid, including PLC, plugin, C++ logic,
and `ecmcConfigOrDie` configuration. The validator does not maintain a separate
model of the complete ecmc command API.

## Path Resolution And Limitations

Local file references are resolved relative to the startup file being
validated. A literal reference such as:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/axis.yaml"
```

can therefore be checked immediately.

A path containing an unresolved EPICS macro cannot yet be resolved statically:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=${AXIS_CONFIG}"
```

Such paths are left for IOC startup. Future validator versions may accept a
macro-value file and recursively inspect statically resolvable included startup
files.

The validator performs static checks only. It cannot verify the connected
EtherCAT topology, SDO behavior, plugin loading, or realtime execution.

## Python Entry Point

The `validate-startup` wrapper is the recommended interface. Its equivalent
Python package command is:

```bash
python3 -m scripts.startup_validator startup.cmd
```

The wrapper changes to the repository root before running that command, which
makes it easier to invoke consistently from another directory.

## Related Pages

- [startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [iocsh utilities]({{< relref "/manual/general_cfg/iocsh_utils.md" >}})
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting/_index.md" >}})
