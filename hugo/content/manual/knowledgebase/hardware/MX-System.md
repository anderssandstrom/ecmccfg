+++
title = "Beckhoff MX-System"
weight = 24
chapter = false
+++

## MO1008, MO2008 and MO2338 connector variants

For MO1008, MO2008 and MO2338, the `-1111` and `-1112` suffixes select the connector
type. Both variants use the same PDO configuration, database records and panel.
The suffix is optional when selecting the hardware configuration:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=MO1008-0000,SLAVE_ID=7"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=MO2008-0000,SLAVE_ID=8"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=MO2338-0000,SLAVE_ID=9"
```

Each descriptor also accepts either suffix, for example
`HW_DESC=MO2008-0000-1112`. These explicit variants reuse the generic
`ecmcMO1008-0000.substitutions`, `ecmcMO2008-0000.substitutions` or
`ecmcMO2338-0000-common.substitutions` database, respectively.

## Enable a second baseplate with EtherLab

### Issue

EtherLab discovers only the first MX baseplate, while TwinCAT can activate the
downstream baseplate. The downstream `MS4210` is not visible in EtherLab at
all, so neither it nor the EtherCAT modules connected through it appear in the
slave list. The `MS4210` is normally installed in the last slot of the
upstream baseplate.

### Root cause

The internal `MB1120 backplane junction`, for this baseplate at slave position 10, starts with EtherCAT port 3 forced
**Closed**.

The relevant EtherCAT Slave Controller (ESC) register is:

- `0x0100`: DL Control
- MB1120 default: `0x0007c001`
- Port 3 set to `Auto`: `0x00070001`

### Observed topology and slave positions

- The `MB1120` is the backplane-junction EtherCAT slave that controls access
  to the next downstream baseplate. Its slave position is the value passed as
  `MB1120_SID`, or as `MX_1` through `MX_5` during startup. For multiple
  baseplates, specify the MB1120 positions in upstream-to-downstream discovery
  order.
- The `MB1100-002` Bluetooth gateway seems to offset subsequent EtherCAT
  slave positions by one. Account for this when determining the MB1120 slave
  position used by the workaround.
- The `MS1110-0000` always seems to appear as the last slave. With one
  baseplate it is last in that topology; when a second baseplate is enabled,
  it moves to the end of the expanded topology.

### Workaround

Set port 3 to `Auto`, wait for the downstream baseplate to become available,
and list the slaves again:

```bash
ethercat reg_write -m1 -p10 -e -t uint32 0x0100 0x00070001
sleep 1
ethercat slaves -m1
```

Adjust the master (`-m1`) and slave position (`-p10`) to match the system.

The same operation is available as an ecmccfg script. The MB1120 slave
position defaults to `10`, and the master defaults to `ECMC_EC_MASTER_ID` (or
`0` if it is not set). The script uses the `ECMC_EC_TOOL_PATH` configured by
`startup.cmd`:

{{% notice warning %}}
`mxEnableDownStreamBaseplate.cmd` can only be used before `addMaster.cmd`
claims the EtherCAT master. For normal IOC startup, use the `MX_1` through
`MX_5` startup macros described below.
{{% /notice %}}

```text
${SCRIPTEXEC} ${ecmccfg_DIR}mxEnableDownStreamBaseplate.cmd
```

Override the defaults with script macros when required:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}mxEnableDownStreamBaseplate.cmd, "MASTER_ID=1,MB1120_SID=10"
```

Set `REPORT=1` to list the EtherCAT slaves before and after enabling the
downstream baseplate. Reporting is disabled by default. Before rescanning, the
script waits three seconds by default; override this with `RESCAN_DELAY`:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}mxEnableDownStreamBaseplate.cmd, "REPORT=1,RESCAN_DELAY=3"
```

The junctions must be opened before ecmc claims the EtherCAT master. For IOC
startup, set `MX_1` through `MX_5` to the MB1120 slave positions. The populated
macros are processed in order, with a rescan after each junction so the next
downstream MB1120 becomes visible:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}startup.cmd, "SYS=...,MX_1=10,MX_2=21,MX_REPORT=1"
```

Omit unused `MX_n` macros. `MX_REPORT` defaults to `0`, and
`MX_RESCAN_DELAY` defaults to `3` seconds.

## MO2338-0000-1112 M12 pinout and BO02 LED indication

Each M12 A-coded connector carries two digital input/output channels:

| Pin | Signal |
|-----|--------|
| 1 | +24 V (`UB`) |
| 2 | DIO B |
| 3 | GND |
| 4 | DIO A |
| 5 | Not connected |

The channels are assigned in A/B pairs. On the first connector, BO01 is DIO A
on pin 4 and BO02 is DIO B on pin 2. The following connectors carry BO03/BO04,
BO05/BO06, and BO07/BO08 in the same pattern.

On one MO2338-0000-1112, the BO02 LED was observed to remain off while all of
the following showed that the output was operating correctly:

- `BO-Arr-RB` returned `0xff` after writing `0xff` to `BO-Arr`.
- Pin 2 of the first M12 connector measured 24 V.
- `BO-Stat01`, `BO-Stat02`, and `BO-Stat03` were all zero.
- `EFU-Stat` was `0x4008`, indicating that the electronic fuse was enabled
  without a warning, error, or trip.

Do not use the BO02 LED alone to determine the electrical output state. Verify
`BO-Arr-RB`, the BO diagnostics, and the voltage between pin 2 and pin 3.

## Restoring missing SII data: MO1008 example

One MO1008-0000-1112 was found with an incomplete or corrupt SII EEPROM. The
terminal identity could still be read, but its descriptive and process-data
information was absent. In this condition, `ethercat slaves` showed only the
numeric vendor ID and product code instead of the terminal name:

```text
8  0:8  PREOP  +  0x00000002:0x811fbc0b
```

`ethercat pdos` returned no PDOs. Likewise, `ethercat xml` contained only the
numeric identity and no SyncManager or PDO definitions. An
`ethercat sii_read -v` returned only a minimal 128-byte SII area.

When ecmc configured an input PDO on SM3, EtherLab consequently reported:

```text
EtherCAT ERROR 1-8: Failed to determine PDO sync manager for FMMU!
```

This error occurs before, and independently of, packing the `0x1a00` input PDO
as `U8` or the `0x1a01` diagnosis PDO as `U16`. EtherLab creates the FMMU from
the application configuration, but cannot resolve SM3 because the physical
SyncManager descriptions are missing from the slave's SII. Adding an ecmc
`Cfg.EcAddSyncManager()` call does not restore those SII descriptions.

The matching ESI specifies the relevant process-data SyncManagers as:

| SyncManager | Start address | Size | Control byte | Direction |
|-------------|---------------|------|--------------|-----------|
| SM2 | `0x1200` | 2 bytes | `0x24` | Outputs |
| SM3 | `0x1900` | 11 bytes | `0x20` | Inputs |

The terminal needs a valid binary SII EEPROM image generated from the matching
ESI or read from an identical working MO1008-0000-1112. Back up the existing
EEPROM before writing anything. The XML ESI file cannot be passed directly to
`ethercat sii_write`; that command expects a compiled binary SII image.

### Write the matching binary SII image

SII means **Slave Information Interface** (not SSI). The following field example
restored the device name of an MO1008-0000-1112 on **master 1, slave position 7**.
The earlier diagnostic example used position 8; always select the position from
the current bus listing.

{{% notice warning %}}
Carry out EEPROM maintenance with the machine stopped and motion disabled.
Confirm the physical module, variant, revision, master ID and slave position
before writing. Use a binary SII image matching that hardware; do not copy an
image from a different module or bypass image checks with `--force`.
{{% /notice %}}

1. Inspect the target and save its existing SII contents, even if incomplete:

   ```bash
   ethercat -m1 slaves
   ethercat -m1 -p7 slaves -v
   ethercat -m1 -p7 sii_read > MO1008-0000-1112-m1-p7-before.bin
   ```

   Check that the read succeeded before proceeding. Omit `-v` from `sii_read`
   when saving a binary backup; verbose output is text.

   Before the repair, the relevant line was:

   ```text
   7  0:7   PREOP  +  0x00000002:0x811fbc0b
   ```

2. Write the matching binary image. In this installation it was stored at:

   ```bash
   ethercat -m1 -p7 sii_write /ioc/NeedfulThings/beckhoff_firmwares/p05_sii_MO1008-0000-1112.bin
   ```

   Replace the path with the location of your verified image. The `p05` in this
   filename does not select the destination: `-m1 -p7` selects master 1,
   slave position 7. Use the permissions required by the local EtherCAT setup.

3. Rescan the selected master to refresh its cached slave information:

   ```bash
   ethercat -m1 rescan
   ethercat -m1 slaves
   ```

   In the reported sequence, `ethercat slaves` immediately after `sii_write`
   still showed the numeric identity. After the rescan it showed:

   ```text
   7  0:7   PREOP  +  MO1008-0000-1112 8-channel digital input, 24 V DC, M12
   ```

   The rescan rereads slave information; an unchanged name before rescan does
   not by itself mean the write failed. Do not repeat the write just to refresh
   the displayed name.

4. Check the restored PDO and SyncManager descriptions:

   ```bash
   ethercat -m1 -p7 sii_read -v
   ethercat -m1 -p7 pdos
   ethercat -m1 -p7 xml
   ```

   Confirm that the expected descriptions are present, then validate the ecmc
   configuration, slave state and input data on the hardware.

The observed rescan restored the MO1008 name, but did not establish that the
whole bus was healthy. Other positions still showed `INIT E`, and positions 10
and 11 showed zero identities or an unknown state in the subsequent listing.
Check every expected slave after rescanning and resolve those issues before
returning the machine to operation. Restoring the name alone does not validate
PDO operation or prove that all SII data are correct.

The generic MO1008-0000 and MO1008-0000-1112 ecmccfg mappings use the matching
Beckhoff ESI's default Synchron mode (`AssignActivate=0x100`): RX `0x1680`
(EFU control) on SM2, and TX `0x1a00` (inputs), `0x1a01` (input diagnosis), and
`0x1a80` (EFU status/current) on SM3. Earlier configurations omitted the required
RX PDO and incorrectly assigned EFU inputs to `0x1a10`. Use the corrected
configuration after restoring SII. The reported SII write and rescan confirm device-name
recovery; process-data validation remains a separate commissioning step.

## MS1010-1002-1334 rail shutdown and recovery

{{% notice warning %}}
Setting bit 0 (`Disable Output`) in `PSU-Ctrl` removes power from the complete
24 V rail. Despite sometimes being described operationally as an enable
control, this bit is active-high disable and must not be toggled casually.

On the tested MS1010-1002-1334, clearing the bit did not immediately restore
the rail. The slave had to be power-cycled and remain fully unpowered for at
least 30 seconds before it would feed power again. Account for the loss of all
devices supplied by that rail before operating this control.
{{% /notice %}}

## Automatic downstream-baseplate discovery utility

The `utils/mxEnableDownstreamBaseplates.sh` utility can discover and open a
chain without specifying the MB1120 positions in advance. It repeatedly finds
the last newly visible MB1120, opens port 3, waits, and rescans until no new
MB1120 is found:

```bash
utils/mxEnableDownstreamBaseplates.sh 1 3 /opt/etherlab/bin/ethercat 3
```

The positional arguments are the master ID (default `0`) and rescan delay in
seconds (default `3`), followed by the optional EtherCAT executable (default
`/opt/etherlab/bin/ethercat`) and EtherCAT port (default `3`). Ports `0`
through `3` are accepted. `MX_MAX_BASEPLATES` sets the safety limit and defaults
to `32`.

{{% notice warning %}}
Run this utility before `addMaster.cmd` claims the EtherCAT master.
{{% /notice %}}

## Related Pages

- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
- [FSoE and TwinSAFE]({{< relref "/manual/general_cfg/ethercat/fsoe.md" >}})
