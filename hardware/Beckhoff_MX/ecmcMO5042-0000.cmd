# WARNING: UNTESTED
epicsEnvSet("ECMC_EC_HWTYPE",        "MO5042-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8143308b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd, "RESET=1"


#SM2: PhysAddr 0x1100, DefaultSize    6, ControlRegister 0x24, Enable 1
#  RxPDO 0x1600 "FB RxPDO-Map Outputs Ch.1"
#    PDO entry 0x7000:01,  1 bit, "Set"
#    PDO entry 0x7000:02,  1 bit, "Direction"
#    PDO entry 0x0000:00, 14 bit, "Gap"
#  RxPDO 0x1601 "FB RxPDO-Map Outputs Ch.2"
#    PDO entry 0x7010:01,  1 bit, "Set"
#    PDO entry 0x7010:02,  1 bit, "Direction"
#    PDO entry 0x0000:00, 14 bit, "Gap"
#  RxPDO 0x1620 "EFU RxPDO-Map Outputs"
#    PDO entry 0x7020:01,  1 bit, "Enable"
#    PDO entry 0x7020:02,  1 bit, "Control via Process Data"
#    PDO entry 0x7020:03,  1 bit, "Reset"
#    PDO entry 0x0000:00, 13 bit, "Gap"
#SM3: PhysAddr 0x1180, DefaultSize   28, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "FB TxPDO-Map Inputs Ch.1"
#    PDO entry 0x6000:01,  1 bit, "Warning"
#    PDO entry 0x6000:02,  1 bit, "Error"
#    PDO entry 0x6000:03,  1 bit, "Ready"
#    PDO entry 0x0000:00,  5 bit, "Gap"
#    PDO entry 0x0000:00,  4 bit, "Gap"
#    PDO entry 0x6000:0d,  1 bit, "Diag"
#    PDO entry 0x6000:0e,  1 bit, "TxPDO State"
#    PDO entry 0x6000:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x6000:11, 64 bit, "Position"
#  TxPDO 0x1a02 "FB TxPDO-Map Inputs Ch.2"
#    PDO entry 0x6010:01,  1 bit, "Warning"
#    PDO entry 0x6010:02,  1 bit, "Error"
#    PDO entry 0x6010:03,  1 bit, "Ready"
#    PDO entry 0x0000:00,  5 bit, "Gap"
#    PDO entry 0x0000:00,  4 bit, "Gap"
#    PDO entry 0x6010:0d,  1 bit, "Diag"
#    PDO entry 0x6010:0e,  1 bit, "TxPDO State"
#    PDO entry 0x6010:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x6010:11, 64 bit, "Position"
#  TxPDO 0x1a20 "EFU TxPDO-Map Inputs"
#    PDO entry 0x6020:01,  1 bit, "Warning"
#    PDO entry 0x6020:02,  1 bit, "Error"
#    PDO entry 0x6020:03,  1 bit, "Tripped"
#    PDO entry 0x6020:04,  1 bit, "Enabled"
#    PDO entry 0x0000:00, 10 bit, "Gap"
#    PDO entry 0x6020:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x0000:00, 16 bit, "Gap"
#    PDO entry 0x6020:12, 32 bit, "Current"


#- FB Outputs Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,B1,encoderSet01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x02,B1,encoderDir01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,U8,dummyStub1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,B4,dummyStub2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,B2,dummyStub3)"

#- FB Outputs Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x7010,0x01,B1,encoderSet02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x7010,0x02,B1,encoderDir02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x0000,0x00,U8,dummyStub4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x0000,0x00,B4,dummyStub5)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x0000,0x00,B2,dummyStub6)"

#- EFU Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x7020,0x01,U16,control01)"


#- FB Inputs Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U16,encoderStatus01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x11,S64,positionActual01)"

#- FB Inputs Ch.2
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x6010,0x01,U16,encoderStatus02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x6010,0x11,S64,positionActual02)"

#- EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a20,0x6020,0x01,U16,status02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a20,0x0000,0x00,U16,dummyStub7)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a20,0x6020,0x11,S32,current)"
