+++
title = "ecb"
weight = 26
chapter = false
+++

`ecb` (ECMC Configuration Builder, `../ecb`, https://github.com/paulscherrerinstitute/ecb) is a C++ YAML validation/rendering tool that can be used as backend for ecmccfg YAML loaders.

## What It Is Good For
- Validating YAML data against schema definitions.
- Rendering ecmccfg Jinja-style templates without the Python venv pipeline.
- Reading/updating YAML keys (`readkey`, `updatekey`) used by loader scripts.

## How It Fits With `ecmccfg`
`ecb` is used by `loadYamlAxis.cmd`, `loadYamlPlc.cmd`, and `loadYamlEnc.cmd` when:

```iocsh
epicsEnvSet(ECMC_CFG_TOOL, "ecb")
```

The ecb module startup file sets this automatically.

`ecmccfg` still provides schema and template files (for example `ecbSchema.json`, `axis_main.jinja2`, `plc.jinja2`); `ecb` is the validation/rendering engine.

## Notes
- Default backend remains `jinja` if `ECMC_CFG_TOOL` is not set to `ecb`.
- Using `ecb` avoids Python venv/pip dependency during YAML parsing.
- `ecb` supports the subset of Jinja syntax needed by ecmccfg templates (implemented via Inja, with ecb-specific compatibility handling).
- For CLI details and schema behavior, see `../ecb/doc/ecb.md`.
