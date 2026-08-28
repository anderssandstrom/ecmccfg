#- FSoE mapping for MO7221-9018-1114 and MO7221-9018-1124.
#- Source: TwinCAT exports for safety module 0x006b0077 (SafeMotionMDSingle).

#- SM6, RxPDO 0x17c0: FSoE connection 1 receive message.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17c0,0xe700,0x01,U8,fsoe_cmd_out_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17c0,0xf701,0x01,U8,fsoe_data_out_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17c0,0xe700,0x03,U16,fsoe_crc_out_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17c0,0xe700,0x02,U16,fsoe_conn_id_out_01)"

#- SM6, RxPDO 0x17f0: two standard-output bits plus six padding bits,
#- registered as one packed byte.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17f0,0xf706,0x01,U8,std_vars_out_01)"

#- SM6, mandatory RxPDO 0x17ff: FSLOGIC output gap.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,6,0x17ff,0x0000,0x00,U16,fsoe_logic_out_01,0)"

#- SM7, TxPDO 0x1bc0: FSoE connection 1 send message.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bc0,0xe600,0x01,U8,fsoe_cmd_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bc0,0xf601,0x01,U8,fsoe_data_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bc0,0xe600,0x03,U16,fsoe_crc_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bc0,0xe600,0x02,U16,fsoe_conn_id_in_01)"

#- SM7, TxPDO 0x1bf0: standard input data.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bf0,0xf606,0x01,U8,std_vars_in_01)"

#- SM7, mandatory TxPDO 0x1bff: FSLOGIC status.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bff,0xf100,0x01,U8,fsoe_state_in_01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,7,0x1bff,0xf100,0x02,U8,fsoe_cycle_counter_in_01)"
