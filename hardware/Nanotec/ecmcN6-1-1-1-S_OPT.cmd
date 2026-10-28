#-d /**
#-d   \brief N6 CSV hardware with optional raw position and masked output gates.
#-d   \param RAW_POS Use 0x6063 as positionActual01; name 0x6064 positionActualScaled01, 0/1, default 0.
#-d   \param HOMING Map homing parameters and sequence-26 trigger alias, 0/1, default 0.
#-d   \param CAPTURE Map 3241:01..0C capture readbacks, 0/1, default 0.
#-d   \param ANALOG_IN Map both 3320 analog inputs, 0/1, default 0.
#-d   \details Legacy PDO layout and motor component type N6 are retained. No units
#-d            or output routing are changed here; apply PositionOutput later.
#-d */
ecmcEpicsEnvSetCalcTernary(N6_OPT_BAD,"'${RAW_POS=0}'!='0' and '${RAW_POS=0}'!='1'","","#-")
${N6_OPT_BAD}ecmcExit Error: N6_OPT RAW_POS must be 0 or 1
ecmcEpicsEnvSetCalcTernary(N6_OPT_BAD,"'${HOMING=0}'!='0' and '${HOMING=0}'!='1'","","#-")
${N6_OPT_BAD}ecmcExit Error: N6_OPT HOMING must be 0 or 1
ecmcEpicsEnvSetCalcTernary(N6_OPT_BAD,"'${CAPTURE=0}'!='0' and '${CAPTURE=0}'!='1'","","#-")
${N6_OPT_BAD}ecmcExit Error: N6_OPT CAPTURE must be 0 or 1
ecmcEpicsEnvSetCalcTernary(N6_OPT_BAD,"'${ANALOG_IN=0}'!='0' and '${ANALOG_IN=0}'!='1'","","#-")
${N6_OPT_BAD}ecmcExit Error: N6_OPT ANALOG_IN must be 0 or 1
epicsEnvUnset(N6_OPT_BAD)

#- Keep the conventional feedback name for the fine open-loop counter.
#- Without RAW_POS, the base descriptor keeps its original entry names.
ecmcEpicsEnvSetCalcTernary(N6_OPT_POSITION_NAME,"${RAW_POS=0}==1","positionActualScaled01","positionActual01")
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcN6-1-1-1-S.cmd
epicsEnvUnset(N6_OPT_POSITION_NAME)

#- Preserve the prefix computed by addSlave.
epicsEnvSet(ECMC_EC_HWTYPE,${HW_DESC=N6-1-1-1-S_OPT})
epicsEnvSet(ECMC_SUBST_TYPE,N6-1-1-1-S_OPT)
epicsEnvSet(ECMC_HW_PANEL,N6-1-1-1-S_OPT)

#- Append to existing PDO 1A03 rather than assigning a fifth TxPDO.
ecmcEpicsEnvSetCalcTernary(N6_OPT_RAW,"${RAW_POS=0}==1","","#-")
${N6_OPT_RAW}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a03,0x6063,0x00,S32,positionActual01)"
${N6_OPT_RAW}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogInput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Enc,suffix=-PosScaled,sourceName=positionActualScaled,EGU=counts,PREC=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_OPT_config.template,ECMC_P=${ECMC_P},PARAM='RAW_POS=${RAW_POS=0},HOMING=${HOMING=0},CAPTURE=${CAPTURE=0},ANALOG_IN=${ANALOG_IN=0}'"

#- Feature-specific records belong to this hardware option, like PosScaled.
#- Load explicitly so they also exist when default substitutions are disabled.
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_outputEnable.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,MASK=0x00010000'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_outputEnable.template,ECMC_P=${ECMC_P},PARAM='CH_ID=02,MASK=0x00020000'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_outputEnable.template,ECMC_P=${ECMC_P},PARAM='CH_ID=03,MASK=0x00040000'"

#- Optional drive-side homing parameters. Reuse SM2 PDO 1603 to retain the
#- existing assignment slots. No homing command is issued by this option.
ecmcEpicsEnvSetCalcTernary(N6_OPT_HOME,"${HOMING=0}==1","","#-")
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1603,0x6098,0x00,S8,homingMethod01)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1603,0x607C,0x00,S32,homeOffset01)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1603,0x6099,0x01,U32,homingVelocitySwitch01)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1603,0x6099,0x02,U32,homingVelocityZero01)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1603,0x609A,0x00,U32,homingAcceleration01)"
#- As for MCS2, a dedicated output-data bit is applied after the parent's
#- whole controlword in the process image. Sequence 26 can therefore hold
#- bit 4 without the DS402 axis's whole-word write clearing its trigger.
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.EcAddDataDT(ec${ECMC_EC_MASTER_ID=0}.s${ECMC_EC_SLAVE_NUM}.driveControl01,0,4,1,B1,driveCmdExe01)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},driveCmdExe01,0)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},homingMethod01,35)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},homeOffset01,0)"
#- Drive homing dynamics use the documented presets. Method 35 does not search.
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},homingVelocitySwitch01,50)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},homingVelocityZero01,10)"
${N6_OPT_HOME}ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},homingAcceleration01,500)"
#- PINI=0 preserves the initialized method/offset and CSV mode at IOC startup.
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-HomeMethod,sourceName=homingMethod,PINI=0,PREC=0,EGU=,DRVL=-128,DRVH=127'"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-HomeOffset,sourceName=homeOffset,PINI=0,PREC=0,EGU=counts'"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-ModeCmd,sourceName=modeControl,PINI=0,PREC=0,EGU=,DRVL=-128,DRVH=127'"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogInput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-ModeAct,sourceName=modeActual,PREC=0,EGU='"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-HomeVelTo,sourceName=homingVelocitySwitch,PINI=0,PREC=0,EGU=user,DRVL=0,DRVH=2147483647'"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-HomeVelFrm,sourceName=homingVelocityZero,PINI=0,PREC=0,EGU=user,DRVL=0,DRVH=2147483647'"
${N6_OPT_HOME}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogOutput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=Drv,suffix=-HomeAcc,sourceName=homingAcceleration,PINI=0,PREC=0,EGU=user,DRVL=0,DRVH=2147483647'"
epicsEnvSet(ECMC_N6_M${ECMC_EC_MASTER_ID=0}_S${ECMC_EC_SLAVE_NUM}_HOMING,${HOMING=0})
epicsEnvUnset(N6_OPT_HOME)

#- Capture readbacks are TxPDO-only according to the N6 object dictionary.
#- Leave arming/routing unchanged; configure 3241:01/05/09 separately by SDO.
#- Distribute four-entry groups across 1A00..1A02 (max eight entries/PDO).
ecmcEpicsEnvSetCalcTernary(N6_OPT_CAPTURE,"${CAPTURE=0}==1","","#-")
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x3241,0x01,U32,captureControl01)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x3241,0x02,U32,captureCount01)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x3241,0x03,U32,capturePosition01)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x3241,0x04,U32,captureRawPosition01)"
${N6_OPT_CAPTURE}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_capture.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01'"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x3241,0x05,U32,captureControl02)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x3241,0x06,U32,captureCount02)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x3241,0x07,U32,capturePosition02)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x3241,0x08,U32,captureRawPosition02)"
${N6_OPT_CAPTURE}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_capture.template,ECMC_P=${ECMC_P},PARAM='CH_ID=02'"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x3241,0x09,U32,captureControl03)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x3241,0x0A,U32,captureCount03)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x3241,0x0B,U32,capturePosition03)"
${N6_OPT_CAPTURE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x3241,0x0C,U32,captureRawPosition03)"
${N6_OPT_CAPTURE}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_capture.template,ECMC_P=${ECMC_P},PARAM='CH_ID=03'"
epicsEnvUnset(N6_OPT_CAPTURE)

#- With RAW_POS and both analog inputs, 1A03 uses exactly eight entries.
ecmcEpicsEnvSetCalcTernary(N6_OPT_AI,"${ANALOG_IN=0}==1","","#-")
${N6_OPT_AI}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a03,0x3320,0x01,S32,analogInput01)"
${N6_OPT_AI}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogInput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=01,KEY=AI,sourceName=analogInput,EGU=user,PREC=0'"
${N6_OPT_AI}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a03,0x3320,0x02,S32,analogInput02)"
${N6_OPT_AI}${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmc_analogInput-chX.template,ECMC_P=${ECMC_P},PARAM='CH_ID=02,KEY=AI,sourceName=analogInput,EGU=user,PREC=0'"
epicsEnvUnset(N6_OPT_AI)

#- Per-master/slave capability used by ecmccomp's PositionOutput validator.
epicsEnvSet(ECMC_N6_M${ECMC_EC_MASTER_ID=0}_S${ECMC_EC_SLAVE_NUM}_RAW_POS,${RAW_POS=0})
epicsEnvUnset(N6_OPT_RAW)
