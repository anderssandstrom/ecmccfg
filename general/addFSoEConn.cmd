#- Add one directly mapped six-byte FSoE connection to a safety master.
#- Run after addSlave.cmd for the safety master and before Cfg.SetAppMode(1).
#-
#- Required macros:
#-   SFTY_MASTER_SID   EtherCAT position of the safety master
#-   SFTY_MASTER_CONN  Connection number, formatted as two hex digits (01, 02)
#-
#- Optional macros:
#-   SFTY_MASTER_VENDOR_ID    Vendor ID (default Beckhoff)
#-   SFTY_MASTER_PRODUCT_ID   Product ID (default MO1918-0000)
#-   SFTY_MASTER_RX_PDO       Master-output PDO index (default 0x1600)
#-   SFTY_MASTER_TX_PDO       Master-input PDO index (default 0x1a00)
#-   SFTY_MASTER_RX_INDEX     Master-output entry index (default 0x6000)
#-   SFTY_MASTER_TX_INDEX     Master-input entry index (default 0x7000)

#- Master outputs: command, one safe-data byte, CRC and connection ID.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=0x1600},${SFTY_MASTER_RX_INDEX=0x6000},0x${SFTY_MASTER_CONN},U8,fsoe_cmd_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=0x1600},${SFTY_MASTER_RX_INDEX=0x6000},0x${SFTY_MASTER_CONN},U8,fsoe_data_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=0x1600},${SFTY_MASTER_RX_INDEX=0x6000},0x${SFTY_MASTER_CONN},U16,fsoe_crc_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=0x1600},${SFTY_MASTER_RX_INDEX=0x6000},0x${SFTY_MASTER_CONN},U16,fsoe_conn_id_out_${SFTY_MASTER_CONN})"

#- Master inputs: command, one safe-data byte, CRC and connection ID.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=0x1a00},${SFTY_MASTER_TX_INDEX=0x7000},0x${SFTY_MASTER_CONN},U8,fsoe_cmd_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=0x1a00},${SFTY_MASTER_TX_INDEX=0x7000},0x${SFTY_MASTER_CONN},U8,fsoe_data_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=0x1a00},${SFTY_MASTER_TX_INDEX=0x7000},0x${SFTY_MASTER_CONN},U16,fsoe_crc_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=0x1a00},${SFTY_MASTER_TX_INDEX=0x7000},0x${SFTY_MASTER_CONN},U16,fsoe_conn_id_in_${SFTY_MASTER_CONN})"

#- Load records for this connection.
dbLoadTemplate("ecmcFSoEMasterConnection.substitutions","P=${ECMC_PREFIX},ECMC_P=${ECMC_P},ECMC_G=${ECMC_G=},PORT=${ECMC_ASYN_PORT},ADDR=0,TIMEOUT=1,MASTER_ID=${ECMC_EC_MASTER_ID=0},SLAVE_POS=${SFTY_MASTER_SID},HWTYPE=FSoEMaster,T_SMP_MS=${ECMC_SAMPLE_RATE_MS},TSE=${ECMC_TSE},CH_ID=${SFTY_MASTER_CONN}")
