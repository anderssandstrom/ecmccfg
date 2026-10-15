#-d /**
#-d   \brief Option-driven two-channel ED7062; legacy descriptor is unchanged.
#-d   \details See hugo/content/manual/knowledgebase/hardware/EX7062_OPT.md.
#-d   \param MODE CSV (default), CSP or CST; MO currently supports CSV only.
#-d   \param TP, INPUTS, ENC2 0/1, default 1; suffix _1/_2 overrides a channel.
#-d   \param DIAG Shared voltage/temperature, default 1.
#-d   \param EXT_DIAG Actual velocity/torque and CSP following error, default 0.
#-d   \param TP_DC Touch-probe 1 timestamps, default 0; requires TP=1.
#-d   \param AUTOTUNE Load tuning records, default 1.
#-d */
epicsEnvSet(ECMC_EC_HWTYPE,ED7062_OPT)
epicsEnvSet(ECMC_EC_VENDOR_ID,0x2)
epicsEnvSet(ECMC_EC_PRODUCT_ID,0x1b961052)
epicsEnvSet(ECMC_EC_COMP_TYPE,EL7062)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX7062_OPT.cmd "CAP_TP_DC=1,FIXED_PDOS=0"
