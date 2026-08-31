#- TESTED
#- ecmc hardware config for: MS1010-1002-1334
#- Power infeed + forwarding, 230 V AC/10 A, 24 V DC/7 A power supply
#- Source ESI: Beckhoff MSxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MS1010-1002-1334")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4d4609b")
epicsEnvSet("ECMC_EC_REVISION",      "0x04005356")
epicsEnvSet("ECMC_HW_PANEL"          "${ECMC_EC_HWTYPE}")

#- Verify slave identity.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"

#- SM2, RxPDO 0x1600: PSU control (16 bits total).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,U16,PSU_Ctrl)"
#- PSU_Ctrl B0=Disable output
#- PSU_Ctrl B1=Reset
#- PSU_Ctrl B2..B15=gap

#- SM3, TxPDO 0x1a00: PSU status and measurements (18 bytes total).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U16,PSU_Stat)"
#- PSU_Stat B0=Warning
#- PSU_Stat B1=Error
#- PSU_Stat B2=I2T warning
#- PSU_Stat B3=DC OK
#- PSU_Stat B4=Overrange
#- PSU_Stat B5..B13=gap
#- PSU_Stat B14..B15=Input cycle counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U16,PSU_Gap01,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x11,F32,PSU_OutVolt)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x12,F32,PSU_OutCurr)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x13,U8,PSU_I2T)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U8,PSU_Gap02,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x15,U16,PSU_Info01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x16,U16,PSU_Info02)"

#- No Distributed Clocks mode is specified by the ESI.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
