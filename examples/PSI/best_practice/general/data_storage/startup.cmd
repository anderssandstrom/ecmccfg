require ecmccfg "MASTER_ID=-1,ENG_MODE=1"

# Data storage buffer. SAMPLE_RATE_MS=-1 means the waveform is pushed on demand
# from PLC code via ds_push_asyn().
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=0, DS_SIZE=1000, SAMPLE_RATE_MS=-1, DS_TYPE=2, DESC='BufferedSignal'"

# PLC generates a simple signal, appends it continuously to the data storage,
# and pushes the waveform to EPICS on a rising edge of static.trigg.
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "PLC_ID=0, SAMPLE_RATE_MS=10, FILE=./plc/data_storage_trigger.plc, PLC_MACROS='DS_ID=0, DBG='"
dbLoadRecords("ecmcPlcBinary.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.trigg,REC_NAME=-PushDataTrigger")
dbLoadRecords("ecmcPlcAnalog.db","P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc0.static.signal,REC_NAME=-Signal")
