# WARNING: UNTESTED
#- ecmc hardware config for: MO7221-9016-1114
#- 1-channel servo motion interface, 24 V DC/8 A, OCT, STO/SS1
#- CSV/STD configuration based on EL7221-9014_STD, with MO-specific PDO indices.
#- Source ESI: Beckhoff MOxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE"             "MO7221-9016-1114")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x815657db")
epicsEnvSet("ECMC_EC_REVISION"           "0x0102755a")
epicsEnvSet("ECMC_EC_COMP_TYPE"          "MO7221_OCT")
epicsEnvSet("ECMC_SUBST_TYPE"            "MO7221-9016-1114")
epicsEnvSet("ECMC_HW_PANEL"              "MO7221-9016")

ecmcFileExist(${ecmccfg_DIR}ecmcMO7221-9016-common.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO7221-9016-common.cmd
