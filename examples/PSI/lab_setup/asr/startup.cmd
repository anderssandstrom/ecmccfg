# Queued PREOP SDO autosave example: EK1100 at 0, EL7041 at 1.
# Run from this directory. See README.md for first commissioning and restart.
require ecmccfg "ENG_MODE=1,MASTER_ID=0,NAMING=mXsXXX"
require "autoSRarray"

# Default to commissioning: IOC starts, but master activation waits for
# ecmcStartAppModeAsync(0). Set SDO_AUTO_START=1 for automatic restored startup.
epicsEnvSet(ECMC_SDO_AUTO_START,"${SDO_AUTO_START=0}")
epicsEnvSet(ECMC_STARTUP_GATE,1)

# Keep autosave configuration local to this IOC. Create the save directory first.
set_requestfile_path("./db")
set_savefile_path("${ASR_SAVE_DIR=./save}")
# Waveforms require pass 1. Do not register this file for pass 0.
set_pass1_restoreFile("sdo_settings.sav","IOC=${IOC}")
afterInit "create_monitor_set('sdo_settings.req',5,'IOC=${IOC}')"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=1,HW_DESC=EL7041"

# EL7041 current settings [mA], U16. No motor component or motion axis is loaded.
# Do not also configure these addresses using Cfg.EcAddSdo / a motor component.
# Automatic interface: a Val write queues a write request.
${SCRIPTEXEC} ${ecmccfg_DIR}addEcSdoRT.cmd "SLAVE_ID=1,INDEX=0x8010,SUBINDEX=0x01,DT=U16,NAME=MaxCurrent,QUEUE=1,WRITE_ON_VAL=1,RESTORE=1"
# Manual interface: Val stages; WrtCmd queues the write. RdCmd remains available.
${SCRIPTEXEC} ${ecmccfg_DIR}addEcSdoRT.cmd "SLAVE_ID=1,INDEX=0x8010,SUBINDEX=0x02,DT=U16,NAME=StandbyCurrent,QUEUE=1,WRITE_ON_VAL=0,RESTORE=1"

${SCRIPTEXEC} ${ecmccfg_DIR}applyConfig.cmd
${SCRIPTEXEC} ${ecmccfg_DIR}setAppMode.cmd
# The PSI launcher completes IOC initialization.
