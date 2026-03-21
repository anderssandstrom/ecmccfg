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
  enable: yes
  externalCommands: yes
  code:
    - ax3.enc.actpos:=(ax1.enc.actpos+ax2.enc.actpos)/2
  filter:
    velocity:
      enable: yes
      size: 100
    trajectory:
      enable: yes
      size: 100
```

### File
```yaml
plc:
  enable: yes
  externalCommands: yes
  file: cfg/heave.plc
  filter:
    velocity:
      enable: yes
      size: 100
    trajectory:
      enable: yes
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
  enable the axis PLC
- `externalCommands`
  allow the PLC to influence axis commands and setpoints
- `code`
  inline PLC lines
- `file`
  external PLC file
- `filter`
  optional filtering of encoder or trajectory velocity values used by the PLC

## When to use inline vs file

- Use `code` for a few short axis-specific lines.
- Use `file` when the logic is more than a handful of lines or should be reused
  across axes.

## Related pages

- [YAML configuration]({{< relref "/manual/motion_cfg/axisYaml.md" >}})
- [legacy motion]({{< relref "/manual/motion_cfg/legacy.md" >}})
- [PLC configuration]({{< relref "/manual/PLC_cfg/_index.md" >}})
