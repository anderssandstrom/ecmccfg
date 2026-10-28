#- Lab-only recovery for the rejected pulse-generator trial, not a component.
#- For ordinary output disarming, use the masked PosOutNN-Ena PVs instead.
#- Restore the original open-loop source/output settings after the pulse trial.
#- Load with the drive disabled, after applyComponent and before applyConfig.
#- This is specific to the original N6 lab setup: interface 1 was disabled,
#- all feedback selection masks were zero, outputs 1/2 were ordinary outputs.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${N6_SID=${ECMC_EC_SLAVE_NUM}},binaryOutputArray01,0)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x03,0,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x01,0,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x01,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x02,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x03,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x04,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60E6,0x01,0,4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60EB,0x01,1,4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3252,0x02,0x0010,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3252,0x03,0x0011,2)"
