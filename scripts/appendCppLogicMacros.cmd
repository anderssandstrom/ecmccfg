#==============================================================================
# appendCppLogicMacros.cmd
#- Arguments: MACROS, [LOGIC_ID], [REPORT]

#-d /**
#-d   \brief Append additional MACROS text to an already loaded C++ logic instance.
#-d   \details This is useful when the full MACROS string would otherwise exceed
#-d            IOC shell line-length limits. The text is appended to the existing
#-d            C++ logic MACROS string with a separating comma.
#-d   \author Anders Sandström, OpenAI Codex
#-d   \file
#-d   \param MACROS   Extra free-form text to append.
#-d   \param LOGIC_ID Optional C++ logic instance index. Defaults to the current
#-d                  `ECMC_CPP_LOGIC_ID`, which is set by `loadCppLogic.cmd`.
#-d   \param REPORT   Print a report after append if >0, default 0.
#-d */

epicsEnvSet("ECMC_CPP_LOGIC_ID", "${LOGIC_ID=${ECMC_CPP_LOGIC_ID=0}}")
ecmcConfigOrDie "Cfg.AppendCppLogicMacros(${ECMC_CPP_LOGIC_ID})=${MACROS=''}"

ecmcEpicsEnvSetCalcTernary("ECMC_CPP_LOGIC_REPORT", "${REPORT=0}>0", "", "#")
${ECMC_CPP_LOGIC_REPORT}ecmcConfigOrDie "Cfg.ReportCppLogic(${ECMC_CPP_LOGIC_ID})"
epicsEnvUnset(ECMC_CPP_LOGIC_REPORT)
