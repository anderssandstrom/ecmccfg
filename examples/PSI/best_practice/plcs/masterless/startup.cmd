##############################################################################
## Simple example config for a PLC without EtherCAT hardware

require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

# Load one PLC in master-less mode. No EtherCAT master or slaves are configured.
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Master-less PLC', SAMPLE_RATE_MS=100, PLC_MACROS='DBG='"

# Expose one writable static variable, one readback counter, and one global bit.
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.hold,REC_NAME=-Hold")
dbLoadRecords("ecmcPlcAnalog.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.counter,REC_NAME=-Counter")
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.global.mode,REC_NAME=-Mode")
