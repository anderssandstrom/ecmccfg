#- Internal family mapping. See hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md for source documentation.
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_PDO_SUFFIX,"${CH_NUM}==1","0","4")
ecmcEpicsEnvSetCalcTernary(ECMC_EX72XX_OPT_DRV_SUFFIX,"${CH_NUM}==1","1","5")
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x16${ECMC_EX72XX_OPT_DRV_SUFFIX}0,${DRV_OUT},0x01,U16,driveControl${CH_ID})"
${ECMC_EX72XX_OPT_CSV}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x16${ECMC_EX72XX_OPT_DRV_SUFFIX}2,${DRV_OUT},0x06,S32,velocitySetpoint${CH_ID})"
${ECMC_EX72XX_OPT_TORQUE}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x16${ECMC_EX72XX_OPT_DRV_SUFFIX}3,${DRV_OUT},0x09,S16,torqueSetpoint${CH_ID})"
${ECMC_EX72XX_OPT_CSTCA}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x16${ECMC_EX72XX_OPT_DRV_SUFFIX}4,${DRV_OUT},0x0E,U16,commutationAngle${CH_ID})"
${ECMC_EX72XX_OPT_CSP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x16${ECMC_EX72XX_OPT_DRV_SUFFIX}1,${DRV_OUT},0x05,S32,positionSetpoint${CH_ID})"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_PDO_SUFFIX}0,${FB_IN},0x11,U32,positionActual${CH_ID})"
#- Aggregate the 16-bit feedback-status PDO, as in the EL family: bit 13
#- is position invalid, and bits 14-15 are the input cycle counter.
${ECMC_EX72XX_OPT_ENCODER_STATUS}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_PDO_SUFFIX}2,${FB_IN},0x01,U16,encoderStatus${CH_ID})"
${ECMC_EX72XX_OPT_TP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_PDO_SUFFIX}3,${TP_IN},0x01,U16,touchProbeStatus${CH_ID})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}0,${DRV_IN},0x01,U16,driveStatus${CH_ID})"
${ECMC_EX72XX_OPT_DIAG}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}2,${DRV_IN},0x07,S32,velocityActual${CH_ID})"
${ECMC_EX72XX_OPT_DIAG}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}3,${DRV_IN},0x08,S16,torqueActual${CH_ID})"
${ECMC_EX72XX_OPT_DIAG}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}4,${DRV_IN},0x12,U16,voltageActual${CH_ID})"
${ECMC_EX72XX_OPT_INFO2_TEMP}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}5,${DRV_IN},0x13,U16,temperatureActual${CH_ID})"
${ECMC_EX72XX_OPT_FOLLOWING}ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a${ECMC_EX72XX_OPT_DRV_SUFFIX}1,${DRV_IN},${FOLLOWING_SUB},S32,followingError${CH_ID})"

#- Read the electronic nameplate for this channel, as in the legacy ELM config.
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},${FB_CFG},0x1,1,1)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},${FB_CFG},0x2,1,1)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},${FB_CFG},0x3,1,1)"
epicsEnvUnset(ECMC_EX72XX_OPT_PDO_SUFFIX)
epicsEnvUnset(ECMC_EX72XX_OPT_DRV_SUFFIX)
