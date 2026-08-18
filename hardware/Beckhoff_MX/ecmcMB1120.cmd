# WARNING: UNTESTED
#- ecmc hardware config for: MB1120 backplane junction
#- Source ESI: Beckhoff MBxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MB1120")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x046008d2")
epicsEnvSet("ECMC_EC_REVISION",      "0x00020000")

#- Verify slave identity without attempting an SDO reset; the ESI has no mailbox.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- Passive junction: no PDOs, sync managers, mailbox, watchdog, or DC mode.
ecmcConfigOrDie "Cfg.EcAddSlave(0,${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID})"
