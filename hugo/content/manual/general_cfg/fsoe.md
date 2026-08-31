+++
title = "FSoE and TwinSAFE"
weight = 18
chapter = false
+++

## Scope

ecmccfg can map and cyclically forward Fail Safe over EtherCAT (FSoE)
telegrams between TwinSAFE devices. The safety application itself must be
configured and downloaded with TwinCAT or TwinSAFE Loader.

{{% notice warning %}}
ecmc and its operator panels are not safety-rated. They only transport and
display process data. CRC, watchdog, connection validation, and the safety
function remain in the certified FSoE/TwinSAFE devices.
{{% /notice %}}

## Direct cyclic forwarding

The generic configuration uses `Cfg.EcAddEntryCyclicWrite(<to>,<from>)`
instead of an ecmc PLC expression. Both EtherCAT entries must exist before the
link command runs, and all connections must be configured before
`Cfg.SetAppMode(1)`.

For a MO1918 safety master with two MO7221 safety slaves, first add the master
and its two directly mapped connections:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=4,HW_DESC=MO1918-0000"
${SCRIPTEXEC} ${ecmccfg_DIR}addFSoEConn.cmd, "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=01"
${SCRIPTEXEC} ${ecmccfg_DIR}addFSoEConn.cmd, "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=02"
${SCRIPTEXEC} ${ecmccfg_DIR}finishFSoEMaster.cmd, "SFTY_MASTER_SID=4"
```

Add the safety slaves and their normal hardware configurations, then link the
endpoints:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=8,HW_DESC=MO7221-9016-1114"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=9,HW_DESC=MO7221-9016-1114"

${SCRIPTEXEC} ${ecmccfg_DIR}linkFSoEConn.cmd, "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=01,SFTY_SLAVE_SID=8,SFTY_SLAVE_CONN=01"
${SCRIPTEXEC} ${ecmccfg_DIR}linkFSoEConn.cmd, "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=02,SFTY_SLAVE_SID=9,SFTY_SLAVE_CONN=01"
```

`ECMC_EC_MASTER_ID` selects the EtherCAT master automatically. The connection
numbers are written as two hexadecimal digits because they are also used in
the EtherCAT entry names.

The required call order is:

1. Add the safety master.
2. Add every master-side FSoE connection.
3. Finish the safety-master mapping with `finishFSoEMaster.cmd`. This appends its
   standard-output, EFUSE, and device-status PDOs after the FSoE telegrams.
4. Add the safety slaves, including their FSoE PDO mappings.
5. Link each master connection to its slave connection.
6. Activate application mode.

## Telegram mapping

The six-byte telegram is registered directly as four packed entries rather
than as one unsupported 48-bit datatype:

| Field | Datatype | Size |
|---|---:|---:|
| Command | `U8` | 1 byte |
| Safe data | `U8` | 1 byte |
| CRC | `U16` | 2 bytes |
| Connection ID | `U16` | 2 bytes |

Mandatory bit groups and gaps that occupy a complete byte are registered as
packed `U8` entries. This avoids invalid `B1`/gap combinations while
preserving the exact PDO length expected by the slave.

## Hardware-panel navigation

The normal hardware-panel path is used:

```text
ecmcMain.ui
  -> generic EtherCAT slave overview
  -> ecmcMO1918-0000.ui
  -> FSoE connections
  -> generated FSoE connection overview
```

The MO1918 hardware definition sets `PnlTyp` to `MO1918-0000`. Its FSoE
button opens `ecmcFSoEMaster.ui`, which contains reusable
`ecmcFSoEConnRow.ui` rows for connections `01` through `08`. Each
row is visible only when its `RmtSID` metadata PV exists and contains a
positive slave ID. This supports up to eight configured connections without
a launcher script or generated UI. Each visible row can open the connection
details or the connected safety-slave hardware panel.

`linkFSoEConn.cmd` loads navigation metadata such as:

```text
$(IOC):FSoE-M1-CH01-RmtSID
$(IOC):FSoE-M1-CH01-RmtConn
$(IOC):FSoE-M1-CH02-RmtSID
$(IOC):FSoE-M1-CH02-RmtConn
```

The **Open slave** buttons call `ecmcOpenObject.sh EC_SLAVE_GENERIC`. That
helper reads the remote SID PV, resolves the remote device's `PnlTyp`, and
opens its standard hardware panel. The MO7221 hardware panel also provides a
direct FSoE details button for its connection `01`.

The compact navigation metadata currently assumes one safety master per
EtherCAT master. This does not affect telegram forwarding; it only affects the
names used for panel navigation.

## Diagnostics

If `Cfg.EcAddEntryCyclicWrite(...)` returns
`ERROR_MAIN_EC_ENTRY_NULL (0x20014)`, at least one named endpoint was not
created. Check that `addFSoEConn.cmd` ran for the master connection and that
the safety-slave FSoE mapping was loaded before `linkFSoEConn.cmd`.

An EtherCAT AL status of `0x0025` (`Invalid Output Mapping`) normally means
the configured PDO order, entry sizes, or total SyncManager length differs
from the mapping expected by the device. Compare the configuration with an
export for the exact product code and revision.

## Related pages

- [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}})
- [Beckhoff MX-System]({{< relref "/manual/knowledgebase/hardware/MX-System.md" >}})
- [Panels]({{< relref "/manual/knowledgebase/panel.md" >}})
