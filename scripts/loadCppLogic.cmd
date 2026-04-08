#==============================================================================
# loadCppLogic.cmd
#- Arguments: [FILE], [LOGIC_ID], [ASYN_PORT], [SAMPLE_RATE_MS], [UPDATE_RATE_MS], [APP_PANEL], [LOAD_DEFAULT_PVS], [LOAD_APP_PVS], [EPICS_SUBST], [DB_PREFIX], [DB_MACROS], [REPORT]

#-d /**
#-d   \brief Script for loading a native C/C++ logic shared library in ecmc.
#-d   \details Loads one C++ logic instance, then optionally loads the
#-d            built-in core substitutions and one custom substitutions file
#-d            for the user-defined `epics.*` exports.
#-d   \author Anders Sandström, OpenAI Codex
#-d   \file
#-d   \param FILE      Shared library implementing ecmc_cpp_logic_get_api(),
#-d                  default `bin/libmain.so`.
#-d   \param LOGIC_ID  C++ logic instance index, default 0. Incremented for
#-d                  the next call after a successful load.
#-d   \param ASYN_PORT Optional dedicated asyn port, default CPP.LOGIC<LOGIC_ID>.
#-d   \param SAMPLE_RATE_MS Optional execution rate in milliseconds.
#-d   \param UPDATE_RATE_MS Optional EPICS/asyn publish rate in milliseconds.
#-d   \param APP_PANEL Optional IOC-local application panel path shown in the
#-d                  generic panel, default `qt/${IOC}_cpp_logic.ui`.
#-d   \param LOAD_DEFAULT_PVS Load built-in control/status PVs, default 1.
#-d   \param LOAD_APP_PVS Load custom EPICS substitutions for `epics.*` exports, default 0.
#-d   \param EPICS_SUBST Optional custom substitutions file, default ${FILE}.substitutions.
#-d   \param DB_PREFIX Optional record prefix, default ${IOC}:.
#-d   \param DB_MACROS Optional extra dbLoadTemplate macros.
#-d   \param REPORT    Print loaded C++ logic report if >0, default 1.
#-d */

epicsEnvSet("ECMC_CPP_LOGIC_ID", "${LOGIC_ID=0}")
epicsEnvSet("ECMC_CPP_LOGIC_FILE", "${FILE=bin/libmain.so}")

ecmcIf("'${ASYN_PORT=EMPTY}'='EMPTY'",ECMC_CPP_LOGIC_PORT_EMPTY_TRUE,ECMC_CPP_LOGIC_PORT_EMPTY_FALSE)
${ECMC_CPP_LOGIC_PORT_EMPTY_TRUE}epicsEnvSet("ECMC_CPP_LOGIC_PORT", "CPP.LOGIC${ECMC_CPP_LOGIC_ID}")
#else
${ECMC_CPP_LOGIC_PORT_EMPTY_FALSE}epicsEnvSet("ECMC_CPP_LOGIC_PORT", "${ASYN_PORT=''}")
ecmcEndIf(ECMC_CPP_LOGIC_PORT_EMPTY_TRUE,ECMC_CPP_LOGIC_PORT_EMPTY_FALSE)

ecmcIf("'${APP_PANEL=EMPTY}'='EMPTY'",ECMC_CPP_LOGIC_PANEL_EMPTY_TRUE,ECMC_CPP_LOGIC_PANEL_EMPTY_FALSE)
${ECMC_CPP_LOGIC_PANEL_EMPTY_TRUE}epicsEnvSet("ECMC_CPP_LOGIC_APP_PANEL", "qt/${IOC}_cpp_logic.ui")
#else
${ECMC_CPP_LOGIC_PANEL_EMPTY_FALSE}epicsEnvSet("ECMC_CPP_LOGIC_APP_PANEL", "${APP_PANEL=''}")
ecmcEndIf(ECMC_CPP_LOGIC_PANEL_EMPTY_TRUE,ECMC_CPP_LOGIC_PANEL_EMPTY_FALSE)

epicsEnvSet("ECMC_CPP_LOGIC_CONFIG", "asyn_port=${ECMC_CPP_LOGIC_PORT};sample_rate_ms=${SAMPLE_RATE_MS=};update_rate_ms=${UPDATE_RATE_MS=}")
epicsEnvSet("ECMC_CPP_LOGIC_CORE_EPICS_SUBST", "ecmcCppLogicCore.substitutions")
epicsEnvSet("ECMC_CPP_LOGIC_DB_MACROS_BASE", "P=${DB_PREFIX=$(IOC):},PORT=${ECMC_CPP_LOGIC_PORT},CPP_ID=${ECMC_CPP_LOGIC_ID},APP_PANEL=${ECMC_CPP_LOGIC_APP_PANEL}")
epicsEnvSet("ECMC_CPP_LOGIC_DEFAULT_EPICS_SUBST", "${ECMC_CPP_LOGIC_FILE}.substitutions")

ecmcFileExist("${ECMC_CPP_LOGIC_FILE}",1)
ecmcConfigOrDie "Cfg.LoadCppLogic(${ECMC_CPP_LOGIC_ID},${ECMC_CPP_LOGIC_FILE},${ECMC_CPP_LOGIC_CONFIG})"

ecmcEpicsEnvSetCalcTernary("ECMC_CPP_LOGIC_REPORT", "${REPORT=1}>0", "", "#")
${ECMC_CPP_LOGIC_REPORT}ecmcConfigOrDie "Cfg.ReportCppLogic(${ECMC_CPP_LOGIC_ID})"
epicsEnvUnset(ECMC_CPP_LOGIC_REPORT)

ecmcIf("'${LOAD_DEFAULT_PVS=1}'='0'",CPP_LOGIC_CORE_SKIP_TRUE,CPP_LOGIC_CORE_SKIP_FALSE)
# skip built-in C++ logic control/status PVs
#else
  ${CPP_LOGIC_CORE_SKIP_FALSE}ecmcIf("'${DB_MACROS=EMPTY}'='EMPTY'",CPP_LOGIC_CORE_DB_EMPTY_TRUE,CPP_LOGIC_CORE_DB_EMPTY_FALSE)
  ${CPP_LOGIC_CORE_SKIP_FALSE}${CPP_LOGIC_CORE_DB_EMPTY_TRUE}dbLoadTemplate("${ECMC_CPP_LOGIC_CORE_EPICS_SUBST}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE}")
  #else
  ${CPP_LOGIC_CORE_SKIP_FALSE}${CPP_LOGIC_CORE_DB_EMPTY_FALSE}dbLoadTemplate("${ECMC_CPP_LOGIC_CORE_EPICS_SUBST}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE},${DB_MACROS=''}")
  ${CPP_LOGIC_CORE_SKIP_FALSE}ecmcEndIf(CPP_LOGIC_CORE_DB_EMPTY_TRUE,CPP_LOGIC_CORE_DB_EMPTY_FALSE)
ecmcEndIf(CPP_LOGIC_CORE_SKIP_TRUE,CPP_LOGIC_CORE_SKIP_FALSE)

ecmcIf("'${LOAD_APP_PVS=0}'='0'",CPP_LOGIC_APP_SKIP_TRUE,CPP_LOGIC_APP_SKIP_FALSE)
# skip generated app PVs
#else
  ${CPP_LOGIC_APP_SKIP_FALSE}ecmcIf("'${EPICS_SUBST=EMPTY}'='EMPTY'",CPP_LOGIC_APP_SUBST_EMPTY_TRUE,CPP_LOGIC_APP_SUBST_EMPTY_FALSE)
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_TRUE}ecmcFileExist("${ECMC_CPP_LOGIC_DEFAULT_EPICS_SUBST}",1,1)
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_TRUE}ecmcIf("'${DB_MACROS=EMPTY}'='EMPTY'",CPP_LOGIC_APP_DB_EMPTY_TRUE_1,CPP_LOGIC_APP_DB_EMPTY_FALSE_1)
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_TRUE}${CPP_LOGIC_APP_DB_EMPTY_TRUE_1}dbLoadTemplate("${ECMC_CPP_LOGIC_DEFAULT_EPICS_SUBST}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE}")
  #else
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_TRUE}${CPP_LOGIC_APP_DB_EMPTY_FALSE_1}dbLoadTemplate("${ECMC_CPP_LOGIC_DEFAULT_EPICS_SUBST}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE},${DB_MACROS=''}")
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_TRUE}ecmcEndIf(CPP_LOGIC_APP_DB_EMPTY_TRUE_1,CPP_LOGIC_APP_DB_EMPTY_FALSE_1)
#else
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_FALSE}ecmcFileExist("${EPICS_SUBST=''}",1,1)
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_FALSE}ecmcIf("'${DB_MACROS=EMPTY}'='EMPTY'",CPP_LOGIC_APP_DB_EMPTY_TRUE_2,CPP_LOGIC_APP_DB_EMPTY_FALSE_2)
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_FALSE}${CPP_LOGIC_APP_DB_EMPTY_TRUE_2=}dbLoadTemplate("${EPICS_SUBST=''}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE}")
  #else
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_FALSE}${CPP_LOGIC_APP_DB_EMPTY_FALSE_2=}dbLoadTemplate("${EPICS_SUBST=''}", "${ECMC_CPP_LOGIC_DB_MACROS_BASE},${DB_MACROS=''}")
  ${CPP_LOGIC_APP_SKIP_FALSE}${CPP_LOGIC_APP_SUBST_EMPTY_FALSE}ecmcEndIf(CPP_LOGIC_APP_DB_EMPTY_TRUE_2,CPP_LOGIC_APP_DB_EMPTY_FALSE_2)
  ${CPP_LOGIC_APP_SKIP_FALSE}ecmcEndIf(CPP_LOGIC_APP_SUBST_EMPTY_TRUE,CPP_LOGIC_APP_SUBST_EMPTY_FALSE)
ecmcEndIf(CPP_LOGIC_APP_SKIP_TRUE,CPP_LOGIC_APP_SKIP_FALSE)

ecmcEpicsEnvSetCalc(ECMC_CPP_LOGIC_COUNT, "$(ECMC_CPP_LOGIC_COUNT=0)+1")
ecmcEpicsEnvSetCalc(LOGIC_ID, "${ECMC_CPP_LOGIC_ID}+1", "%d")
