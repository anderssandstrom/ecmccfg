#- TESTED
#- Generic ecmc hardware config for MO2338-0000-1111 and MO2338-0000-1112
#- The connector-specific wrappers should be preferred when the exact variant
#- is known. This wrapper intentionally does not constrain the ESI revision.

epicsEnvSet("ECMC_EC_HWTYPE"             "MO2338-0000")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x812b6c8b")
epicsEnvSet("ECMC_SUBST_TYPE"             "MO2338-0000-common")
epicsEnvSet("ECMC_HW_PANEL"              "MO2338-0000-common")

ecmcFileExist(${ecmccfg_DIR}ecmcMO2338-0000-common.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO2338-0000-common.cmd
