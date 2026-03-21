# Master-less PLC Example

This example shows a self-contained PLC-only setup with `MASTER_ID=-1`.

It demonstrates:

- running ecmc without claiming an EtherCAT master
- loading a classic PLC file with `loadPLCFile.cmd`
- exposing `static` and `global` PLC variables as EPICS PVs through wrapper scripts
- controlling a PLC variable from EPICS in master-less mode

## Files

- `startup.cmd`: loads one PLC in master-less mode and exposes selected PLC variables as PVs
- `cfg/main.plc`: simple PLC code with one counter, one writable hold bit, and one global mode bit

## Startup flow

```cmd
require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Master-less PLC', SAMPLE_RATE_MS=100, PLC_MACROS='DBG='"
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd "NAME=Hold,PLC_VAR=hold,ONAM=Hold,ZNAM=Run"
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd "NAME=Counter,PLC_VAR=counter,PREC=0,EGU=counts"
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd "NAME=Mode,PLC_VAR=mode,SCOPE=global,ONAM=One,ZNAM=Zero"
```

## Important PVs

- `<IOC>:Hold`: writable hold bit for the PLC counter
- `<IOC>:Counter`: current counter value
- `<IOC>:Mode`: global mode bit toggled by the PLC

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
camonitor <IOC>:Counter <IOC>:Mode
caput <IOC>:Hold 1
caput <IOC>:Hold 0
```
