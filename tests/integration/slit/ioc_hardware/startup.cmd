# Real-hardware slit commissioning IOC. Run from this directory.
# Terminal positions and drive settings follow the existing slit lab setup.
# One BiSS encoder: TR_LO on EL5042 channel 1; TR_HI uses its internal counter.
# EL2794 slave 25, channel 1 switches TR_LO encoder power (active high).
epicsEnvSet("IOC", "${HARDWARE_IOC=HWSLIT}")
require ecmccfg ${ECMCCFG_HW_VER=sandst_a} "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000,ECMC_VER=${ECMC_HW_VER=sandst_a},SIM=0"
on error halt
# Assert the physical backend; fail if this master was initialized for simulation.
ecmcConfigOrDie "Cfg.SetIoBackend(0,0)"
asynSetTraceMask(${ECMC_ASYN_PORT}, -1, 0x01)
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"

# Physical station positions; unlisted rack terminals are not used by this IOC.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
# Brake coils: output 01 = LO, output 02 = HI; 1 releases the brake.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=5,HW_DESC=EL2008"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=25,HW_DESC=EL2794"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=9,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=12,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=24000,R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_ax6_HI.yaml,DRV_SLAVE=12,ENC_SLAVE=12,ENC_CHANNEL=01,M_ID=0"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_ax5_LO.yaml,DRV_SLAVE=14,ENC_SLAVE=14,ENC_CHANNEL=01,M_ID=0"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd "FILE=./cfg/biss-c.yaml,DEV=${IOC},ENC_SID=9,ENC_CH=01"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_vax5_YCEN.yaml,AX_ID=12,M_ID=0,DRV_SLAVE=14"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_vax6_YGAP.yaml,AX_ID=13,M_ID=0,DRV_SLAVE=14"
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/axis_main.plc,INC=./cfg,PLC_MACROS='AX_CEN=12,AX_GAP=13,AX_LO=5,AX_HI=6'"
${SCRIPTEXEC} ${ecmccfg_DIR}addMasterSlaveSM.cmd "NAME=Slit_SM,MST_GRP_NAME=virtualAxes,SLV_GRP_NAME=realAxes"

# PVT controller finalization links spare EL2008 output 05 (active high).
# 400 ms pulses remain observable through CA and fit between test triggers.
epicsEnvSet(TRG_EC_ENTRY,"ec0.s5.binaryOutput05.0")
epicsEnvSet(TRG_DUR_S,"0.4")
dbLoadRecords("./hardware-test.db", "P=${ECMC_PREFIX}")

# The launcher initializes the IOC after loading this file; the registered
# atInit hook finalizes ECMC and starts the real EtherCAT master.
# No motion commands, counter images or fake ready flags are issued.
