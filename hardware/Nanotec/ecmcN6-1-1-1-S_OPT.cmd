#-d /**
#-d   \brief N6 CSV hardware with optional raw position and masked output gates.
#-d   \param RAW_POS Use 0x6063 as positionActual01; name 0x6064 positionActualScaled01, 0/1, default 0.
#-d   \details Legacy PDO layout and motor component type N6 are retained. No units
#-d            or output routing are changed here; apply PositionOutput later.
#-d */
ecmcEpicsEnvSetCalcTernary(N6_OPT_BAD,"'${RAW_POS=0}'!='0' and '${RAW_POS=0}'!='1'","","#-")
${N6_OPT_BAD}ecmcExit Error: N6_OPT RAW_POS must be 0 or 1
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
${SCRIPTEXEC} ${ecmccfg_DIR}applyTemplate.cmd "TEMPLATE_FILE=ecmcN6_OPT_config.template,ECMC_P=${ECMC_P},PARAM='RAW_POS=${RAW_POS=0}'"

#- Per-master/slave capability used by ecmccomp's PositionOutput validator.
epicsEnvSet(ECMC_N6_M${ECMC_EC_MASTER_ID=0}_S${ECMC_EC_SLAVE_NUM}_RAW_POS,${RAW_POS=0})
epicsEnvUnset(N6_OPT_RAW)
