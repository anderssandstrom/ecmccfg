#- MO1008-0000-1111 connector variant; shares the generic PDO mapping.
#- Validation on hardware is pending, as for the generic configuration.
ecmcFileExist(${ecmccfg_DIR}ecmcMO1008-0000.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO1008-0000.cmd

#- Keep the selected connector identity and the generic database/panel.
epicsEnvSet("ECMC_EC_HWTYPE", "MO1008-0000-1111")
