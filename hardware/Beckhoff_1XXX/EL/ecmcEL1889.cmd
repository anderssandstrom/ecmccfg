#-d /**
#-d   \brief hardware script for EL1889
#-d   \details HD terminal 16ch digital input, ground switching
#-d   \author Anders Sandström
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL1889")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x07613052")

#- verify slave
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

#- binary inputs
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX1016.cmd
