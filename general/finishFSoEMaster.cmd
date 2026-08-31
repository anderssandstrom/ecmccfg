#- Finish the PDO mapping of a safety master after all addFSoEConn.cmd calls.
#- Required macro: SFTY_MASTER_SID
#- Optional macros: SFTY_MASTER_VENDOR_ID, SFTY_MASTER_PRODUCT_ID

#- Standard outputs: two bits plus six padding bits, registered as one byte.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,0x17f0,0xf788,0x00,U8,std_vars_out_01)"
ecmcConfigOrDie "Cfg.EcAddDataDT(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.std_vars_out_01,0,0,1,B1,binaryOutput01)"
ecmcConfigOrDie "Cfg.EcAddEntryAlias(${SFTY_MASTER_SID},binaryOutput01,BO01)"
ecmcConfigOrDie "Cfg.EcAddDataDT(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.std_vars_out_01,0,1,1,B1,binaryOutput02)"
ecmcConfigOrDie "Cfg.EcAddEntryAlias(${SFTY_MASTER_SID},binaryOutput02,BO02)"

#- Mandatory FSLOGIC output gap.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,0x17ff,0x0000,0x00,U16,dummyStub1,0)"

#- EFUSE status: four status bits, 12-bit gap, then 32-bit current.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,0x1bfe,0x6040,0x01,U16,status1)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,0x1bfe,0x6040,0x12,S32,current)"

#- FSoE device status.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,0x1bff,0xf100,0x01,U8,fsoe_state_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,0x1bff,0xf100,0x02,U8,fsoe_cycle_counter_in_01)"
