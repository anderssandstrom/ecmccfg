#-d /**
#-d   \brief Option-driven EL7411 BLDC drive; legacy configs remain unchanged.
#-d   \param MODE CSV (default), CSP, CST or CSTCA; MODE_1 overrides MODE.
#-d   \param TP Touch-probe status, default 0; 0 or 1.
#-d   \param INFO2 NONE (default), INPUTS or TEMP.
#-d   \param DIAG Velocity, torque and voltage diagnostics, default 0.
#-d   \param ENC_STAT Must remain 0; EL7411 has no EL72xx status PDO.
#-d   \note CSTCA maps target torque and commutation angle (electrical degrees).
#-d   \note See hugo/content/manual/knowledgebase/hardware/EL7411_OPT.md.
#-d */
epicsEnvSet(ECMC_EC_HWTYPE,EL7411_OPT)
epicsEnvSet(ECMC_EC_VENDOR_ID,0x2)
epicsEnvSet(ECMC_EC_PRODUCT_ID,0x1cf33052)
epicsEnvSet(ECMC_EC_COMP_TYPE,EL7411)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT.cmd "PDO_FAMILY=EL7411,CHANNELS=1,CAP_CSTCA=1,CAP_STO=1,CAP_TP=1,CAP_ENCODER_STATUS=0,DEFAULT_TP=0,DEFAULT_INFO2=NONE,DEFAULT_DIAG=0,FOLLOWING_SUB=0x06,DEFAULT_VEL_ESLO=1,DEFAULT_VEL_EGU=RAW,DEFAULT_POS_ESLO=1,DEFAULT_POS_EGU=RAW,INFO2_SDO_SIZE=1,INPUTS_SUBST=ecmcEL7411_OPT_inputs.substitutions"
