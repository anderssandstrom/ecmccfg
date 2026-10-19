#- Shared EL/ED7062 and constrained MO7062-0100 OPT dispatcher.
#- Default EL/ED process image matches ecmcEX7062.cmd (CSV); MO has no inputs.
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_DIAG,"'${DIAG=1}'!='0' and '${DIAG=1}'!='1'","","#-")
${EX7062_BAD_DIAG}ecmcExit Error: DIAG must be 0 or 1
#- These EL72xx options have no equivalent 7062 PDO selector.
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_SERVO_OPT,"'${INFO2=}'!='' or '${INFO2_1=}'!='' or '${INFO2_2=}'!='' or '${ENC_STAT=}'!='' or '${ENC_STAT_1=}'!='' or '${ENC_STAT_2=}'!=''","","#-")
${EX7062_BAD_SERVO_OPT}ecmcExit Error: INFO2 and ENC_STAT are not supported by 7062 OPT; use INPUTS and ENC2
#- DIAG is shared hardware supply/temperature, not a channel option.
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_DIAG_CH,"'${DIAG_1=}'!='' or '${DIAG_2=}'!=''","","#-")
${EX7062_BAD_DIAG_CH}ecmcExit Error: use shared DIAG instead of DIAG_1 or DIAG_2
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_validate.cmd "MODE=${MODE_1=${MODE=CSV}},TP=${TP_1=${TP=1}},INPUTS=${INPUTS_1=${INPUTS=${CAP_INPUTS=1}}},ENC2=${ENC2_1=${ENC2=1}},EXT_DIAG=${EXT_DIAG_1=${EXT_DIAG=0}},TP_DC=${TP_DC_1=${TP_DC=0}},AUTOTUNE=${AUTOTUNE_1=${AUTOTUNE=1}}"
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_validate.cmd "MODE=${MODE_2=${MODE=CSV}},TP=${TP_2=${TP=1}},INPUTS=${INPUTS_2=${INPUTS=${CAP_INPUTS=1}}},ENC2=${ENC2_2=${ENC2=1}},EXT_DIAG=${EXT_DIAG_2=${EXT_DIAG=0}},TP_DC=${TP_DC_2=${TP_DC=0}},AUTOTUNE=${AUTOTUNE_2=${AUTOTUNE=1}}"
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=true"
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_channel.cmd "CH_ID=01,CH_NUM=1,CFG_SUFFIX=,MODE=${MODE_1=${MODE=CSV}},TP=${TP_1=${TP=1}},INPUTS=${INPUTS_1=${INPUTS=${CAP_INPUTS=1}}},ENC2=${ENC2_1=${ENC2=1}},EXT_DIAG=${EXT_DIAG_1=${EXT_DIAG=0}},TP_DC=${TP_DC_1=${TP_DC=0}},AUTOTUNE=${AUTOTUNE_1=${AUTOTUNE=1}},PDO_OFFSET=0,FB_IN=0x6000,TP_IN=0x6001,BI_IN=0x6020,DRV_IN=0x6010,DRV_OUT=0x7010,TP_OUT=0x7001"
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_channel.cmd "CH_ID=02,CH_NUM=2,CFG_SUFFIX=02,MODE=${MODE_2=${MODE=CSV}},TP=${TP_2=${TP=1}},INPUTS=${INPUTS_2=${INPUTS=${CAP_INPUTS=1}}},ENC2=${ENC2_2=${ENC2=1}},EXT_DIAG=${EXT_DIAG_2=${EXT_DIAG=0}},TP_DC=${TP_DC_2=${TP_DC=0}},AUTOTUNE=${AUTOTUNE_2=${AUTOTUNE=1}},PDO_OFFSET=128,FB_IN=0x6100,TP_IN=0x6101,BI_IN=0x6120,DRV_IN=0x6110,DRV_OUT=0x7110,TP_OUT=0x7101"

#- Supply diagnostics occur once, as in the legacy process image.
ecmcEpicsEnvSetCalcTernary(EX7062_DIAG,"${DIAG=1}==1","","#-")
${EX7062_DIAG}${SCRIPTEXEC} ${ecmccfg_DIR}applySubstitutions.cmd "SUBST_FILE=ecmcEX7062_OPT_supply.substitutions,ECMC_P=${ECMC_P}"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_supplyConfig.template,ECMC_P=${ECMC_P},PARAM='DIAG=${DIAG=1}'"
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_timing.cmd
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
epicsEnvSet(DEFAULT_SUBS,false)
epicsEnvSet(ECMC_HW_PANEL,EX7062_OPT)
epicsEnvUnset(EX7062_BAD_DIAG)
epicsEnvUnset(EX7062_BAD_DIAG_CH)
epicsEnvUnset(EX7062_DIAG)
epicsEnvUnset(EX7062_BAD_MODE)
epicsEnvUnset(EX7062_BAD_BOOL)
epicsEnvUnset(EX7062_BAD_TP_DC)
epicsEnvUnset(EX7062_BAD_FIXED)
epicsEnvUnset(EX7062_CSV)
epicsEnvUnset(EX7062_CSP)
epicsEnvUnset(EX7062_CST)
epicsEnvUnset(EX7062_TP)
epicsEnvUnset(EX7062_INPUTS)
epicsEnvUnset(EX7062_ENC2)
epicsEnvUnset(EX7062_EXT_DIAG)
epicsEnvUnset(EX7062_TP_DC)
epicsEnvUnset(EX7062_AUTOTUNE)
epicsEnvUnset(EX7062_FOLLOWING)
epicsEnvUnset(EX7062_PDO)
epicsEnvUnset(EX7062_MODE_CODE)
epicsEnvUnset(EX7062_FOLLOWING_VALUE)
epicsEnvUnset(EX7062_MODE_VALUE)
epicsEnvUnset(EX7062_SUPPLY)
epicsEnvUnset(EX7062_BAD_SERVO_OPT)
