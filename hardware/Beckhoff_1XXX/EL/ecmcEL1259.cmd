#-d /**
#-d   \brief hardware script for EL1259
#-d   \author Anders Sandstroem
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL1259")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x04eb3052")

#- verify slave
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

#- MTO inputs CH 1..8
ecmcFileExist(${ecmccfg_DIR}ecmcEL1259-MTO-Inputs-chX.cmd,1)
ecmcForLoop(${ecmccfg_DIR}ecmcEL1259-MTO-Inputs-chX.cmd,"NO_MACROS=0",ECMC_LOOP_IDX,0,7,1)

ecmcFileExist(${ecmccfg_DIR}ecmcEL1259-MTI-Inputs_10x-chX.cmd,1)
ecmcForLoop(${ecmccfg_DIR}ecmcEL1259-MTI-Inputs_10x-chX.cmd,"NO_MACROS=0",ECMC_LOOP_IDX,0,7,1)

#- Cleanup
ecmcEnvUnset(ECMC_CH_ID_2_CHARS)
ecmcEnvUnset(ECMC_PDO_ID)
ecmcEnvUnset(ECMC_ENTRY_ID)
ecmcEnvUnset(ECMC_LOOP_IDX)

