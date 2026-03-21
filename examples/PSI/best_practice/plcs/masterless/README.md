# Master-less PLC Example

This example shows a self-contained PLC-only setup with `MASTER_ID=-1`.

It demonstrates:

- running ecmc without claiming an EtherCAT master
- loading a classic PLC file with `loadPLCFile.cmd`
- exposing `static` and `global` PLC variables as EPICS PVs
- controlling a PLC variable from EPICS in master-less mode

## Files

- `startup.cmd`: loads one PLC in master-less mode and exposes selected PLC variables as PVs
- `cfg/main.plc`: simple PLC code with one counter, one writable hold bit, and one global mode bit

## Startup flow

```cmd
require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Master-less PLC', SAMPLE_RATE_MS=100, PLC_MACROS='DBG='"
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.hold,REC_NAME=-Hold")
dbLoadRecords("ecmcPlcAnalog.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.counter,REC_NAME=-Counter")
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.global.mode,REC_NAME=-Mode")
```

## Important PVs

- `<IOC>:Set-Hold-RB`: writable hold bit for the PLC counter
- `<IOC>:Set-Counter-RB`: current counter value
- `<IOC>:Set-Mode-RB`: global mode bit toggled by the PLC

## PLC behavior

- `static.counter` increments every PLC cycle while `static.hold=0`
- when the counter reaches `10`, it is reset to `0`
- each reset toggles `global.mode`

## Running

Run from this directory:

```sh
iocsh.bash startup.cmd
```

Example interaction:

```sh
camonitor <IOC>:Set-Counter-RB <IOC>:Set-Mode-RB
caput <IOC>:Set-Hold-RB 1
caput <IOC>:Set-Hold-RB 0
```
