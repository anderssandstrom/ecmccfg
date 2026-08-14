epicsEnvSet("ECMC_EC_HWTYPE",        "MS1132-2001")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4d5732b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

ecmcConfigOrDie "Cfg.EcAddSlave(0,${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID})"




#SM2: PhysAddr 0x1200, DefaultSize    0, ControlRegister 0x24, Enable 1
#  RxPDO 0x1600 "PSU RxPDO-Map Outputs"
#    PDO entry 0x7000:01,  1 bit, "Disable Output"
#    PDO entry 0x7000:02,  1 bit, "Reset"
#    PDO entry 0x0000:00, 14 bit, "Gap"
#SM3: PhysAddr 0x1300, DefaultSize    0, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "PSU TxPDO-Map Inputs"
#    PDO entry 0x6000:01,  1 bit, "Warning"
#    PDO entry 0x6000:02,  1 bit, "Error"
#    PDO entry 0x6000:03,  1 bit, "I2T Warning"
#    PDO entry 0x6000:04,  1 bit, "DC OK"
#    PDO entry 0x6000:05,  1 bit, "Overrange"
#    PDO entry 0x0000:00,  9 bit, "Gap"
#    PDO entry 0x6000:0f,  2 bit, "Input Cycle Counter"
#    PDO entry 0x0000:00, 16 bit, "Gap"
#    PDO entry 0x6000:11, 32 bit, "Output Voltage"
#    PDO entry 0x6000:12, 32 bit, "Output Current"
#    PDO entry 0x6000:13,  8 bit, "I2T Utilization"
#    PDO entry 0x0000:00,  8 bit, "Gap"
#    PDO entry 0x6000:15, 16 bit, "Info Data 1"
#    PDO entry 0x6000:16, 16 bit, "Info Data 2"

##- PSU Outputs
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,U16,control1)"
#
##- PSU Inputs
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U16,status)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U16,DummyStub4)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x11,U32,OutputVoltage)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x12,U32,OutputCurrent)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x13,U8,I2T_Utilization)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x14,U8,DummyStub5)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x15,U16,InfoData1)"
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x16,U16,InfoData2)"
#
#
#
##- ############ Distributed clocks config:
##- Configure DC clock
##- From TwinCAT: SYNC 0: User defined 62.5 us, SYNC 1: 2000 us <-- I set this to the cycle time below
#ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)
#ecmcConfigOrDie "Cfg.EcSlaveConfigDC(${ECMC_EC_SLAVE_NUM},0x700,125000,${ECMC_SYNC_0_OFFSET_NS=0},125000,${ECMC_SYNC_1_OFFSET_NS=0})"
#epicsEnvUnset("ECMC_TEMP_PERIOD_NANO_SECS")
#
##- watchdog
#${SCRIPTEXEC} ${ecmccfg_DIR}ecmcWatchDog.cmd
