#===============================================================================
# master config
# Arguments
# [optional]
# MASTER_ID = 0

epicsEnvSet("ECMC_EC_MASTER_ID"          "$(MASTER_ID=0)")
#Choose master
EthercatMCConfigController "$(ECMC_MOTOR_PORT)", "Cfg.EcSetMaster($(ECMC_EC_MASTER_ID))"