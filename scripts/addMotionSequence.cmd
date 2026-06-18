#==============================================================================
# addMotionSequence.cmd
#- Arguments: [SEQ_ID], [MAX_STEPS], [ASYN_PORT], [DB_PREFIX], [RECORD_PREFIX], [SCAN], [PREC], [SOFT_TRG_FLNK], [LOAD_PVS], [REPORT]

#-d /**
#-d   \brief Create one ecmc motion sequence and optionally load its EPICS records.
#-d   \details The sequence must be created before records connect to its
#-d            dedicated asyn port.
#-d   \file
#-d   \param SEQ_ID        Sequence index, default 0.
#-d   \param MAX_STEPS     Maximum configured steps, default 32.
#-d   \param ASYN_PORT     Dedicated asyn port, default ECMC_SEQ<SEQ_ID>.
#-d   \param DB_PREFIX     EPICS record prefix, default $(IOC):.
#-d   \param RECORD_PREFIX Sequence record prefix, default Seq<SEQ_ID>-.
#-d   \param SCAN          Status/readback polling rate, default .1 second.
#-d   \param PREC          Floating-point precision, default 3.
#-d   \param SOFT_TRG_FLNK Optional forward link from the soft-trigger counter.
#-d   \param LOAD_PVS      Load ecmcMotionSequence.template, default 1.
#-d   \param REPORT        Report the created sequence, default 0.
#-d */

epicsEnvSet("ECMC_MOTION_SEQ_ID", "${SEQ_ID=0}")
epicsEnvSet("ECMC_MOTION_SEQ_PORT", "${ASYN_PORT=ECMC_SEQ${ECMC_MOTION_SEQ_ID}}")

ecmcConfigOrDie "Cfg.CreateMotionSeq(${ECMC_MOTION_SEQ_ID},${MAX_STEPS=32},${ECMC_MOTION_SEQ_PORT})"

ecmcIf("'${LOAD_PVS=1}'='0'",MOTION_SEQ_PVS_SKIP_TRUE,MOTION_SEQ_PVS_SKIP_FALSE)
# skip motion sequence PVs
#else
  ${MOTION_SEQ_PVS_SKIP_FALSE}ecmcFileExist("ecmcMotionSequence.template",1,1)
  ${MOTION_SEQ_PVS_SKIP_FALSE}dbLoadRecords("ecmcMotionSequence.template","P=${DB_PREFIX=$(IOC):},R=${RECORD_PREFIX=Seq${ECMC_MOTION_SEQ_ID}-},PORT=${ECMC_MOTION_SEQ_PORT},SCAN=${SCAN=.1 second},PREC=${PREC=3},SOFT_TRG_FLNK=${SOFT_TRG_FLNK=''}")
ecmcEndIf(MOTION_SEQ_PVS_SKIP_TRUE,MOTION_SEQ_PVS_SKIP_FALSE)

ecmcEpicsEnvSetCalcTernary("ECMC_MOTION_SEQ_REPORT", "${REPORT=0}>0", "", "#")
${ECMC_MOTION_SEQ_REPORT}ecmcConfigOrDie "Cfg.ReportMotionSeq(${ECMC_MOTION_SEQ_ID})"
epicsEnvUnset(ECMC_MOTION_SEQ_REPORT)

