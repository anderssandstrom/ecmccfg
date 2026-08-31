#- Link one FSoE master connection to one FSoE slave connection using cyclic
#- EtherCAT entry copies. Run after both slaves and all entries are configured,
#- but before Cfg.SetAppMode(1).
#-
#- Required macros:
#-   SFTY_MASTER_SID  EtherCAT position of the FSoE master
#-   SFTY_SLAVE_SID   EtherCAT position of the FSoE slave
#-
#- Optional macros:
#-   SFTY_MASTER_CONN  FSoE connection on the master (default 01)
#-   SFTY_SLAVE_CONN   FSoE connection on the slave (default 01)

#- Publish the remote endpoint for hardware-panel navigation. One safety master
#- per EtherCAT master is assumed by the compact metadata PV name.
dbLoadRecords("ecmcFSoELink.template","P=${ECMC_PREFIX},MASTER_ID=${ECMC_EC_MASTER_ID=0},MASTER_CONN=${SFTY_MASTER_CONN=01},SLAVE_SID=${SFTY_SLAVE_SID},SLAVE_CONN=${SFTY_SLAVE_CONN=01}")

#- FSoE slave -> FSoE master.
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_cmd_out_${SFTY_MASTER_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_cmd_in_${SFTY_SLAVE_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_data_out_${SFTY_MASTER_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_data_in_${SFTY_SLAVE_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_crc_out_${SFTY_MASTER_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_crc_in_${SFTY_SLAVE_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_conn_id_out_${SFTY_MASTER_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_conn_id_in_${SFTY_SLAVE_CONN=01})"

#- FSoE master -> FSoE slave.
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_cmd_out_${SFTY_SLAVE_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_cmd_in_${SFTY_MASTER_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_data_out_${SFTY_SLAVE_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_data_in_${SFTY_MASTER_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_crc_out_${SFTY_SLAVE_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_crc_in_${SFTY_MASTER_CONN=01})"
ecmcConfigOrDie "Cfg.EcAddEntryCyclicWrite(ec${ECMC_EC_MASTER_ID=0}.s${SFTY_SLAVE_SID}.fsoe_conn_id_out_${SFTY_SLAVE_CONN=01},ec${ECMC_EC_MASTER_ID=0}.s${SFTY_MASTER_SID}.fsoe_conn_id_in_${SFTY_MASTER_CONN=01})"
