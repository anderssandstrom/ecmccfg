+++
title = "EtherCAT and commissioning"
weight = 20
chapter = false
+++

Configure and verify the EtherCAT system before commissioning motion.

## Commissioning order

1. [Supported slaves]({{< relref "/manual/general_cfg/ethercat/supported_slaves.md" >}}) — select hardware and find its configuration files.
2. [Advanced EtherCAT and commissioning]({{< relref "/manual/general_cfg/ethercat/ethercat_advanced.md" >}}) — configure domains, data items, DC, verification, and topology handling.
3. [EtherCAT endpoint timing]({{< relref "/manual/general_cfg/ethercat/ethercat_timing.md" >}}) — configure delays, phase, timestamps, and diagnostic PVs.
4. [Verify DC timing with position compare]({{< relref "/manual/general_cfg/ethercat/verify_dc_timing_position_compare.md" >}}) — check timed outputs against a touch probe.

## Additional configuration

- [FSoE and TwinSAFE]({{< relref "/manual/general_cfg/ethercat/fsoe.md" >}}) — safety-telegram forwarding and panels.
- [ESI parser]({{< relref "/manual/general_cfg/ethercat/esi_parser.md" >}}) — legacy ESI XML conversion utility.

For communication faults, use the [EtherCAT command line guide]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}}) and [hardware notes]({{< relref "/manual/knowledgebase/hardware/_index.md" >}}).
