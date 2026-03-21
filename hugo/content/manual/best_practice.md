+++
title = "best practice"
weight = 6
chapter = false
+++

## Scope

This page is the entry point for the public best-practice material in the
manual.

Use best-practice pages when you want:

- a recommended starting point for a new configuration
- example-driven guidance rather than full reference material
- public examples that correspond to the manual text

## By area

- [General]({{< relref "/manual/general_cfg/best_practice.md" >}})
  host setup, EtherCAT rate, and controller-side recommendations
- [Motion]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
  axis, encoder, homing, motor-record, and motion example patterns
- [PLC]({{< relref "/manual/PLC_cfg/best_practice.md" >}})
  PLC structure, macros, debug handling, and EPICS variable exposure

## Core recommendations

Some recurring recommendations apply across several sections:

- prefer the YAML-based motion workflow for new configurations
- keep SDO verification enabled so slave mismatches are caught at startup
- prefer native axis auto-enable and disable via `axis.autoEnable`
- use `VAR ... END_VAR` in PLC code for clearer structure
- use public best-practice examples as the reusable starting point, not
  `examples/test` or `lab_setup`
