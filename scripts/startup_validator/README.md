# ecmccfg startup validator

This package statically validates the IOC shell startup file that ecmc will
execute. It does not generate or replace IOC shell and has no runtime role.

```sh
./scripts/validate-startup startup.cmd
./scripts/validate-startup startup.cmd --format json
./scripts/validate-startup startup.cmd --warnings-as-errors
```

The wrapper changes to the repository root and invokes the Python package. The
equivalent developer command is `python3 -m scripts.startup_validator`.

The command exits with status `1` when errors are found and otherwise exits
with status `0`. `--warnings-as-errors` also makes warnings fail validation.

## Initial checks

- balanced EPICS macro expressions such as `${NAME}` and `$(NAME)`;
- unterminated quoted strings;
- malformed, invalid, empty, and duplicate script macros;
- missing files referenced by common file macros;
- use of the legacy `configureSlave.cmd` workflow;
- machine-readable JSON diagnostics for CI.

Local references are resolved relative to the startup file. Paths containing
EPICS macros cannot be resolved statically and are left for a later resolved-
macro validation phase.

The validator intentionally does not restrict available scripts, IOC shell
commands, PLCs, plugins, C++ logic, or `ecmcConfigOrDie` expressions.

## Planned increments

1. recursively inspect statically resolvable included startup files;
2. accept a macro-value file so more `${...}` paths can be resolved;
3. invoke the existing YAML validators for referenced axis/encoder/PLC files;
4. add optional, separately maintained lint policies for deprecated APIs and
   common ordering mistakes.
