#- MO2008-0000-1111 connector variant; shares the generic PDO mapping.
ecmcFileExist(${ecmccfg_DIR}ecmcMO2008-0000.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO2008-0000.cmd

#- Keep the selected connector identity and the generic database/panel.
epicsEnvSet("ECMC_EC_HWTYPE", "MO2008-0000-1111")
