#- TESTED
epicsEnvSet("ECMC_EC_HWTYPE",        "MO7062-0100")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0x8154f18b")
epicsEnvSet("ECMC_EC_COMP_TYPE"      "EL7062")
#- verify slave
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

#- Load standard cfg
ecmcFileExist(${ecmccfg_DIR}ecmcEX7062.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062.cmd
