+++
title = "Advanced EtherCAT and Commissioning"
weight = 17
chapter = false
+++

## Scope
This page covers the lower-level EtherCAT and commissioning helpers that are available when the normal `addSlave.cmd` and `applyComponent.cmd` path is not enough.

Use it when you need:

- additional EtherCAT domains
- custom process-image pointers/data items
- explicit distributed-clock setup
- slave identity verification
- topology gaps where one or more slave positions should be skipped

## Additional Domains

The normal setup uses one EtherCAT domain.

If you need a separate execution rate or execution offset for a set of entries, create another domain:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addDomain.cmd "EXE_RATE=2,EXE_OFFSET=0,ALLOW_OFFLINE=0"
```

Important behavior:

- all EtherCAT entries created after `addDomain.cmd` belong to the new domain
- `EXE_RATE` is in realtime cycles
- `EXE_OFFSET` is also in realtime cycles
- `ALLOW_OFFLINE=1` relaxes the domain state requirement, but can affect the rest of the bus and the DC behavior

Use extra domains only when you have a clear reason. For most systems, the default single-domain setup is simpler and safer.

## Custom EtherCAT Data Items

`addEcDataItem.cmd` exposes a value directly from already configured process-image data.

Think of it as a typed pointer into the process image.

Example:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addEcDataItem.cmd \
  "STRT_ENTRY_S_ID=5,STRT_ENTRY_NAME=statusWord01,OFFSET_BYTE=0,OFFSET_BITS=0,RW=2,DT=U16,NAME=rawStatus"
```

Use this when:

- you need direct access to a value that is already in the process image
- you need a custom EPICS-facing record for a piece of EtherCAT data
- a plugin or PLC should consume a small custom process-image item without defining a full axis or component object

Key parameters:

- `STRT_ENTRY_S_ID`: slave position
- `STRT_ENTRY_NAME`: start entry name
- `OFFSET_BYTE`, `OFFSET_BITS`: offset from that start entry
- `RW`: `1` write, `2` read
- `DT`: data type such as `B1`, `U16`, `S32`, `F32`, `F64`
- `NAME`: runtime name of the created item

By default, the wrapper also loads a matching EPICS record for the item.

## Distributed Clocks

Use `applySlaveDCconfig.cmd` when a slave needs explicit distributed-clock configuration:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd \
  "ASSIGN_ACTIVATE=0x0300,SYNC_0_CYCLE=1000000,SYNC_0_SHIFT=0"
```

Typical inputs:

- `ASSIGN_ACTIVATE`: DC assign/activate word from the terminal XML
- `SYNC_0_CYCLE`: sync period in ns
- `SYNC_0_SHIFT`: sync shift in ns
- `SYNC_1_CYCLE`: optional second sync period in ns

Use this only when the slave actually needs explicit DC setup. Unnecessary DC customization can make commissioning harder.

## Slave Identity Verification

Use `slaveVerify.cmd` during commissioning or in strict production setups to verify that the expected slave is actually present:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0,READ_FW=1"
```

The script can:

- verify vendor/product identity
- optionally reset the terminal through `0x1011`
- optionally read the firmware version from `0x100a`

This is useful when:

- identical stations may have different hardware revisions
- you want startup to fail early on the wrong terminal
- you are commissioning replacement hardware

## Skipping Slave Positions

Use `ignoreSlaves.cmd` when the logical topology in the startup file must skip one or more bus positions:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}ignoreSlaves.cmd "COUNT=2"
```

This does not configure anything by itself. It only advances the slave-position counter used by later slave-related scripts.

Typical use:

- a coupler branch or optional hardware is not part of the active configuration
- one startup file is shared across similar but not identical topologies

## Recommended Usage

For normal systems:

1. start with `addSlave.cmd`
2. use `applyComponent.cmd` where possible
3. use the helpers on this page only when there is a concrete commissioning or process-image need

For advanced systems:

1. define the topology
2. add extra domains only if the timing model requires them
3. expose extra process-image data with `addEcDataItem.cmd`
4. apply explicit DC settings only where required
5. verify critical slaves during commissioning

## Related Pages

- [startup.cmd]({{< relref "/manual/general_cfg/startup/_index.md" >}})
- [Script Reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [RT SDO Objects]({{< relref "/manual/general_cfg/rt_sdo.md" >}})
- [ecmc command reference]({{< relref "/manual/general_cfg/ecmc_command_ref.md" >}})
- [knowledgebase: EtherCAT CLI]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
