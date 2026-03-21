##############################################################################
## Simple example config for a PLC without EtherCAT hardware

require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

# Load one PLC in master-less mode. No EtherCAT master or slaves are configured.
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Master-less PLC', SAMPLE_RATE_MS=100, PLC_MACROS='DBG='"

# Expose one writable static variable, one readback counter, and one global bit.
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd "NAME=Hold,PLC_VAR=hold,ONAM=Hold,ZNAM=Run"
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd "NAME=Counter,PLC_VAR=counter,PREC=0,EGU=counts"
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd "NAME=Mode,PLC_VAR=mode,SCOPE=global,ONAM=One,ZNAM=Zero"
