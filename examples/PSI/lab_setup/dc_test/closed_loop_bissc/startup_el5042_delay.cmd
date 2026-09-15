##############################################################################
## EL5042 BiSS-C relative-delay verification
##
## This startup uses the same closed-loop BiSS-C lab hardware, but the active
## test is only the relative-delay PLC:
##   encoder 1 = ED7062/EL7062 open-loop reference
##   encoder 2 = EL5042 BiSS-C
##
## Move the axis with constant velocity in both directions. The PLC prints the
## mean encoder2-encoder1 offset for positive and negative motion and estimates
## the relative delay from the direction-dependent position difference.

require ecmccfg dc_timing "ENG_MODE=1,ECMC_VER=dc_timing"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=2,HW_DESC=EL2819"
epicsEnvSet("SYNC_0_SHIFT","-20000")
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=22,HW_DESC=ED7062_TPDC"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=500, I_STDBY_MA=100, U_NOM_MV=48000,R_COIL_MOHM=2440,L_COIL_UH=3140'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Generic-Ch-Not-Used, CH_ID=2"
epicsEnvSet(DRV_SID,${ECMC_EC_SLAVE_NUM})
# Here 0 selects the primary/internal open-loop position (ch 1 and 2)
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8001,0x15,0,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8101,0x15,0,2)"
epicsEnvUnset("SYNC_0_SHIFT")
ecmcConfig "Cfg.EcSetSlaveTimingSource(22,2,0)"
# DO NOT USE ecmcConfig "Cfg.EcSetSlaveTimingOverride(22,2,-1,-44000,31250)"

epicsEnvSet("SYNC_0_SHIFT","-20000")
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=9,HW_DESC=EL5042_DC"
epicsEnvUnset("SYNC_0_SHIFT")
ecmcConfig "Cfg.EcSetSlaveTimingSource(${ECMC_EC_SLAVE_NUM},2,1)"
ecmcConfig "Cfg.EcSetSlaveTimingOverride(${ECMC_EC_SLAVE_NUM},2,-1,0,100000)"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=2"
epicsEnvSet(ENC_SID,${ECMC_EC_SLAVE_NUM})

${SCRIPTEXEC} ${ecmccfg_DIR}setRecordUpdateRate.cmd "RATE_MS=1"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=25,HW_DESC=EL2252"
${SCRIPTEXEC} ${ecmccfg_DIR}setRecordUpdateRate.cmd "RATE_MS=10"

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis_open_loop.yaml,   DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${DRV_SID}, ENC_SID=${DRV_SID}, ENC_CH=01,PC_SLAVE=25"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd,    "FILE=./cfg/enc_biss.yaml, DEV=${IOC}, ENC_SID=${ENC_SID}"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=29,HW_DESC=EL1252"

#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=31,HW_DESC=EK1100"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL9227-5500"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL5042"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL5042"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL3204"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL2008"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL1008"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL7211-9014"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL7211-9014"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL7211-9014"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL7211-9014"
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL9576"

${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=20,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='EL5042 delay sequence'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=21,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Reference sample time'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=22,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='EL5042 sample time'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=23,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Reference position'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=24,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='EL5042-reference diff'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=25,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Reference velocity'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=26,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='EL5042 velocity'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=27,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Mean diff positive'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=28,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Mean diff negative'"
${SCRIPTEXEC} ${ecmccfg_DIR}addDataStorage.cmd "DS_ID=29,DS_SIZE=1000,SAMPLE_RATE_MS=-1,DS_TYPE=2,DESC='Relative delay ns'"

${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "PLC_ID=11,FILE=./cfg/el5042_delay.plc,PLC_MACROS='AX_ID=1,ENC_REF_ID=1,ENC_BISS_ID=2,REF_SID=22,BISS_SID=9,DS_BASE=20,PRINT_EVERY=100,PUSH_ASYN=1'"

# Useful commands:
# ecmcConfig "EcPrintSlaveConfig(9)"
# ecmcConfig "EcPrintSlaveConfig(22)"
# ecmcConfig "EcPrintControlTiming(9,25)"
