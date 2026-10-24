#-d /**
#-d   \brief Option-driven hardware script for EL7201-0010
#-d   \details Uses the shared EL72XX PDO family, 1 channel(s).
#-d   \param MODE CSV (default), CSP, CST or CSTCA; MODE_1/MODE_2 override per channel
#-d   \param TP Touch-probe status PDO, default 1; supported: 1
#-d   \param INFO2 Default ERRORS; see hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md for capabilities
#-d   \param DIAG Actual velocity, torque and voltage PDOs, default 1
#-d   \param ENC_STAT 0 or 1; default 1
#-d   \note Channel overrides also exist for TP, INFO2, DIAG and ENC_STAT (e.g. TP_2).
#-d   \note Timing/watchdog options are documented in hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md.
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL7201-0010_OPT")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x1c213052")
epicsEnvSet("ECMC_EC_COMP_TYPE"          "EL7201_OCT")

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT.cmd "PDO_FAMILY=EL72XX,CHANNELS=1,CAP_STO=0,CAP_TP=1,CAP_ENCODER_STATUS=1,DEFAULT_TP=1,DEFAULT_INFO2=ERRORS,DEFAULT_DIAG=1,FOLLOWING_SUB=0x06,HALF_SHIFT=0,DEFAULT_VEL_ESLO=2.3406E-5,DEFAULT_VEL_EGU=rad/s,DEFAULT_POS_ESLO=2.3406E-5,DEFAULT_POS_EGU=rad/s"
