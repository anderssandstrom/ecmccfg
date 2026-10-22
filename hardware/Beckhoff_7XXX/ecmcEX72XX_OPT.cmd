#-d /**
#-d   \brief Shared option dispatcher for supported MDP742 EL/EP/ELM72xx and EL7411 drives
#-d   \param MODE CSV (default), CSP, CST or CSTCA (capable wrappers only)
#-d   \param TP 0 or 1, device default
#-d   \param INFO2 INPUTS, TEMP, ERRORS or NONE, subject to device capabilities
#-d   \param DIAG 0 or 1, device default (velocity, torque, DC voltage)
#-d   \param ENC_STAT 0 or 1; default 1 where supported, otherwise 0
#-d   \note MODE_1/2, TP_1/2, INFO2_1/2, DIAG_1/2 and ENC_STAT_1/2 override a channel.
#-d   \param SYNC_0_CYCLE Sync 0 period [ns], family default
#-d   \param SYNC_0_SHIFT Sync 0 shift [ns], device default
#-d   \param SYNC_1_CYCLE Sync 1 period [ns], family default
#-d   \param SYNC_1_SHIFT Sync 1 shift [ns], default 0
#-d   \param WATCHDOG_DIVIDER Watchdog divider, default derived from sample rate
#-d   \param WATCHDOG_INTERVALS Watchdog intervals, default derived from sample rate
#-d   \note Call through a device OPT wrapper, which fixes family/capabilities.
#-d   \file
#-d */

ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_EL,"'${PDO_FAMILY}'='EL72XX'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_ELM,"'${PDO_FAMILY}'='ELM72XX'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_EL7411,"'${PDO_FAMILY}'='EL7411'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_BAD_FAMILY,"'${PDO_FAMILY}'!='EL72XX' and '${PDO_FAMILY}'!='ELM72XX' and '${PDO_FAMILY}'!='EL7411'","","#-")
${ECMC_EX72XX_OPT_BAD_FAMILY}ecmcExit Error: unsupported OPT PDO family
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_BAD_CHANNELS,"${CHANNELS}!=1 and (${CHANNELS}!=2 or '${PDO_FAMILY}'!='ELM72XX')","","#-")
${ECMC_EX72XX_OPT_BAD_CHANNELS}ecmcExit Error: unsupported OPT channel count
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_CH2,"${CHANNELS}==2","","#-")

#- Reject options for a nonexistent second channel instead of silently ignoring them.
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_BAD_CH2_OPTIONS,"${CHANNELS}==1 and ('${MODE_2=}'!='' or '${TP_2=}'!='' or '${INFO2_2=}'!='' or '${DIAG_2=}'!='' or '${ENC_STAT_2=}'!='')","","#-")
${ECMC_EX72XX_OPT_BAD_CH2_OPTIONS}ecmcExit Error: channel 2 options require a two-channel drive

#- Validate all channels before slaveVerify resets the device.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_validate.cmd "CH_ID=01,CH_NUM=1,CFG_SUFFIX=,MODE=${MODE_1=${MODE=CSV}},TP=${TP_1=${TP=${DEFAULT_TP}}},INFO2=${INFO2_1=${INFO2=${DEFAULT_INFO2}}},DIAG=${DIAG_1=${DIAG=${DEFAULT_DIAG}}},ENC_STAT=${ENC_STAT_1=${ENC_STAT=}}"
${ECMC_EX72XX_OPT_CH2}${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_validate.cmd "CH_ID=02,CH_NUM=2,CFG_SUFFIX=02,MODE=${MODE_2=${MODE=CSV}},TP=${TP_2=${TP=${DEFAULT_TP}}},INFO2=${INFO2_2=${INFO2=${DEFAULT_INFO2}}},DIAG=${DIAG_2=${DIAG=${DEFAULT_DIAG}}},ENC_STAT=${ENC_STAT_2=${ENC_STAT=}}"

${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=true"

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_channel.cmd "CH_ID=01,CH_NUM=1,CFG_SUFFIX=,MODE=${MODE_1=${MODE=CSV}},TP=${TP_1=${TP=${DEFAULT_TP}}},INFO2=${INFO2_1=${INFO2=${DEFAULT_INFO2}}},DIAG=${DIAG_1=${DIAG=${DEFAULT_DIAG}}},ENC_STAT=${ENC_STAT_1=${ENC_STAT=}},FB_IN=0x6000,TP_IN=0x6001,DRV_IN=0x6010,DRV_OUT=0x7010,DRV_CFG=0x8010,FB_CFG=0x8008"
${ECMC_EX72XX_OPT_CH2}${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_channel.cmd "CH_ID=02,CH_NUM=2,CFG_SUFFIX=02,MODE=${MODE_2=${MODE=CSV}},TP=${TP_2=${TP=${DEFAULT_TP}}},INFO2=${INFO2_2=${INFO2=${DEFAULT_INFO2}}},DIAG=${DIAG_2=${DIAG=${DEFAULT_DIAG}}},ENC_STAT=${ENC_STAT_2=${ENC_STAT=}},FB_IN=0x6100,TP_IN=0x6101,DRV_IN=0x6110,DRV_OUT=0x7110,DRV_CFG=0x8110,FB_CFG=0x8108"

#- Timing and current/nameplate policy belong to the PDO family.
${ECMC_EX72XX_OPT_EL}${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_EL72XX_timing.cmd
${ECMC_EX72XX_OPT_ELM}${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT_ELM72XX_timing.cmd
${ECMC_EX72XX_OPT_EL7411}${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEL7411_OPT_timing.cmd
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
epicsEnvSet(ECMC_EC_STARTUP_DELAY,${ECMC_EC_STARTUP_DELAY_EL72XX=10})
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX72XX_OPT_channels.template,ECMC_P=${ECMC_P},PARAM='CHANNELS=${CHANNELS}'"
epicsEnvSet(DEFAULT_SUBS,false)
ecmcEpicsEnvSetCalcTernary(ECMC_HW_PANEL,"${CHANNELS}==2","EX72XX_OPT_2ch","EX72XX_OPT")
epicsEnvUnset(ECMC_EX72XX_OPT_EL)
epicsEnvUnset(ECMC_EX72XX_OPT_ELM)
epicsEnvUnset(ECMC_EX72XX_OPT_BAD_FAMILY)
epicsEnvUnset(ECMC_EX72XX_OPT_BAD_CHANNELS)
epicsEnvUnset(ECMC_EX72XX_OPT_CH2)
epicsEnvUnset(ECMC_EX72XX_OPT_BAD_CH2_OPTIONS)
epicsEnvUnset(ECMC_EX72XX_OPT_CSV)
epicsEnvUnset(ECMC_EX72XX_OPT_CSP)
epicsEnvUnset(ECMC_EX72XX_OPT_CST)
epicsEnvUnset(ECMC_EX72XX_OPT_TP)
epicsEnvUnset(ECMC_EX72XX_OPT_DIAG)
epicsEnvUnset(ECMC_EX72XX_OPT_INFO2_INPUTS)
epicsEnvUnset(ECMC_EX72XX_OPT_INFO2_TEMP)
epicsEnvUnset(ECMC_EX72XX_OPT_INFO2_ERRORS)
epicsEnvUnset(ECMC_EX72XX_OPT_INFO2_NONE)
epicsEnvUnset(ECMC_EX72XX_OPT_OFFSET)
epicsEnvUnset(ECMC_EX72XX_OPT_FOLLOWING)
epicsEnvUnset(ECMC_EX72XX_OPT_ENCODER_STATUS)
epicsEnvUnset(ECMC_EX72XX_OPT_ENC_DEFAULT)
epicsEnvUnset(ECMC_EX72XX_OPT_ENC_VALUE)
epicsEnvUnset(ECMC_EX72XX_OPT_EL7411)
epicsEnvUnset(ECMC_EX72XX_OPT_CSTCA)
epicsEnvUnset(ECMC_EX72XX_OPT_TORQUE)
