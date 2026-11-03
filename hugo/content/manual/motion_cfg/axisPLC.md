+++
title = "Axis PLC"
weight = 22
chapter = false
+++

## Scope

Each motion axis can have a local axis PLC. This is configured as part of the
[YAML axis configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}}).

Use the axis PLC for logic that belongs directly to one axis, for example:

- interlocking
- derived setpoints
- local synchronization logic
- local signal filtering or overrides

For larger machine logic or coordination between many objects, use a normal PLC
instead of putting everything in the axis PLC.

## Two ways to provide the code

The code can be provided either inline in the YAML or in a separate file.

### Inline
```yaml
plc:
  enable: true
  externalCommands: true
  code:
    - ax3.enc.actpos:=(ax1.enc.actpos+ax2.enc.actpos)/2
  velocity_filter:
    encoder:
      enable: true
      size: 100
    trajectory:
      enable: true
      size: 100
```

### File
```yaml
plc:
  enable: true
  externalCommands: true
  file: cfg/heave.plc
  velocity_filter:
    encoder:
      enable: true
      size: 100
    trajectory:
      enable: true
      size: 100
```

The corresponding PLC file:

```text
ax${AXIS_NO}.enc.actpos:=(ax{{ var.ty1 }}.enc.actpos+ax{{ var.ty2 }}.enc.actpos)/2;
```

Note the mixed use of startup macros like `${AXIS_NO}` and local template
variables like `{{ var.ty1 }}`.

## Main keys

- `enable`
  enable the axis PLC; required when the axis `plc` block is present
- `externalCommands`
  allow the PLC to influence axis commands and setpoints; default false
- `code`
  inline PLC lines
- `file`
  external PLC file
- `velocity_filter`
  optional `encoder` and `trajectory` velocity filtering. Each block defaults
  to `enable: false`, `size: 1` (cycles). Set `enable: true` to use it.

The older `filter.velocity` and `filter.trajectory` syntax remains supported
but is deprecated. `file` and `code` are optional; when both are supplied,
inline lines are appended after the file content.

## When to use inline vs file

- Use `code` for a few short axis-specific lines.
- Use `file` when the logic is more than a handful of lines or should be reused
  across axes.

## Related pages

- [YAML configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}})
- [PLC configuration]({{< relref "/manual/plc_cfg/_index.md" >}})
