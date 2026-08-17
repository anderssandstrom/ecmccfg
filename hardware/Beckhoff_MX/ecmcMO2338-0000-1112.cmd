#- ecmc hardware config for: MO2338-0000-1112 | 8-channel digital combi, 24 V DC/0.5 A, M12
#- source ESI file: Beckhoff MOxxxx.xml
#- NOTE: BO02 is pin 2 on the first M12 connector. Its LED may remain off even
#- while the output is electrically high; see the common snippet and MX-System
#- knowledge-base page for verification details.

epicsEnvSet("ECMC_EC_HWTYPE"             "MO2338-0000-1112")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x812b6c8b")
epicsEnvSet("ECMC_EC_REVISION"           "0x1000458")
#- The PDO database and panel are shared by both connector variants.
epicsEnvSet("ECMC_SUBST_TYPE"             "MO2338-0000-common")
epicsEnvSet("ECMC_HW_PANEL"              "MO2338-0000-common")

ecmcFileExist(${ecmccfg_DIR}ecmcMO2338-0000-common.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO2338-0000-common.cmd
