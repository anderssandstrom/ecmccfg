#- Same DC schedule and calibrated input timing as legacy EX7062.
ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)
ecmcEpicsEnvSetCalc("ECMC_SYNC_1","${ECMC_TEMP_PERIOD_NANO_SECS}-62500")

ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"

ecmcConfigOrDie "Cfg.EcSlaveConfigDC(${ECMC_EC_SLAVE_NUM},0x700,62500,${SYNC_0_SHIFT=0},${ECMC_SYNC_1},0)"

#- Shared ED7062/EL7062 input timing metadata.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062Timing.cmd

epicsEnvUnset(ECMC_SYNC_1)
epicsEnvUnset(ECMC_TEMP_PERIOD_NANO_SECS)
