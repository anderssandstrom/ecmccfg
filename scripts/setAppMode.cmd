#==============================================================================
# setAppMode.cmd
#- Arguments: n/a
#-d /**
#-d   \brief Script for switching to operational mode.
#-d   \details Validates configuration, starts realtime thread and checks EtherCAT slaves are in OP.
#-d   \author Niko Kivel
#-d
#-d   Macros (optional):
#-d     T_SMP_HOOK_MS  : Update rate of MCU-Updated PV [ms]
#-d     PROC_HOOK      : Forward link pf MCU-Updated PV
#-d     ECMC_PROC_HOOK : Same as PROC_HOOK
#-d     T_SMP_MS       : Maximum sample time of other records loaded by this script [ms]
#-d     ECMC_STARTUP_GATE : Hold axes/PLCs until IOC/bus readiness (0/1, default 0)
#-d     ECMC_SDO_AUTO_START : Start after queued SDO restore (0/1, default 1).
#-d                           With queued SDOs, 0 holds activation until an explicit
#-d                           ecmcStartAppModeAsync(0), for initial commissioning.
#-d 
#-d   \file
#-d */
ecmcFileExist("${ECMC_CONFIG_ROOT}general.cmd",1)
${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}general.cmd

#- Only load ec records if master is selected. ECMC_EC_MASTER_ID is set in startup.cmd.
ecmcEpicsEnvSetCalcTernary(ECMC_MASTER_CMD, "${ECMC_EC_MASTER_ID=0}>=0", "","#- ")
${ECMC_MASTER_CMD} ecmcFileExist("ecmcEc.db",1,1)
${ECMC_MASTER_CMD} dbLoadRecords("ecmcEc.db","P=${ECMC_PREFIX},ECMC_EC_MP=${ECMC_EC_MP=m},PORT=${ECMC_ASYN_PORT},ADDR=0,TIMEOUT=1,MASTER_ID=${ECMC_EC_MASTER_ID},T_SMP_MS=${ECMC_SAMPLE_RATE_MS},TSE=${ECMC_TSE},ECMCCFG_VER=${ecmccfg_VERSION},EPICS_VER=${EPICS_RELEASE}")

#- Load pvt controller records if PVT is in use and not been previously configured
ecmcEpicsEnvSetCalcTernary(ECMC_PVT_AUTO_CFG_CMD,"${ECMC_MR_PVT_CONTROLLER_CONFIGURED=0}==0 and ${ECMC_MR_PVT_AXES_COUNT_IN_USE=0}>0","","#-")
${ECMC_PVT_AUTO_CFG_CMD}# Warning: PVT configured for axes but PVT asynMotorController config not done. A default configuration will be executed:
${ECMC_PVT_AUTO_CFG_CMD}${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}pvtControllerConfig.cmd
${ECMC_PVT_AUTO_CFG_CMD}epicsEnvUnset(ECMC_MR_PVT_MAX_RB_POINTS_IN_USE)
${ECMC_PVT_AUTO_CFG_CMD}epicsEnvUnset(ECMC_MR_PVT_MAX_POINTS_IN_USE)
${ECMC_PVT_AUTO_CFG_CMD}epicsEnvUnset(ECMC_MR_PVT_AXES_COUNT_IN_USE)
epicsEnvUnset(ECMC_PVT_AUTO_CFG_CMD)
epicsEnvUnset(ECMC_MR_PVT_CONTROLLER_CONFIGURED)

# EtherCAT bus startup delay (minimum startup time) [seconds->cycles]:
ecmcEpicsEnvSetCalc("EC_DELAY_CYCLES" ,"${ECMC_EC_SAMPLE_RATE=1000}*${ECMC_EC_STARTUP_DELAY=0}")
ecmcConfigOrDie "Cfg.EcSetDelayECOkAtStartup(${EC_DELAY_CYCLES=0})"
epicsEnvUnset(EC_DELAY_CYCLES)
epicsEnvUnset(ECMC_EC_STARTUP_DELAY)

#- Alias the existing first-slave pointer once for prefix-only discovery.
ecmcEpicsEnvSetCalcTernary(ECMC_SIM_META_CMD, "${ECMC_SIM=0}=1 and ${ECMC_SIM_METADATA_DONE=0}=0", "", "#-")
${ECMC_SIM_META_CMD}dbLoadRecords("ecmcSimulationFirstSlave.db","P=${ECMC_PREFIX},SIM_P=${ECMC_SIM_PREFIX=${ECMC_PREFIX}SIM:}")
${ECMC_SIM_META_CMD}epicsEnvSet(ECMC_SIM_METADATA_DONE,1)
epicsEnvUnset(ECMC_SIM_META_CMD)

#- One common loader creates records for declared simulated I/O fields.
#- It runs before runtime/iocInit; hardware and axis templates are unchanged.
ecmcEpicsEnvSetCalcTernary(ECMC_SIM_RECORDS_CMD, "${ECMC_SIM=0}=1", "", "#-")
${ECMC_SIM_RECORDS_CMD}ecmcConfigOrDie "Cfg.SimLoadRecords(${ECMC_SIM_PREFIX=${ECMC_PREFIX}SIM:})"
epicsEnvUnset(ECMC_SIM_RECORDS_CMD)

# Queued SDOs need post-restore collection before activation even when the
# requested default was ECMC-first. Keep legacy startup unchanged otherwise.
ecmcEpicsEnvSetCalcTernary(ECMC_SDO_BAD_AUTO_START,"'${ECMC_SDO_AUTO_START=1}'!='0' and '${ECMC_SDO_AUTO_START=1}'!='1'","","#-")
${ECMC_SDO_BAD_AUTO_START}ecmcExit Error: ECMC_SDO_AUTO_START must be 0 or 1
epicsEnvUnset(ECMC_SDO_BAD_AUTO_START)
ecmcEpicsEnvSetCalcTernary(ECMC_START_EPICS_FIRST_EFFECTIVE,"${ECMC_START_EPICS_FIRST=0}=1 or ${ECMC_SDO_QUEUE_IN_USE=0}=1",1,0)
ecmcEpicsEnvSetCalcTernary(ECMC_START_EPICS_FIRST_CMD,"${ECMC_START_EPICS_FIRST_EFFECTIVE}=1","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_START_ECMC_FIRST_CMD,"${ECMC_START_EPICS_FIRST_EFFECTIVE}=0","","#-")

#- Start RT thread
ecmcConfigOrDie "Cfg.SetStartupGate(${ECMC_STARTUP_GATE=1})"
${ECMC_START_ECMC_FIRST_CMD}ecmcConfigOrDie "Cfg.SetAppMode(1)"
#- Postpone ecmc start if EPICS should start first
ecmcEpicsEnvSetCalcTernary(ECMC_START_SDO_WORKER_CMD,"${ECMC_START_EPICS_FIRST_EFFECTIVE}=1 and (${ECMC_SDO_QUEUE_IN_USE=0}=0 or ${ECMC_SDO_AUTO_START=1}=1)","","#-")
${ECMC_START_SDO_WORKER_CMD}afterIocRunning "ecmcStartAppModeAsync(${ECMC_EC_STABILIZATION_TIME=2})"
epicsEnvUnset(ECMC_START_SDO_WORKER_CMD)

# Stabilize EtherCAT bus.....
${ECMC_START_ECMC_FIRST_CMD}epicsThreadSleep ${ECMC_EC_STABILIZATION_TIME=2}

#- For check in finalize.cmd if executed
epicsEnvSet(ECMC_SET_APP_MODE_DONE,1)

#- Dump cfg diags
afterInit "ecmcLogBufferPrint"
