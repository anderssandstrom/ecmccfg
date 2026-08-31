# WARNING: UNTESTED
epicsEnvSet("ECMC_EC_HWTYPE",        "MO1918-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8127bb8b")
epicsEnvSet("ECMC_HW_PANEL",         "MO1918-0000")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"


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


#- FSoE connections are project-dependent and are added after addSlave.cmd with
#- general/addFSoEConn.cmd.

#- Standard outputs: two bits plus six padding bits, registered as one byte.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x17f0,0xf788,0x00,U8,std_vars_out_01)"
ecmcConfigOrDie "Cfg.EcAddDataDT(ec${ECMC_EC_MASTER_ID=0}.s${ECMC_EC_SLAVE_NUM}.std_vars_out_01,0,0,1,B1,binaryOutput01)"
ecmcConfigOrDie "Cfg.EcAddEntryAlias(${ECMC_EC_SLAVE_NUM},binaryOutput01,BO01)"
ecmcConfigOrDie "Cfg.EcAddDataDT(ec${ECMC_EC_MASTER_ID=0}.s${ECMC_EC_SLAVE_NUM}.std_vars_out_01,0,1,1,B1,binaryOutput02)"
ecmcConfigOrDie "Cfg.EcAddEntryAlias(${ECMC_EC_SLAVE_NUM},binaryOutput02,BO02)"

#- Mandatory FSLOGIC output gap.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x17ff,0x0000,0x00,U16,dummyStub1,0)"


#- EFUSE Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bfe,0x6040,0x01,U16,status1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bfe,0x6040,0x11,S32,current)"

#- FSoE Device Status: SafeLogicState and CycleCounter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bff,0xf100,0x01,U8,fsoe_state_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bff,0xf100,0x02,U8,fsoe_cycle_counter_in_01)"
