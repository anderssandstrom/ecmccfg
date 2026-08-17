#- TESTED
#- ecmc hardware config for: MO2338-0000-1111 | 8-channel digital combi, 24 V DC/0.5 A, M8
#- source ESI file: Beckhoff MOxxxx.xml

epicsEnvSet("ECMC_EC_HWTYPE"             "MO2338-0000-1111")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x812b6c8b")
epicsEnvSet("ECMC_EC_REVISION"           "0x1000457")
epicsEnvSet("ECMC_SUBST_TYPE"             "MO2338-0000-common")
epicsEnvSet("ECMC_HW_PANEL"              "MO2338-0000-common")

ecmcFileExist(${ecmccfg_DIR}ecmcMO2338-0000-common.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO2338-0000-common.cmd
