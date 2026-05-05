#==============================================================================
# setRecordUpdateRate.cmd
#- Arguments: [RATE_MS = ECMC_EC_SAMPLE_RATE_MS]

#-d /**
#-d   \brief Script for changing record update rate
#-d   \details Update record processing rate, all records created after this command will be updated in the specified rate.
#-d   \author Anders Sandström
#-d   \file
#-d   \param RATE_MS (optional) update rate in milli-seconds of any record loaded after this call, defaults to ethercat bus rate.
#-d */
ecmcEpicsEnvSetCalcTernary(BEC_MODE_EXE, "${ECMC_BEC_MODE=0}=1",,"#-")
${BEC_MODE_EXE="#-"}ecmcEpicsEnvSetCalcTernary(RATE_MS, "${RATE_MS=${ECMC_EC_SAMPLE_RATE_MS}}<100","100","${RATE_MS=${ECMC_EC_SAMPLE_RATE_MS}}")
${BEC_MODE_EXE="#-"}WARNING: ecmc runs is BEC_MODE and will not allow faster updates than 10Hz.

epicsEnvSet(ECMC_SAMPLE_RATE_MS,${RATE_MS=${ECMC_EC_SAMPLE_RATE_MS}})
