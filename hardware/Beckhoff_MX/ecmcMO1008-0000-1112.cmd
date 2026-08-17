#- TESTED
#- ecmc hardware config for: MO1008-0000-1112 | 8-channel digital input, 24 V DC, M12
#- source ESI file: Beckhoff MOxxxx.xml
#- product code: 0x811fbc0b, revision: 0x02000458

#- Reuse the generic MO1008 PDO configuration and database records.
ecmcFileExist(${ecmccfg_DIR}ecmcMO1008-0000.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO1008-0000.cmd

#- Restore the exact variant identity overwritten by the generic config.
epicsEnvSet("ECMC_EC_HWTYPE"             "MO1008-0000-1112")
epicsEnvSet("ECMC_EC_REVISION"           "0x2000458")
epicsEnvSet("ECMC_SUBST_TYPE"             "MO1008-0000")
epicsEnvSet("ECMC_HW_PANEL"               "MO1008-0000")
