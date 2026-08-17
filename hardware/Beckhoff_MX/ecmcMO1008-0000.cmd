#- TESTED
epicsEnvSet("ECMC_EC_HWTYPE",        "MO1008-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x811fbc0b")
epicsEnvSet("ECMC_SUBST_TYPE",       "MO1008-0000")
epicsEnvSet("ECMC_HW_PANEL",         "MO1008-0000")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"


#SM2: PhysAddr 0x1200, DefaultSize    2, ControlRegister 0x24, Enable 1
#  RxPDO 0x1610 "BI TxPDO-Map Diagnosis"
#    PDO entry 0x7080:01,  1 bit, "Enable"
#    PDO entry 0x7080:02,  1 bit, "Control Via Process Data"
#    PDO entry 0x7080:03,  1 bit, "Reset"
#    PDO entry 0x0000:00, 13 bit, "Gap"
#SM3: PhysAddr 0x1900, DefaultSize   11, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "BI TxPDO-Map Input"
#    PDO entry 0x6000:01,  1 bit, "Input"
#    PDO entry 0x6010:01,  1 bit, "Input"
#    PDO entry 0x6020:01,  1 bit, "Input"
#    PDO entry 0x6030:01,  1 bit, "Input"
#    PDO entry 0x6040:01,  1 bit, "Input"
#    PDO entry 0x6050:01,  1 bit, "Input"
#    PDO entry 0x6060:01,  1 bit, "Input"
#    PDO entry 0x6070:01,  1 bit, "Input"
#  TxPDO 0x1a01 "BI TxPDO-Map Diagnosis"
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


#- BI Diagnosis
#ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7080,0x01,U16,control1)"

#- BI Input
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,U8,BI_Arr)"
#- BI_Arr B0..B7=Input Ch1..Ch8

#- BI Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6001,0x01,U16,BI_Stat)"
#- BI_Stat B0..B1=Ch1: Wirebreak, Power Supply Missing
#- BI_Stat B2..B3=Ch2: Wirebreak, Power Supply Missing
#- BI_Stat B4..B5=Ch3: Wirebreak, Power Supply Missing
#- BI_Stat B6..B7=Ch4: Wirebreak, Power Supply Missing
#- BI_Stat B8..B9=Ch5: Wirebreak, Power Supply Missing
#- BI_Stat B10..B11=Ch6: Wirebreak, Power Supply Missing
#- BI_Stat B12..B13=Ch7: Wirebreak, Power Supply Missing
#- BI_Stat B14..B15=Ch8: Wirebreak, Power Supply Missing

#- EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x01,U16,EFU_Stat)"
#- EFU_Stat B0=Warning, B1=Error, B2=Tripped, B3=Enabled
#- EFU_Stat B4..B13=gap, B14..B15=Input Cycle Counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x0000,0x00,U16,EFU_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x12,F32,EFU_Curr)"
