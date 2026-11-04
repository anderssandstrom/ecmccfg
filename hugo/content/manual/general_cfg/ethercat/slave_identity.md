+++
title = "Slave firmware and identity"
weight = 18
chapter = false
+++

`addSlave.cmd` loads static identity records next to the existing `HWType` PV.
With a matching ECMC build, it reads them once during configuration, after the
hardware script and record loading, before runtime and `iocInit`.

| Slave PV suffix | Value |
| --- | --- |
| `HWType` | Configured hardware description, such as `EL2794` |
| `HWFw` | Firmware string read from CoE SDO `0x100A:00` |
| `HWRev` | Discovered SII revision, formatted as eight hexadecimal digits |
| `HWSer` | Discovered SII serial number, formatted as an unsigned decimal string |
| `HWFwStat` | Result of the optional firmware read |
| `HWIdStat` | Result of the revision/serial read |

Use the same slave prefix as `HWType`. These are soft `stringin` records with
no cyclic read. The values describe the startup snapshot; restart the IOC to
refresh them after replacing a terminal or updating firmware. String storage
preserves the entire unsigned 32-bit serial number without signed conversion.

## Availability and status

Not every EtherCAT slave supports CoE or implements `0x100A`. For example,
[EL27xx terminals have no CoE interface](https://infosys.beckhoff.com/content/1033/el27xx/index.html).
Where implemented, [0x100A is a firmware string](https://infosys.beckhoff.com/content/1033/ej2502/2448711307.html),
not a fixed two-byte number. Revision and serial are read from the master's
discovered identity, so their read does not depend on that firmware object.

`Available` means the corresponding read succeeded. Firmware that is absent,
unsupported or could not be read remains `Unknown` with status
`Unavailable/read failed`. Empty and non-text values have explicit statuses.
The EPICS string field holds 39 characters; a longer firmware string is shortened
and marked `Truncated`. Identity read failures leave revision and serial
`Unknown`. These optional reads do not abort startup.

A successful serial read can return `0`. This is the device's reported value,
not a guarantee of a unique manufacturing serial. Some Beckhoff devices encode
production information in this field; see the
[identity-object description](https://infosys.beckhoff.com/content/1033/ej2502/2448711307.html).
`HWRev` is the SII device revision and is kept separate from firmware.

## Enable or disable reads

Reads are enabled by default for real hardware when the native helper is
available. Disable them for one slave with:

```bash
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL2794,READ_IDENTITY=0"
```

Or set the global default before adding slaves:

```bash
epicsEnvSet("ECMC_READ_SLAVE_IDENTITY", "0")
```

An explicit `READ_IDENTITY` overrides the global default. The records report
`Disabled` when reads are disabled, `Simulation` for `SIM=1`, and
`Development mode` when slave verification is disabled through `ECMC_DEV_MODE`.
No hardware reads are issued in those modes. `DEFAULT_SLAVE_PVS=false`
suppresses these records and their reads along with the other standard slave PVs.

## ECMC support

Firmware string capture requires an ECMC build registering
`ecmcReadEcSlaveIdentity(slavePosition, pvPrefix)`. Such builds export
`ECMC_EC_SLAVE_IDENTITY_SUPPORTED=1`; rebuild and install ECMC as well as
ecmccfg to enable capture. The helper uses EPICS's static database API before
`iocInit` and refuses calls after database initialization or outside ECMC
configuration mode.

On older ECMC builds, the new PVs still exist with `Unknown` values and
`Not supported` statuses. The startup script does not attempt the missing helper.
Do not set the capability environment variable manually.

The legacy `slaveVerify.cmd` option `READ_FW=1` remains a two-byte numeric read
into `ECMC_EC_SLAVE_FW`; it does not populate these PVs and is not the generic
firmware-string reader.
