#==============================================================================
# finalizeAxGrp_loopStep.cmd
#-d /**
#-d   \brief Finalize axis-group loop step for GUI generation.
#-d   \details Shows axis-group environment variables and loads records for the current loop index.
#-d   \file
#-d */
#- Load info for axis groups, mainly to allow automatic GUI generation
epicsEnvShow (ECMC_AX_GRP_ID_${ECMC_LOOP_IDX}_LIST)
epicsEnvShow (ECMC_AX_GRP_ID_${ECMC_LOOP_IDX}_NAME)
dbLoadRecords(ecmcAxisGroup_chX.db,"P=${P},NAME=${ECMC_AX_GRP_ID_${ECMC_LOOP_IDX}_NAME},AXES='${ECMC_AX_GRP_ID_${ECMC_LOOP_IDX}_LIST}',ID=${ECMC_LOOP_IDX}")
