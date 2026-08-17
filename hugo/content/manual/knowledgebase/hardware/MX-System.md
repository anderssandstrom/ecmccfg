+++
title = "Beckhoff MX-System"
weight = 24
chapter = false
+++

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

### Automatic discovery utility

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
