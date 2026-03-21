+++
title = "Grbl Plugin"
weight = 18
chapter = false
+++

## Scope
The Grbl plugin is used for NC/G-code style motion workflows on top of ecmc axes.

Use it when:

- motion should be driven from G-code or an NC-style frontend
- axis roles such as `X`, `Y`, `Z`, and spindle should be mapped into one controller layer

## Common Interface

The Grbl plugin follows the normal [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}}).

The current plugin index documents the typical config keys:

- `DBG_PRINT`
- `X_AXIS`
- `Y_AXIS`
- `Z_AXIS`
- `SPINDLE_AXIS`
- `AUTO_ENABLE`
- `AUTO_START`

These axis-role mappings are the key plugin-specific part of the startup config.

The plugin README also verifies PLC helper functions such as:

- `grbl_set_execute(...)`
- `grbl_mc_halt(...)`
- `grbl_mc_resume(...)`
- `grbl_get_busy()`
- `grbl_get_parser_busy()`
- `grbl_get_code_row_num()`
- `grbl_get_error()`
- `grbl_reset_error()`
- `grbl_get_all_enabled()`
- `grbl_set_all_enable(...)`

And plugin-specific iocsh configuration helpers:

- `ecmcGrblLoadConfigFile(...)`
- `ecmcGrblAddConfig(...)`
- `ecmcGrblLoadGCodeFile(...)`
- `ecmcGrblAddCommand(...)`

## Current Documentation Scope

The plugin README also documents a few practical constraints:

- limit switches are handled by ecmc, not by the Grbl layer
- homing must be handled in ecmc before G-code execution
- soft limits should be handled in ecmc

This repo currently contains the general load model and role mapping, but no full public Grbl startup example.

So this page documents when to choose the plugin and what the main config surface looks like, while the detailed NC/G-code object model still belongs to the plugin package.

## Related Pages

- [plugins]({{< relref "/manual/plugins/_index.md" >}})
- [Plugin Interface]({{< relref "/manual/plugins/interface.md" >}})
- [motion configuration]({{< relref "/manual/motion_cfg/_index.md" >}})
