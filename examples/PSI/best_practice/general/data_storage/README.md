# Data Storage Buffer

This example shows a minimal self-contained data-storage setup without
EtherCAT hardware.

It demonstrates:

- creating a data-storage buffer with `addDataStorage.cmd`
- continuously appending data from a PLC
- exposing a PLC trigger variable as an EPICS PV
- pushing the buffered waveform to EPICS on demand with `ds_push_asyn()`

## Files

- `startup.cmd`: creates the data storage and loads the PLC
- `plc/data_storage_trigger.plc`: generates a simple signal and pushes data on
  a rising edge of `static.trigg`

## Startup flow

```cmd
require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=0, DS_SIZE=1000, SAMPLE_RATE_MS=-1, DS_TYPE=2, DESC='BufferedSignal'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "PLC_ID=0, SAMPLE_RATE_MS=10, FILE=./plc/data_storage_trigger.plc, PLC_MACROS='DS_ID=0, DBG='"
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.trigg,REC_NAME=-PushDataTrigger")
dbLoadRecords("ecmcPlcAnalog.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.signal,REC_NAME=-Signal")
```

## Important PVs

- `<IOC>:ds0-Data-Act`: waveform with the buffered data
- `<IOC>:Set-PushDataTrigger-RB`: push trigger for the waveform
- `<IOC>:Set-Signal-RB`: current generated signal value

## Running

Run from this directory:

```sh
iocsh.bash startup.cmd
```

Trigger a push to EPICS:

```sh
caput <IOC>:Set-PushDataTrigger-RB 1
caput <IOC>:Set-PushDataTrigger-RB 0
caput <IOC>:Set-PushDataTrigger-RB 1
```

Watch the signal and the pushed waveform:

```sh
camonitor <IOC>:Set-Signal-RB <IOC>:ds0-Data-Act
```
