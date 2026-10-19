#-d /**
#-d   \brief Option-driven hardware script for ELM7231-0010
#-d   \details Uses the shared ELM72XX PDO family, 1 channel(s).
#-d   \param MODE CSV (default), CSP, CST or CSTCA; MODE_1/MODE_2 override per channel
#-d   \param TP Touch-probe status PDO, default 0; supported: 1
#-d   \param INFO2 Default NONE; see hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md for capabilities
#-d   \param DIAG Actual velocity, torque and voltage PDOs, default 0
#-d   \param ENC_STAT 0 or 1; default 1
#-d   \note Channel overrides also exist for TP, INFO2, DIAG and ENC_STAT (e.g. TP_2).
#-d   \note Timing/watchdog options are documented in hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md.
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "ELM7231-0010_OPT")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x502275f9")
epicsEnvSet("ECMC_EC_COMP_TYPE"          "EL7231_OCT")

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT.cmd "PDO_FAMILY=ELM72XX,CHANNELS=1,CAP_STO=0,CAP_TP=1,CAP_ENCODER_STATUS=1,DEFAULT_TP=0,DEFAULT_INFO2=NONE,DEFAULT_DIAG=0,FOLLOWING_SUB=0x06,HALF_SHIFT=0,DEFAULT_VEL_ESLO=1,DEFAULT_VEL_EGU=RAW,DEFAULT_POS_ESLO=1,DEFAULT_POS_EGU=RAW"
