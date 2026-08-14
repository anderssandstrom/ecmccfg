epicsEnvSet("ECMC_EC_HWTYPE",        "MO7062-0100")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8154f18b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd


#SM2: PhysAddr 0x1200, DefaultSize   12, ControlRegister 0x24, Enable 1
#  RxPDO 0x1600 "DRV RxPDO-Map Controlword Ch.1"
#    PDO entry 0x7010:01, 16 bit, "Controlword"
#  RxPDO 0x1601 "DRV RxPDO-Map Target velocity Ch.1"
#    PDO entry 0x7010:06, 32 bit, "Target velocity"
#  RxPDO 0x1680 "DRV RxPDO-Map Controlword Ch.2"
#    PDO entry 0x7110:01, 16 bit, "Controlword"
#  RxPDO 0x1681 "DRV RxPDO-Map Target velocity Ch.2"
#    PDO entry 0x7110:06, 32 bit, "Target velocity"
#SM3: PhysAddr 0x1900, DefaultSize   20, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "FB TxPDO-Map Position Ch.1"
#    PDO entry 0x6000:11, 32 bit, "Position"
#  TxPDO 0x1a01 "DRV TxPDO-Map Statusword Ch.1"
#    PDO entry 0x6010:01, 16 bit, "Statusword"
#  TxPDO 0x1a80 "FB TxPDO-Map Position Ch.2"
#    PDO entry 0x6100:11, 32 bit, "Position"
#  TxPDO 0x1a81 "DRV TxPDO-Map Statusword Ch.2"
#    PDO entry 0x6110:01, 16 bit, "Statusword"


ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x0,0,1)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x1,0x1600,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x2,0x1601,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x3,0x1680,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x4,0x1681,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x0,4,1)"

ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x0,0,1)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x1,0x1a00,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x2,0x1a01,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x3,0x1a80,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x4,0x1a81,2)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x0,4,1)"


#- ========================== Channel 1 ==========================
#- Activly choose CSV
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x7010,0x3,9,1)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7010,0x01,U16,driveControl01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x7010,0x06,S32,velocitySetpoint01)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x11,U32,positionActual01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6010,0x01,U16,driveStatus01)"


#- ========================== Channel 2 ==========================
#- Activly choose CSV
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x7110,0x3,9,1)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1680,0x7110,0x01,U16,driveControl02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1681,0x7110,0x06,S32,velocitySetpoint02)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6100,0x11,U32,positionActual02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a81,0x6110,0x01,U16,driveStatus02)"

#- ############ Distributed clocks config:
#- Configure DC clock
#- From TwinCAT: SYNC 0: User defined 62.5 us, SYNC 1: 2000 us <-- I set this to the cycle time below
#ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)
#ecmcConfigOrDie "Cfg.EcSlaveConfigDC(${ECMC_EC_SLAVE_NUM},0x700,62500,${ECMC_SYNC_0_OFFSET_NS=0},${ECMC_TEMP_PERIOD_NANO_SECS},${ECMC_SYNC_1_OFFSET_NS=0})"
#epicsEnvUnset("ECMC_TEMP_PERIOD_NANO_SECS")

#- watchdog
#${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd

#ecmcConfigOrDie "Cfg.EcSetDelayECOkAtStartup(${ECMC_EC_STARTUP_DELAY=4000})"
