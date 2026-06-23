##############################################################################
## Motion sequencer lab example based on stepper_bissc/startup_local_hw.cmd

require ecmccfg sandst_a "ENG_MODE=1,MASTER_ID=0,ECMC_VER=sandst_a"

# 0:7 - EL7041 1Ch Stepper
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1500,I_STDBY_MA=1000,U_NOM_MV=48000,R_COIL_MOHM=1230'"
epicsEnvSet(DRV_SID,${ECMC_EC_SLAVE_NUM})

# 0:2 - EL5042 2Ch BiSS-C Encoder, RLS-LA11
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=9,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=2"
epicsEnvSet(ENC_SID,${ECMC_EC_SLAVE_NUM})

libversionShow

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${DRV_SID},ENC_SID=${ENC_SID},ENC_CH=01"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd,    "FILE=./cfg/enc_open_loop.yaml,DEV=${IOC},ENC_SID=${DRV_SID}"

# Create sequence 0 and load its records on port ECMC_SEQ0.
${SCRIPTEXEC} ${ecmccfg_DIR}addMotionSequence.cmd, "SEQ_ID=0,MAX_STEPS=16,DB_PREFIX=$(IOC):,RECORD_PREFIX=Seq0-,REPORT=1"

# Safe manual test: reset/power, move to absolute position 10 mm, start a
# nonblocking +0.2 mm move, wait for in-position, delay, then return -0.2 mm
# with a blocking move.
# The sequence is compiled and armed, but is not started automatically.

# SeqReset(seqIndex,stepIndex,axis,timeoutMs)
# Sequence 0, step 0: reset axis 1 and wait up to 2000 ms for completion.
ecmcConfigOrDie "Cfg.SeqReset(0,0,1,2000)"

# SeqPower(seqIndex,stepIndex,axis,enable,timeoutMs)
# Sequence 0, step 1: enable axis 1 and wait up to 5000 ms for enabled status.
ecmcConfigOrDie "Cfg.SeqPower(0,1,1,1,5000)"

# SeqMoveAbs(seqIndex,stepIndex,axis,position,velocity,acceleration,deceleration,timeoutMs,wait)
# Sequence 0, step 2: move axis 1 to absolute position 10 mm at 0.5 mm/s.
# wait=1 explicitly makes this a blocking move with a 30000 ms timeout.
ecmcConfigOrDie "Cfg.SeqMoveAbs(0,2,1,10.0,0.5,2.0,2.0,30000,1)"

# SeqMoveRel(seqIndex,stepIndex,axis,distance,velocity,acceleration,deceleration,timeoutMs,wait)
# Sequence 0, step 3: start a +0.2 mm move on axis 1 at 0.5 mm/s.
# wait=0 makes this step advance immediately after issuing the command.
ecmcConfigOrDie "Cfg.SeqMoveRel(0,3,1,0.2,0.5,2.0,2.0,1000,0)"

# SeqWaitInPos(seqIndex,stepIndex,axis,timeoutMs)
# Sequence 0, step 4: wait up to 5000 ms for axis 1 to reach its target.
ecmcConfigOrDie "Cfg.SeqWaitInPos(0,4,1,5000)"

# SeqWaitTime(seqIndex,stepIndex,waitMs)
# Sequence 0, step 5: remain at the outward position for 500 ms.
ecmcConfigOrDie "Cfg.SeqWaitTime(0,5,500)"

# SeqMoveRel(seqIndex,stepIndex,axis,distance,velocity,acceleration,deceleration,timeoutMs)
# Sequence 0, step 6: move axis 1 by -0.2 mm and wait up to 5000 ms.
# The short command form defaults to blocking behavior.
ecmcConfigOrDie "Cfg.SeqMoveRel(0,6,1,-0.2,0.5,2.0,2.0,5000)"

# CompileMotionSeq(seqIndex): validate and compile sequence 0.
ecmcConfigOrDie "Cfg.CompileMotionSeq(0)"

# ArmMotionSeq(seqIndex): copy the compiled plan into the active RT plan.
ecmcConfigOrDie "Cfg.ArmMotionSeq(0)"
