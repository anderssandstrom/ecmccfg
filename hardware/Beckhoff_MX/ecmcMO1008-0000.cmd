epicsEnvSet("ECMC_EC_HWTYPE",        "MO1008-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x811fbc0b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"


#SM2: PhysAddr 0x1200, DefaultSize    2, ControlRegister 0x24, Enable 1
#  RxPDO 0x1610 "DIP TxPDO-Map Diagnosis"
#    PDO entry 0x7080:01,  1 bit, "Enable"
#    PDO entry 0x7080:02,  1 bit, "Control Via Process Data"
#    PDO entry 0x7080:03,  1 bit, "Reset"
#    PDO entry 0x0000:00, 13 bit, "Gap"
#SM3: PhysAddr 0x1900, DefaultSize   11, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "DIP TxPDO-Map Input"
#    PDO entry 0x6000:01,  1 bit, "Input"
#    PDO entry 0x6010:01,  1 bit, "Input"
#    PDO entry 0x6020:01,  1 bit, "Input"
#    PDO entry 0x6030:01,  1 bit, "Input"
#    PDO entry 0x6040:01,  1 bit, "Input"
#    PDO entry 0x6050:01,  1 bit, "Input"
#    PDO entry 0x6060:01,  1 bit, "Input"
#    PDO entry 0x6070:01,  1 bit, "Input"
#  TxPDO 0x1a01 "DIP TxPDO-Map Diagnosis"
#    PDO entry 0x6001:01,  1 bit, "Wirebreak"
#    PDO entry 0x6001:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6011:01,  1 bit, "Wirebreak"
#    PDO entry 0x6011:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6021:01,  1 bit, "Wirebreak"
#    PDO entry 0x6021:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6031:01,  1 bit, "Wirebreak"
#    PDO entry 0x6031:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6041:01,  1 bit, "Wirebreak"
#    PDO entry 0x6041:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6051:01,  1 bit, "Wirebreak"
#    PDO entry 0x6051:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6061:01,  1 bit, "Wirebreak"
#    PDO entry 0x6061:02,  1 bit, "Power Supply Missing"
#    PDO entry 0x6071:01,  1 bit, "Wirebreak"
#    PDO entry 0x6071:02,  1 bit, "Power Supply Missing"
#  TxPDO 0x1a10 "EFU TxPDO-Map Inputs"
#    PDO entry 0x6080:01,  1 bit, "Warning"
#    PDO entry 0x6080:02,  1 bit, "Error"
#    PDO entry 0x6080:03,  1 bit, "Tripped"
#    PDO entry 0x6080:04,  1 bit, "Enabled"
#    PDO entry 0x0000:00, 10 bit, "Gap"
#    PDO entry 0x6080:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x0000:00, 16 bit, "Gap"
#    PDO entry 0x6080:11, 32 bit, "Current"


#- DIP Diagnosis
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7080,0x01,U16,control1)"

#- DIP Input
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,B1,binaryInput1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6010,0x01,B1,binaryInput2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6020,0x01,B1,binaryInput3)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6030,0x01,B1,binaryInput4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6040,0x01,B1,binaryInput5)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6050,0x01,B1,binaryInput6)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6060,0x01,B1,binaryInput7)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6070,0x01,B1,binaryInput8)"

#- DIP Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6001,0x01,B2,status1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6011,0x01,B2,status2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6021,0x01,B2,status3)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6031,0x01,B2,status4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6041,0x01,B2,status5)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6051,0x01,B2,status6)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6061,0x01,B2,status7)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6071,0x01,B2,status8)"

#- EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x01,U16,status9)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,U16,dummyStub1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x12,S32,current)"
