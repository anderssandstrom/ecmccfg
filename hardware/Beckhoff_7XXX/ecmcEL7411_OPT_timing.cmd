#- Retain EL7411's DC schedule and initial peak-current policy.
ecmcEpicsEnvSetCalc(ECMC_EL7411_OPT_PERIOD_NS,"1000000000/${ECMC_EC_SAMPLE_RATE=1000}")
ecmcEpicsEnvSetCalc(ECMC_EL7411_OPT_SYNC1_NS,"${ECMC_EL7411_OPT_PERIOD_NS}-62500")
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x1,3,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x2,${ECMC_EL7411_OPT_PERIOD_NS},4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x1,3,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x2,${ECMC_EL7411_OPT_PERIOD_NS},4)"
ecmcConfigOrDie "Cfg.EcSlaveConfigDC(${ECMC_EC_SLAVE_NUM},0x700,${SYNC_0_CYCLE=62500},${SYNC_0_SHIFT=0},${SYNC_1_CYCLE=${ECMC_EL7411_OPT_SYNC1_NS}},${SYNC_1_SHIFT=0})"
#- Motor configuration overwrites this legacy initial 1000 mA peak-current value.
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x11,1000,4)"
epicsEnvUnset(ECMC_EL7411_OPT_PERIOD_NS)
epicsEnvUnset(ECMC_EL7411_OPT_SYNC1_NS)
