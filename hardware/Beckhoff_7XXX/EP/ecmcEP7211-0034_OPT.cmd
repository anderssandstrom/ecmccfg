#-d /**
#-d   \brief Option-driven hardware script for EP7211-0034
#-d   \details Uses the shared EL72XX PDO family, 1 channel(s).
#-d   \param MODE CSV (default), CSP or CST; MODE_1/MODE_2 override per channel
#-d   \param TP Touch-probe status PDO, default 1; supported: 1
#-d   \param INFO2 Default INPUTS; see hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md for capabilities
#-d   \param DIAG Actual velocity, torque and voltage PDOs, default 1
#-d   \param ENC_STAT 0 or 1; default 1
#-d   \note Channel overrides also exist for TP, INFO2, DIAG and ENC_STAT (e.g. TP_2).
#-d   \note Timing/watchdog options are documented in hugo/content/manual/knowledgebase/hardware/EX72xx_OPT.md.
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EP7211-0034_OPT")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x1c2b4052")
epicsEnvSet("ECMC_EC_COMP_TYPE"          "EL7211_OCT")

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_OPT.cmd "PDO_FAMILY=EL72XX,CHANNELS=1,CAP_STO=1,CAP_TP=1,CAP_ENCODER_STATUS=1,DEFAULT_TP=1,DEFAULT_INFO2=INPUTS,DEFAULT_DIAG=1,FOLLOWING_SUB=0x09,HALF_SHIFT=0,DEFAULT_VEL_ESLO=2.3406E-5,DEFAULT_VEL_EGU=rad/s,DEFAULT_POS_ESLO=2.3406E-5,DEFAULT_POS_EGU=rad/s"

#- Check EtherCAT port wiring on EP boxes only.
ecmcConfigOrDie "Cfg.EcSetSlavePortWiringCheckEnable(${ECMC_EC_SLAVE_NUM},1)"
