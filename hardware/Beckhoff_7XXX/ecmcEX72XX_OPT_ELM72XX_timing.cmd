#- Internal ELM timing policy: retain 62.5 us Sync 0 and bus-cycle Sync 1.
#- Do not apply EL-specific cycle-time SDOs or overwrite nameplate current settings.
ecmcEpicsEnvSetCalc(ECMC_EX72XX_OPT_PERIOD_NS,"1000000000/${ECMC_EC_SAMPLE_RATE=1000}")
ecmcConfigOrDie "Cfg.EcSlaveConfigDC(${ECMC_EC_SLAVE_NUM},0x700,${SYNC_0_CYCLE=62500},${SYNC_0_SHIFT=${ECMC_SYNC_0_OFFSET_NS=0}},${SYNC_1_CYCLE=${ECMC_EX72XX_OPT_PERIOD_NS}},${SYNC_1_SHIFT=${ECMC_SYNC_1_OFFSET_NS=0}})"
epicsEnvUnset(ECMC_EX72XX_OPT_PERIOD_NS)
