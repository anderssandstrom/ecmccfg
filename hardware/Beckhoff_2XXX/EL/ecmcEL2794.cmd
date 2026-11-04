#-d /**
#-d   \brief hardware script for EL2794
#-d   \details 4-channel solid state relay output, 30 V AC/48 V DC, 2 A, potential-free
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL2794")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x0aea3052")

#- verify slave
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX2004.cmd
