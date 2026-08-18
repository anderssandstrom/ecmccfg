# WARNING: UNTESTED
#- ecmc hardware config for: MS4210-1003-1114
#- EtherCAT power output, 24 V DC/2x 10 A, switchable
#- Source ESI: Beckhoff MSxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MS4210-1003-1114")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4f0809b")
epicsEnvSet("ECMC_EC_REVISION",      "0x0500798a")
epicsEnvSet("ECMC_HW_PANEL"          "${ECMC_EC_HWTYPE}")

#- Verify slave identity. The ESI also lists the older revision 0x0400798a.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"

#- SM2, RxPDO 0x1600: Us output control.
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,U16,Us_Ctrl)"
#- Us_Ctrl: B0=Reset, B1=gap, B2=Enable, B3=Control via process data, B4..B15=gap

#- SM2, RxPDO 0x1610: Up output control.
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7010,0x01,U16,Up_Ctrl)"
#- Up_Ctrl: B0=Reset, B1=gap, B2=Enable, B3=Control via process data, B4..B15=gap

#- SM3, TxPDO 0x1a00: Us output status.
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U32,Us_Stat)"
#- Us_Stat: B0=Enabled, B1=Tripped, B3=Overload, B6=Undervoltage
#-          B7=Current level warning, B8=Cool-down lock, B14..B15=Input cycle counter
#-          B18=Error, B21=Load level warning; all other bits are gaps

#- SM3, TxPDO 0x1a10: Up output status.
ecmcConfigOrDie "Cfg.EcAddEntryFixedDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x01,U32,Up_Stat)"
#- Up_Stat: B0=Enabled, B1=Tripped, B3=Overload, B6=Undervoltage
#-          B7=Current level warning, B8=Cool-down lock, B14..B15=Input cycle counter
#-          B18=Error, B21=Load level warning; all other bits are gaps

#- Optional load-information PDOs 0x1a01 and 0x1a11 are not assigned by default.
#- No Distributed Clocks mode is specified by the ESI.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
