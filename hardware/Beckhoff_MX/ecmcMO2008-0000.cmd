#- Shared PDO mapping, database and panel for the -1111 and -1112 connector types.
#- Can also be selected directly with HW_DESC=MO2008-0000.
epicsEnvSet("ECMC_EC_HWTYPE",        "MO2008-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8128860b")
epicsEnvSet("ECMC_SUBST_TYPE"        "MO2008-0000")
epicsEnvSet("ECMC_HW_PANEL"          "MO2008-0000")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"


#SM2: PhysAddr 0x1200, DefaultSize    3, ControlRegister 0x24, Enable 1
#  RxPDO 0x1600 "DOS RxPDO-Map Output"
#    PDO entry 0x7000:01,  1 bit, "Output"
#    PDO entry 0x7010:01,  1 bit, "Output"
#    PDO entry 0x7020:01,  1 bit, "Output"
#    PDO entry 0x7030:01,  1 bit, "Output"
#    PDO entry 0x7040:01,  1 bit, "Output"
#    PDO entry 0x7050:01,  1 bit, "Output"
#    PDO entry 0x7060:01,  1 bit, "Output"
#    PDO entry 0x7070:01,  1 bit, "Output"
#  RxPDO 0x1680 "EFU RxPDO-Map Outputs"
#    PDO entry 0x7080:01,  1 bit, "Enable"
#    PDO entry 0x7080:02,  1 bit, "Control Via Process Data"
#    PDO entry 0x7080:03,  1 bit, "Reset"
#    PDO entry 0x0000:00, 13 bit, "Gap"
#SM3: PhysAddr 0x1900, DefaultSize   13, ControlRegister 0x20, Enable 1
#  TxPDO 0x1a00 "DOS TxPDO-Map Diagnosis"
#    PDO entry 0x6000:01..05, 5 bit, "Ch1 Diag"
#    PDO entry 0x6010:01..05, 5 bit, "Ch2 Diag"
#    PDO entry 0x6020:01..05, 5 bit, "Ch3 Diag"
#    PDO entry 0x6030:01..05, 5 bit, "Ch4 Diag"
#    PDO entry 0x6040:01..05, 5 bit, "Ch5 Diag"
#    PDO entry 0x6050:01..05, 5 bit, "Ch6 Diag"
#    PDO entry 0x6060:01..05, 5 bit, "Ch7 Diag"
#    PDO entry 0x6070:01..05, 5 bit, "Ch8 Diag"
#  TxPDO 0x1a80 "EFU TxPDO-Map Inputs"
#    PDO entry 0x6080:01,  1 bit, "Warning"
#    PDO entry 0x6080:02,  1 bit, "Error"
#    PDO entry 0x6080:03,  1 bit, "Tripped"
#    PDO entry 0x6080:04,  1 bit, "Enabled"
#    PDO entry 0x0000:00, 10 bit, "Gap"
#    PDO entry 0x6080:0f,  2 bit, "Input cycle counter"
#    PDO entry 0x0000:00, 16 bit, "Gap"
#    PDO entry 0x6080:11, 32 bit, "Current"

#- DOS Output
#- RX PDO 0x1600: BO Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x1,U8,BO_Arr)"
#- BO_Arr B0..B7=Output

#- RX PDO 0x1680: EFU Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1680,0x7080,0x1,U16,EFU_Ctrl)"
#- EFU_Ctrl B0=Enable
#- EFU_Ctrl B1=Control via Process Data
#- EFU_Ctrl B2=Reset
#- EFU_Ctrl B3..B15=gap

#- TX PDO 0x1a10: BO Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x1,U16,BO_Stat01)"
#- BO_Stat01 B0=Ch1 Overcurrent
#- BO_Stat01 B1=Ch1 Overload
#- BO_Stat01 B2=Ch1 gap
#- BO_Stat01 B3=Ch1 Short to 24V
#- BO_Stat01 B4=Ch1 Power Supply Missing
#- BO_Stat01 B5=Ch2 Overcurrent
#- BO_Stat01 B6=Ch2 Overload
#- BO_Stat01 B7=Ch2 gap
#- BO_Stat01 B8=Ch2 Short to 24V
#- BO_Stat01 B9=Ch2 Power Supply Missing
#- BO_Stat01 B10=Ch3 Overcurrent
#- BO_Stat01 B11=Ch3 Overload
#- BO_Stat01 B12=Ch3 gap
#- BO_Stat01 B13=Ch3 Short to 24V
#- BO_Stat01 B14=Ch3 Power Supply Missing
#- BO_Stat01 B15=Ch4 Overcurrent
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6030,0x2,U16,BO_Stat02)"
#- BO_Stat02 B0=Ch4 Overload
#- BO_Stat02 B1=Ch4 gap
#- BO_Stat02 B2=Ch4 Short to 24V
#- BO_Stat02 B3=Ch4 Power Supply Missing
#- BO_Stat02 B4=Ch5 Overcurrent
#- BO_Stat02 B5=Ch5 Overload
#- BO_Stat02 B6=Ch5 gap
#- BO_Stat02 B7=Ch5 Short to 24V
#- BO_Stat02 B8=Ch5 Power Supply Missing
#- BO_Stat02 B9=Ch6 Overcurrent
#- BO_Stat02 B10=Ch6 Overload
#- BO_Stat02 B11=Ch6 gap
#- BO_Stat02 B12=Ch6 Short to 24V
#- BO_Stat02 B13=Ch6 Power Supply Missing
#- BO_Stat02 B14=Ch7 Overcurrent
#- BO_Stat02 B15=Ch7 Overload
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6060,0x4,U8,BO_Stat03)"
#- BO_Stat03 B0=Ch7 gap
#- BO_Stat03 B1=Ch7 Short to 24V
#- BO_Stat03 B2=Ch7 Power Supply Missing
#- BO_Stat03 B3=Ch8 Overcurrent
#- BO_Stat03 B4=Ch8 Overload
#- BO_Stat03 B5=Ch8 gap
#- BO_Stat03 B6=Ch8 Short to 24V
#- BO_Stat03 B7=Ch8 Power Supply Missing

#- TX PDO 0x1a80: EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6080,0x1,U16,EFU_Stat)"
#- EFU_Stat B0=Warning
#- EFU_Stat B1=Error
#- EFU_Stat B2=Tripped
#- EFU_Stat B3=Enabled
#- EFU_Stat B4..B13=gap
#- EFU_Stat B14..B15=Input Cycle Counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x0000,0x00,U16,EFU_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6080,0x12,F32,EFU_Curr)"

#- DC mode: Synchron (FreeRun/SM-Synchron)
ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x0,SYNC_0_CYCLE=0,SYNC_0_SHIFT=0,SYNC_1_CYCLE=0,SYNC_1_SHIFT=0"
