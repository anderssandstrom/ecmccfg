# WARNING: UNTESTED
#- ecmc hardware config for: MS1110-0000
#- System module, EtherCAT extension
#- Source ESI: Beckhoff MSxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MS1110-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x04564cd2")
epicsEnvSet("ECMC_EC_REVISION",      "0x00010000")

#- Verify slave identity without attempting an SDO reset; the ESI has no mailbox.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- Passive EtherCAT extension: no PDOs, sync managers, mailbox, watchdog, or DC.
ecmcConfigOrDie "Cfg.EcAddSlave(0,${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID})"
