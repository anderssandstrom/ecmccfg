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
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=9,HW_DESC=MO7221-9016-1124"

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

`finishFSoEMaster.cmd` is required for safety masters whose fixed PDOs follow
the project-dependent FSoE connections. It must run exactly once, after the
last `addFSoEConn.cmd` call. For the MO1918 this produces the process-image
order reported by the slave:

```text
SM2: 0x1600, 0x1601, ..., 0x17f0, 0x17ff
SM3: 0x1a00, 0x1a01, ..., 0x1bfe, 0x1bff
```

The ellipsis represents additional configured FSoE connections. The standard
outputs and the EFUSE/device-status PDOs must remain after them. Adding those
fixed PDOs in `addSlave.cmd`, before the dynamic connections, gives ecmc a
different process-image order and shifts the FSoE data even though
`EcPrintSlaveConfig()` prints the expected PDO indices.

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

The connection ID is mapped directly as the final `U16` entry in each
telegram. An additional `Cfg.EcAddDataDT()` view is not needed when the PDOs
are registered in process-image order. `EcAddDataDT()` is still useful for
named bit views, such as the MO1918 Reset and Run controls inside its packed
standard-output byte.

## MO1918 diagnostics

The MO1918 hardware panel provides controls for the standard outputs and
links to both the FSoE overview and an expert panel.

| PV suffix | Description |
|---|---|
| `-Rst` / `-Rst-RB` | Reset the safety application and its readback |
| `-Run` / `-Run-RB` | Run the safety application and its readback |
| `-FSoE-StateIn01` | Safe Logic state |
| `-FSoE-CycCntIn01` | Safe Logic cycle counter |
| `-EFU-Stat` | Electronic-fuse status bits |
| `-EFU-Curr` | Electronic-fuse current in amperes |

`EFU-Stat` uses the standard Beckhoff MX layout:

| Bit | Meaning |
|---:|---|
| 0 | Warning |
| 1 | Error |
| 2 | Tripped |
| 3 | Enabled |
| 4...15 | Gap/reserved |

The current entry is EtherCAT object `0x6040:18` with datatype `REAL`, mapped
as `F32` and exposed to EPICS through `asynFloat64`.

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

Rapidly changing or implausible connection IDs are another indication of a
process-image offset error. For example, an MO1918 connection ID showing the
EFUSE status value, or the Safe Logic state/cycle counter, means the trailing
PDOs were registered before the FSoE connections. Verify that
`finishFSoEMaster.cmd` ran after every `addFSoEConn.cmd` and before
`Cfg.SetAppMode(1)`.

Useful runtime checks are:

```text
ethercat pdos -m <master> -p <slave> -v
ecmcConfig "EcPrintSlaveConfig(<slave>)"
```

The EtherCAT output establishes the physical PDO layout. The ecmc output
confirms which entries and sizes were registered; live EPICS monitoring can
then reveal an offset mismatch.

If an MO7221 reaches `Ready to switch on` (`0x0021`) but does not advance when
the controlword changes to `7` or `15`, verify its stored operating mode:

```text
ethercat upload -m <master> -p <slave> -t int8 0x7010 3
```

The standard ecmccfg MO7221 mapping uses cyclic synchronous velocity mode
(CSV), so the value must be `9`. A device previously configured by TwinCAT may
retain CSP mode (`8`). The MO7221 hardware configuration explicitly writes
CSV during PREOP and registers the setting for reapplication after reconnect.

MO7221 is also available with cyclic synchronous position mode descriptors:

```text
MO7221-9016-1114_CSP  # 24 V
MO7221-9016-1124_CSP  # 48 V
```

These select mode `8` and map target position through PDO `0x1611`, object
`0x7010:05`, as `positionSetpoint01`. The CSP RxPDO assignment contains
`0x1610` and `0x1611`; it does not include the CSV torque-offset PDO. The
descriptors without `_CSP` select mode `9` and map target velocity through
`0x1612`, object `0x7010:06`.

The CSP descriptors set `PnlTyp` to `MO7221-9016_CSP`. Its hardware panel
retains the normal MO7221 status and FSoE navigation, while its Expert button
opens the CSP drive panel with position-command PVs instead of CSV velocity
commands.

## Related pages

- [Advanced EtherCAT and Commissioning]({{< relref "/manual/general_cfg/ethercat_advanced.md" >}})
- [Beckhoff MX-System]({{< relref "/manual/knowledgebase/hardware/MX-System.md" >}})
- [Panels]({{< relref "/manual/knowledgebase/panel.md" >}})
