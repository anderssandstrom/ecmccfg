+++
title = "Terminology"
weight = 6
chapter = false
+++

This page defines the main terms used across the manual.

## Preferred terms

### axis PLC
An axis PLC is PLC logic attached directly to one axis as part of the motion
configuration. Use it for axis-local logic such as local interlocks, setpoint
conditioning, or small axis-specific sequences.

### best-practice example
A best-practice example is a public, reusable example under
`examples/PSI/best_practice/`. These examples should be self-contained and are
the preferred examples to reference from the manual.

### component
A component is a reusable hardware or function configuration block, typically
applied with `applyComponent.cmd`. Components are commonly used to configure
motors, encoders, and related EtherCAT-side settings.

### data storage
Data storage is the buffered sample storage facility used for collecting values
over time and optionally pushing them to EPICS/asyn.

### global PLC variable
A `global` PLC variable is shared across PLCs. Use it when several PLCs or EPICS
records need to access the same value.

### legacy motion
Legacy motion refers to the older classic motion configuration flow based on
`.ax`, `.vax`, and `.sax` files and the related classic startup commands.

### master-less mode
Master-less mode means running with `MASTER_ID=-1`, without an EtherCAT master.
This is also called non-EtherCAT mode in some pages.

Note:
The directory name `masterless` may still appear in example paths. In prose, the
preferred term is `master-less`.

### PLC
A PLC in `ecmccfg` is deterministic logic executed in the ecmc cycle. Use a
normal PLC for shared logic, coordination across multiple axes, state handling,
I/O logic, and reusable control sequences.

### plugin
A plugin is an optional runtime extension loaded into ecmc for functionality
that is not part of the core axis/PLC setup.

### static PLC variable
A `static` PLC variable belongs to one PLC instance. It keeps its value between
PLC scans and is the normal choice for PLC-local state.

### virtual axis
A virtual axis is an axis without a physical drive or encoder interface. It is
typically used for coordination, synchronization, or higher-level motion logic.
