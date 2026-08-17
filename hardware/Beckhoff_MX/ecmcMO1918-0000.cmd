# WARNING: UNTESTED
epicsEnvSet("ECMC_EC_HWTYPE",        "MO1918-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8127bb8b")

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


#- RxPDO Mapping Connection 01
# FSoE: Command, Data, CRC, ConnectionID
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7050,0x01,U8,fsoe_cmd_out_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7002,0x01,B1,fsoe_err_ack_mod1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7012,0x01,B1,fsoe_err_ack_mod2)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7022,0x01,B1,fsoe_err_ack_mod3)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7032,0x01,B1,fsoe_err_ack_mod4)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7040,0x01,B1,fsoe_err_reset_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7050,0x03,U16,fsoe_crc_out_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7050,0x02,U16,fsoe_conn_id_out_01)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x17ff,0x0000,0x00,U16,dummyStub1)"


#- TxPDO Mapping Connection 01
# FSoE: Command, Data, CRC, ConnectionID
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6050,0x01,U8,fsoe_cmd_in_01)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6001,0x01,B1,fsoe_input01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6001,0x02,B1,fsoe_input02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6002,0x01,B1,fsoe_fault_mod01)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6011,0x01,B1,fsoe_input03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6011,0x02,B1,fsoe_input04)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6012,0x01,B1,fsoe_fault_mod02)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6021,0x01,B1,fsoe_input05)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6021,0x02,B1,fsoe_input06)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6022,0x01,B1,fsoe_fault_mod03)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6031,0x01,B1,fsoe_input07)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6031,0x02,B1,fsoe_input08)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6032,0x01,B1,fsoe_fault_mod04)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6040,0x01,B4,fsoe_status_01)"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6050,0x03,U16,fsoe_crc_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa0,0x6050,0x02,U16,fsoe_conn_id_in_01)"


#- EFUSE Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bfe,0x6040,0x01,U16,status1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bfe,0x6040,0x11,S32,current)"

#- FSoE Device Status: SafeLogicState and CycleCounter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bff,0xf100,0x01,U8,fsoe_state_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1bff,0xf100,0x02,U8,fsoe_cycle_counter_in_01)"
