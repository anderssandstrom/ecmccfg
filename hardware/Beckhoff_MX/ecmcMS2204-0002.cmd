#- TESTED
#- Common PDO configuration for MS2204-0002 variants.
#- Source ESI: Beckhoff MSxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MS2204-0002")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4dedf0b")
epicsEnvSet("ECMC_SUBST_TYPE",       "MS2204-0002")

ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"

#- SM2, RxPDO 0x1600: EFU control (16 bits).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,U16,EFU_Ctrl)"
#- EFU_Ctrl B0=Enable, B1=Control via process data, B2=Reset, B3..B15=gap

#- SM3, TxPDO 0x1a00: EFU status/current (8 bytes).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U16,EFU_Stat)"
#- EFU_Stat B0=Warning, B1=Error, B2=Tripped, B3=Enabled
#- EFU_Stat B4..B13=gap, B14..B15=Input cycle counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U16,EFU_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x12,F32,EFU_Curr)"

#- SM3, TxPDO 0x1a10: power-infeed status/measurements (12 bytes).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x01,U16,PWI_Stat)"
#- PWI_Stat B0=Warning, B1..B13=gap, B14..B15=Input cycle counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,U16,PWI_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x12,F32,PWI_Volt)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x13,F32,PWI_Curr)"

#- No Distributed Clocks mode is specified by the ESI.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
