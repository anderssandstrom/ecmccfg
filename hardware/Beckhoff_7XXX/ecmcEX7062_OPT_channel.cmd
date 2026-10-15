#- Internal: resolved channel options and object addresses.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT_validate.cmd
ecmcEpicsEnvSetCalc(EX7062_PDO,"5632+${PDO_OFFSET}","%d")
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,${EX7062_PDO},${DRV_OUT},0x01,U16,driveControl${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"5633+${PDO_OFFSET}","%d")
${EX7062_CSV}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,${EX7062_PDO},${DRV_OUT},0x06,S32,velocitySetpoint${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"5634+${PDO_OFFSET}","%d")
${EX7062_CST}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,${EX7062_PDO},${DRV_OUT},0x09,S16,torqueSetpoint${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"5638+${PDO_OFFSET}","%d")
${EX7062_CSP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,${EX7062_PDO},${DRV_OUT},0x05,S32,positionSetpoint${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"5639+${PDO_OFFSET}","%d")
${EX7062_TP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,${EX7062_PDO},${TP_OUT},0x01,U16,touchProbeControl${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6656+${PDO_OFFSET}","%d")
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${FB_IN},0x11,U32,positionActual${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6657+${PDO_OFFSET}","%d")
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${DRV_IN},0x01,U16,driveStatus${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6658+${PDO_OFFSET}","%d")
${EX7062_EXT_DIAG}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${DRV_IN},0x07,S32,velocityActual${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6659+${PDO_OFFSET}","%d")
${EX7062_EXT_DIAG}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${DRV_IN},0x08,S16,torqueActual${CH_ID})"
ecmcEpicsEnvSetCalcTernary(EX7062_SUPPLY,"${CH_NUM}==1 and ${DIAG=1}==1","","#-")
${EX7062_SUPPLY}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a04,0x6010,0x11,U16,voltageActual01)"
${EX7062_SUPPLY}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a05,0x6010,0x13,U16,temperatureActual01)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6663+${PDO_OFFSET}","%d")
${EX7062_TP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${TP_IN},0x01,U16,touchProbeStatus${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6664+${PDO_OFFSET}","%d")
${EX7062_TP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${TP_IN},0x11,U32,touchProbePositionPos${CH_ID}_1)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6665+${PDO_OFFSET}","%d")
${EX7062_TP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${TP_IN},0x12,U32,touchProbePositionNeg${CH_ID}_1)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6672+${PDO_OFFSET}","%d")
${EX7062_INPUTS}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${BI_IN},0x01,U16,binaryInputs${CH_ID})"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6673+${PDO_OFFSET}","%d")
${EX7062_TP_DC}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${TP_IN},0x15,U32,touchProbeTimestampPos${CH_ID}_1)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6674+${PDO_OFFSET}","%d")
${EX7062_TP_DC}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${TP_IN},0x16,U32,touchProbeTimestampNeg${CH_ID}_1)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6677+${PDO_OFFSET}","%d")
${EX7062_ENC2}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${FB_IN},0x15,U32,positionActual${CH_ID}_2)"
ecmcEpicsEnvSetCalc(EX7062_PDO,"6662+${PDO_OFFSET}","%d")
${EX7062_FOLLOWING}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,${EX7062_PDO},${DRV_IN},0x06,S32,followingError${CH_ID})"
${EX7062_CSV}epicsEnvSet(EX7062_MODE_CODE,9)
${EX7062_CSV}epicsEnvSet(EX7062_MODE_VALUE,0)
${EX7062_CSP}epicsEnvSet(EX7062_MODE_CODE,8)
${EX7062_CSP}epicsEnvSet(EX7062_MODE_VALUE,1)
${EX7062_CST}epicsEnvSet(EX7062_MODE_CODE,10)
${EX7062_CST}epicsEnvSet(EX7062_MODE_VALUE,2)
#- Write now and replay on reconnection; slave exists after PDO registration.
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},${DRV_OUT},0x03,${EX7062_MODE_CODE},1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},${DRV_OUT},0x03,${EX7062_MODE_CODE},1)"
ecmcConfigOrDie "Cfg.EcSetSlaveNeedSDOSettings(${ECMC_EC_SLAVE_NUM},${CH_NUM},1)"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_common.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_CSV}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_csv.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_CSP}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_csp.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_CST}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_cst.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_INPUTS}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_inputs.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_ENC2}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_enc2.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_TP}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEL7062_TP-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_TP_DC}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_tpDc.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_AUTOTUNE}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEL7062_autoTune-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID},P=${ECMC_PREFIX},CH_ID_VAL=${CH_NUM}'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX72XX_OPT_state.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID}'"
${EX7062_EXT_DIAG}${SCRIPTEXEC} ${ecmccfg_DIR}applySubstitutions.cmd "SUBST_FILE=ecmcEX7062_OPT_diagnostics.substitutions,ECMC_P=${ECMC_P},MACROS='OPT_CH_ID=${CH_ID}'"
${EX7062_FOLLOWING}${SCRIPTEXEC} ${ecmccfg_DIR}applySubstitutions.cmd "SUBST_FILE=ecmcEX72XX_OPT_followingError.substitutions,ECMC_P=${ECMC_P},MACROS='OPT_CH_ID=${CH_ID},OPT_POS_ESLO=1,OPT_POS_EGU=Counts'"
ecmcEpicsEnvSetCalc(EX7062_FOLLOWING_VALUE,"'${MODE}'='CSP' and ${EXT_DIAG}==1","%d")
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcEX7062_OPT_config.template,ECMC_P=${ECMC_P},PARAM='CH_ID=${CH_ID},CFG_SUFFIX=${CFG_SUFFIX},MODE_VALUE=${EX7062_MODE_VALUE},TP=${TP},INPUTS=${INPUTS},ENC2=${ENC2},EXT_DIAG=${EXT_DIAG},TP_DC=${TP_DC},AUTOTUNE=${AUTOTUNE},FOLLOWING=${EX7062_FOLLOWING_VALUE}'"
