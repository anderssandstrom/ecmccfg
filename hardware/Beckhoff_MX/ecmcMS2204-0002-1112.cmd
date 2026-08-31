#- TESTED
#- ecmc hardware config for: MS2204-0002-1112
#- System module, EtherCAT power infeed + forwarding
#- Product code: 0xa4dedf0b, revision: 0x03005278

#- Reuse the generic MS2204-0002 PDO configuration and database records.
ecmcFileExist(${ecmccfg_DIR}ecmcMS2204-0002.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMS2204-0002.cmd

#- Restore the exact variant identity overwritten by the generic config.
epicsEnvSet("ECMC_EC_HWTYPE"             "MS2204-0002-1112")
epicsEnvSet("ECMC_EC_REVISION"           "0x03005278")
epicsEnvSet("ECMC_SUBST_TYPE"             "MS2204-0002")
epicsEnvSet("ECMC_HW_PANEL"               "MS2204-0002-1112")
