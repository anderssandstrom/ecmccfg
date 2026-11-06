# Queued SDO autosave / restore

IOC-local example for an EK1100 at slave 0 and an EL7041 at slave 1, master 0.
It requires the queued-SDO changes in both ECMC and ecmccfg, plus `autoSRarray`.
It uses real EtherCAT mailbox transfers; the simulation backend cannot run it.
No axis or motor component is loaded. Adjust the hardware layout before use.

`startup.cmd` demonstrates two interfaces to EL7041 current settings:

| Name | Address | Interface |
| --- | --- | --- |
| MaxCurrent | `0x8010:01`, U16, mA | Writing `Val` queues a write |
| StandbyCurrent | `0x8010:02`, U16, mA | Writing `Val` stages; `WrtCmd=1` queues a write |

Both use `QUEUE=1,RESTORE=1`, which also selects `PREOP_ONLY=1`. Omitting these
options keeps the legacy interface. `RdCmd=1` still requests an upload in either
interface, including after startup. PREOP-only writes are rejected after master
activation.

## First commissioning

Run the PSI IOC launcher from this directory, with your usual IOC name. First
create a writable save directory:

```sh
mkdir -p save
```

The default `SDO_AUTO_START=0` lets EPICS finish starting while holding master
activation. A missing save file on the first run is expected. Use values suitable
for your motor; these commands illustrate 400 mA maximum and 100 mA standby.
Replace `MYIOC` with the IOC name:

```sh
caput MYIOC:m0s001-SDO-MaxCurrent-Val 400
caput MYIOC:m0s001-SDO-StandbyCurrent-Val 100
caput MYIOC:m0s001-SDO-StandbyCurrent-WrtCmd 1
```

At this point the requests are pending; the value write itself does not confirm a
hardware transfer. In the IOC shell, start the queue worker:

```iocsh
ecmcStartAppModeAsync(0)
```

It downloads each request in PREOP, uploads and compares the actual value, then
permits master activation. Wait for both `Bsy` PVs to become zero, check that both
`ErrId` PVs are zero, and check `Val-RB` against the requested values. The worker
also reports activation failures in the IOC log. A failed startup write keeps
activation held; fix the cause before submitting another request and retrying.

The monitored autosave set writes `save/sdo_settings.sav` after changes (five
second period). Check that the file contains both request waveforms before
stopping the IOC. Save files are local runtime data and are ignored by Git.
Give each IOC its own save directory; `ASR_SAVE_DIR` overrides `./save`.

## Automatic restart

Set the startup macro `SDO_AUTO_START=1` for subsequent runs. Autosave restores
`sdo_settings.sav` in pass 1, before ECMC collects the saved requests. The worker
then writes and verifies them before allowing cyclic operation / OP. Queued SDOs
defer activation even when the normal configuration would start ECMC first.
`STARTUP_GATE` separately holds motion/PLCs until startup readiness.

An untouched SDO has no valid request and causes no restore write. For the manual
interface, staging `Val` without `WrtCmd` does not create a saved request. An
explicit write of zero is a valid request and is restored as zero.

The local request file is `db/sdo_settings.req`. It saves the internal
`StartupData_` waveform, which contains the accepted request and its identity;
leave this data to the driver. Do not autosave `WrtCmd`, `RdCmd`, `Val`, or
`Val-RB`. Restore these waveforms in pass 1 only. This example registers its
request/save set explicitly; avoid also registering it through generated PSI
save/restore scripts.

Do not configure the same SDO addresses through static startup downloads, such
as a motor component's `Cfg.EcAddSdo` calls. A conflicting static download could
overwrite the restored value during activation; the queued startup path rejects
that conflict.

This example has not been exercised against a live IOC or EL7041.
