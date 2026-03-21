+++
title = "PLC"
weight = 12
chapter = false
+++

## Topics
{{% children %}}
---

## Scope
ECMC PLCs provide deterministic real-time logic in the ecmc cycle for:
- EtherCAT I/O conditioning and interlocks
- axis synchronization and supervisory logic
- motion limit/home override logic
- derived signals and buffering workflows

## By Task
### Load and run PLC code
- Use classic text PLC loading:
```bash
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "FILE=<filename>, INC=<include_dirs>, SAMPLE_RATE_MS=<rate_ms>, PLC_MACROS='<custom_macros>'"
```
- Use YAML wrapper loading:
```bash
${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}loadYamlPlc.cmd, "FILE=./plc.yaml, ECMC_TMPDIR=/tmp/"
```

YAML PLC loading supports both parser backends:
- `jinja` (default, Python-based)
- `ecb` (C++ backend via `ECMC_CFG_TOOL=ecb`, see [ecb]({{< relref "/manual/motion_cfg/ecb.md" >}}))

### Understand language/syntax and available variables
- [syntax]({{< relref "/manual/PLC_cfg/syntax.md" >}}) for operators, declarations, comments, and macro rules.
- [variables]({{< relref "/manual/PLC_cfg/variables.md" >}}) for axis/ec/ds/plc variable namespaces.
- [patterns]({{< relref "/manual/PLC_cfg/patterns.md" >}}) for short practical PLC examples.
- [functions]({{< relref "/manual/PLC_cfg/functions.md" >}}) for the PLC helper function reference.

### Reuse PLC functions and shared code
- [function libs]({{< relref "/manual/PLC_cfg/function_libs.md" >}}) for `loadPLCLib.cmd`, function signatures, and constraints.

### Apply robust coding patterns
- [best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}}) for macros, include/substitute usage, printout strategy, declaration patterns, and exposing PLC variables as EPICS PVs.

## PLC Definition Styles
`ecmccfg` supports three styles:
1. Pure text PLC files (classic)
2. Pure YAML PLC definitions
3. YAML header + external text PLC file (recommended for complex PLCs)

### Pure YAML (minimal)
All keys are mandatory:
- `id`: unique PLC id (`uint`)
- `enable`: start enabled/disabled
- `rateMilliseconds`: execution rate in ms (`-1` means every cycle)
- `code`: list of PLC code lines

```yaml
plc:
  id: 1
  enable: no
  rateMilliseconds: 10
  code:
    - 'ec0.s2.binaryOutput07:=global.test|'
    - '${PLC_ID}.enable:=plc0.enable|'
    - 'ec0.s2.binaryOutput05:=not(ec0.s2.binaryOutput05)|'
```

### YAML Header + Text File
Use `file:` to keep large PLC logic in text files:
```yaml
plc:
  id: 1
  enable: yes
  rateMilliseconds: 10
  file: plc1.plc
```

{{% notice warning %}}
If `file` is set, entries in `code` are overwritten.
{{% /notice %}}

### Formatting Notes
{{% notice warning %}}
YAML is indentation-sensitive.
{{% /notice %}}

{{% notice tip %}}
Use 2-space indentation.
{{% /notice %}}

{{% notice note %}}
PLC statement line terminator remains `|` in YAML-based code lines.
{{% /notice %}}

## Recommended Reading Order
1. [syntax]({{< relref "/manual/PLC_cfg/syntax.md" >}})
2. [variables]({{< relref "/manual/PLC_cfg/variables.md" >}})
3. [patterns]({{< relref "/manual/PLC_cfg/patterns.md" >}})
4. [functions]({{< relref "/manual/PLC_cfg/functions.md" >}})
5. [best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}})
6. [function libs]({{< relref "/manual/PLC_cfg/function_libs.md" >}})
