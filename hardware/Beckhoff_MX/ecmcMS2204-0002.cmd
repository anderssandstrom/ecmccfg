epicsEnvSet("ECMC_EC_HWTYPE",        "MS2204-0002")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4dedf0b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"

#SM2: PhysAddr 0x1100, DefaultSize    2, ControlRegister 0x24, Enable 1
#  RxPDO 0x1600 "EFU RxPDO-Map Outputs"
#    PDO entry 0x7000:01,  1 bit, "Enable"
#    PDO entry 0x7000:02,  1 bit, "Control Via Process Data"
#    PDO entry 0x7000:03,  1 bit, "Reset"
#    PDO entry 0x0000:00, 13 bit, "Gap"
#SM3: PhysAddr 0x1200, DefaultSize   20, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "EFU TxPDO-Map Inputs"
#    PDO entry 0x6000:01,  1 bit, "Warning"
#    PDO entry 0x6000:02,  1 bit, "Error"
#    PDO entry 0x6000:03,  1 bit, "Tripped"
#    PDO entry 0x6000:04,  1 bit, "Enabled"
#    PDO entry 0x0000:00, 10 bit, "Gap"
#    PDO entry 0x6000:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x0000:00, 16 bit, "Gap"
#    PDO entry 0x6000:12, 32 bit, "Current"
#  TxPDO 0x1a10 "PWI TxPDO-Map Inputs"
#    PDO entry 0x6010:01,  1 bit, "Warning"
#    PDO entry 0x0000:00, 31 bit, "Gap"
#    PDO entry 0x6010:12, 32 bit, "Voltage"
#    PDO entry 0x6010:13, 32 bit, "Current"


#- EFU Output Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x01,B1,control1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x02,B1,control2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x03,B1,control3)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,U8,dummyStub1,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,B4,dummyStub2,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,B1,dummyStub3,0)"

#- EFU Inputs Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,B1,status1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x02,B1,status2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x03,B1,status3)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x04,B1,status4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,B2,dummyStub4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U8,dummyStub5)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x0f,B2,ICC)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x0000,0x00,U16,dummyStub6)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x12,S32,EFU_current)"

#- PWI Inputs Ch.1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x01,B1,PWI_warning)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,U8,dummyStub7)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,B4,dummyStub8)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,B1,dummyStub9)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x0f,B2,PWI_cycle_counter)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,U16,dummyStub10)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x12,U32,PWI_voltage)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x13,U32,PWI_current)"
