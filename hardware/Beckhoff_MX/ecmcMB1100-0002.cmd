# WARNING: UNTESTED
#- ecmc hardware config for: MB1100-0002 Bluetooth gateway
#- Source ESI: Beckhoff MBxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MB1100-0002")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x044c08d2")
epicsEnvSet("ECMC_EC_REVISION",      "0x00010002")
epicsEnvSet("ECMC_HW_PANEL"          "${ECMC_EC_HWTYPE}")

#- Verify slave identity without restoring SDO defaults.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- SM2, RxPDO 0x1600: Bluetooth gateway control (16 bits).
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,U16,BTG_Ctrl)"
#- BTG_Ctrl: B0=Enable Bluetooth, B1=Activate pairing, B2..B15=gap

#- SM3, TxPDO 0x1a00: Bluetooth gateway status (16 bits).
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U16,BTG_Stat)"
#- BTG_Stat: B0=Dongle present, B1=Bluetooth enabled, B2=Pairing active
#-           B3=Connected, B4..B11=gap, B12=Diag, B13=gap
#-           B14..B15=Input cycle counter

#- No Distributed Clocks mode is specified by the ESI.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
