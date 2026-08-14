epicsEnvSet("ECMC_EC_HWTYPE",        "MS6020-1100")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa500691b")

#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=1"

ecmcConfigOrDie "Cfg.EcAddSlave(0,${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID})"
