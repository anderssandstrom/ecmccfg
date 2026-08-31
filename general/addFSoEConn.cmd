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
#-   SFTY_MASTER_RX_PDO        Master-output PDO index
#-   SFTY_MASTER_TX_PDO        Master-input PDO index
#-   SFTY_MASTER_RX_CMD_INDEX  Master-output command/CRC/ConnID index
#-   SFTY_MASTER_RX_DATA_INDEX Master-output safe-data index
#-   SFTY_MASTER_TX_CMD_INDEX  Master-input command/CRC/ConnID index
#-   SFTY_MASTER_TX_DATA_INDEX Master-input safe-data index
#- Defaults are calculated from SFTY_MASTER_CONN for the MO1918 PDO layout.

ecmcEpicsEnvSetCalc("ECMC_FSOE_RX_PDO",5632+${SFTY_MASTER_CONN}-1,"0x%04x")
ecmcEpicsEnvSetCalc("ECMC_FSOE_TX_PDO",6656+${SFTY_MASTER_CONN}-1,"0x%04x")
ecmcEpicsEnvSetCalc("ECMC_FSOE_RX_CMD_INDEX",28736+${SFTY_MASTER_CONN}*16,"0x%04x")
ecmcEpicsEnvSetCalc("ECMC_FSOE_RX_DATA_INDEX",28737+${SFTY_MASTER_CONN}*16,"0x%04x")
ecmcEpicsEnvSetCalc("ECMC_FSOE_TX_CMD_INDEX",24640+${SFTY_MASTER_CONN}*16,"0x%04x")
ecmcEpicsEnvSetCalc("ECMC_FSOE_TX_DATA_INDEX",24641+${SFTY_MASTER_CONN}*16,"0x%04x")

#- Master outputs: command, one safe-data byte, CRC and connection ID.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=${ECMC_FSOE_RX_PDO}},${SFTY_MASTER_RX_CMD_INDEX=${ECMC_FSOE_RX_CMD_INDEX}},0x01,U8,fsoe_cmd_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=${ECMC_FSOE_RX_PDO}},${SFTY_MASTER_RX_DATA_INDEX=${ECMC_FSOE_RX_DATA_INDEX}},0x01,U8,fsoe_data_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=${ECMC_FSOE_RX_PDO}},${SFTY_MASTER_RX_CMD_INDEX=${ECMC_FSOE_RX_CMD_INDEX}},0x03,U16,fsoe_crc_out_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},1,2,${SFTY_MASTER_RX_PDO=${ECMC_FSOE_RX_PDO}},${SFTY_MASTER_RX_CMD_INDEX=${ECMC_FSOE_RX_CMD_INDEX}},0x02,U16,fsoe_conn_id_out_${SFTY_MASTER_CONN})"

#- Master inputs: command, one safe-data byte, CRC and connection ID.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=${ECMC_FSOE_TX_PDO}},${SFTY_MASTER_TX_CMD_INDEX=${ECMC_FSOE_TX_CMD_INDEX}},0x01,U8,fsoe_cmd_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=${ECMC_FSOE_TX_PDO}},${SFTY_MASTER_TX_DATA_INDEX=${ECMC_FSOE_TX_DATA_INDEX}},0x01,U8,fsoe_data_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=${ECMC_FSOE_TX_PDO}},${SFTY_MASTER_TX_CMD_INDEX=${ECMC_FSOE_TX_CMD_INDEX}},0x03,U16,fsoe_crc_in_${SFTY_MASTER_CONN})"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${SFTY_MASTER_SID},${SFTY_MASTER_VENDOR_ID=0x00000002},${SFTY_MASTER_PRODUCT_ID=0x8127bb8b},2,3,${SFTY_MASTER_TX_PDO=${ECMC_FSOE_TX_PDO}},${SFTY_MASTER_TX_CMD_INDEX=${ECMC_FSOE_TX_CMD_INDEX}},0x02,U16,fsoe_conn_id_in_${SFTY_MASTER_CONN})"

#- Load records for this connection.
dbLoadTemplate("ecmcFSoEMasterConnection.substitutions","P=${ECMC_PREFIX},ECMC_P=${ECMC_P},ECMC_G=${ECMC_G=},PORT=${ECMC_ASYN_PORT},ADDR=0,TIMEOUT=1,MASTER_ID=${ECMC_EC_MASTER_ID=0},SLAVE_POS=${SFTY_MASTER_SID},HWTYPE=FSoEMaster,T_SMP_MS=${ECMC_SAMPLE_RATE_MS},TSE=${ECMC_TSE},CH_ID=${SFTY_MASTER_CONN}")

epicsEnvUnset(ECMC_FSOE_RX_PDO)
epicsEnvUnset(ECMC_FSOE_TX_PDO)
epicsEnvUnset(ECMC_FSOE_RX_CMD_INDEX)
epicsEnvUnset(ECMC_FSOE_RX_DATA_INDEX)
epicsEnvUnset(ECMC_FSOE_TX_CMD_INDEX)
epicsEnvUnset(ECMC_FSOE_TX_DATA_INDEX)
