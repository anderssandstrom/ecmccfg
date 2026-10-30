#- Configuration scripts
#require ecmccfg v11.0.9_RC2 "MASTER_ID=0,ENG_MODE=1,EC_RATE=500,ECMC_VER=v11.0.9_RC2"
require ecmccfg sandst_a "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000,ECMC_VER=sandst_a,SIM=1"
#require ecmccfg sandst_a "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000,ECMC_VER=sandst_a"
#require ecmccfg "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000"
#- Only output errors
asynSetTraceMask(${ECMC_ASYN_PORT}, -1, 0x01)
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"

#- #################################################################
# Configure Hardware and Motion
# EtherCAT slave configuration

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=1,HW_DESC=EL2068"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=2,HW_DESC=EL2819"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=3,HW_DESC=EL5001"
# Requires custom cfg ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=4,HW_DESC=EL6224"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=5,HW_DESC=EL2008"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=6,HW_DESC=EL4132"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=7,HW_DESC=EL5072"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=8,HW_DESC=EL1008"
# Later ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=9,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=10,HW_DESC=EL5102"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=11,HW_DESC=EK1100"
# Later ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=12,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=13,HW_DESC=EL7201"
# Later ${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=15,HW_DESC=EL7342"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=16,HW_DESC=EL7411"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=17,HW_DESC=EL7211-9014"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=18,HW_DESC=EL9576"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=19,HW_DESC=ED7062"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=20,HW_DESC=EL7047"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=21,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=22,HW_DESC=EL9227-5500"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=23,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=24,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=25,HW_DESC=EL3204"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=26,HW_DESC=EL2008"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=27,HW_DESC=EL1008"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=28,HW_DESC=EL7211-9014"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=29,HW_DESC=EL7211-9014"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=30,HW_DESC=EL7211-9014"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=31,HW_DESC=EL7211-9014"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=32,HW_DESC=EL9576"

# 0:2  - EL5042    2Ch BiSS-C Encoder, RLS-LA11
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=9,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=2"
epicsEnvSet(ENC_SID,${ECMC_EC_SLAVE_NUM})

# 0:7 - EL7031    1Ch Stepper
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=12,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=1000, I_STDBY_MA=500, U_NOM_MV=24000, R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis_ax6_HI.yaml,        DRV_SLAVE=${ECMC_EC_SLAVE_NUM}, ENC_SLAVE=${ECMC_EC_SLAVE_NUM}, ENC_CHANNEL=01,M_ID=${ECMC_EC_MASTER_ID}"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd,    "FILE=./cfg/biss-c.yaml, DEV=${IOC}, ENC_SID=${ENC_SID}"

# 0:7 - EL7041    1Ch Stepper
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=1000, I_STDBY_MA=500, U_NOM_MV=48000, R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis_ax5_LO.yaml,        DRV_SLAVE=${ECMC_EC_SLAVE_NUM}, ENC_SLAVE=${ECMC_EC_SLAVE_NUM}, ENC_CHANNEL=01,M_ID=${ECMC_EC_MASTER_ID}"

#- #################################################################
#- Virtual axes
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,      "FILE=./cfg/axis_vax5_YCEN.yaml, AX_ID=${AX_NUM=12},M_ID=${ECMC_EC_MASTER_ID},DRV_SLAVE=${ECMC_EC_SLAVE_NUM}"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,      "FILE=./cfg/axis_vax6_YGAP.yaml, AX_ID=${AX_NUM=13},M_ID=${ECMC_EC_MASTER_ID},DRV_SLAVE=${ECMC_EC_SLAVE_NUM}"

#- #################################################################
#- PLCs with kinematics (note the INC var including dirs to search for include files)
#- The group ID:s configured in yaml are stored in GRP_<axis.group>_ID
${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}loadPLCFile.cmd,  "FILE=cfg/axis_main.plc, INC=./cfg/:${ecmccfg_DIR}, PLC_MACROS='AX_CEN=12, AX_GAP=13,  AX_LO=5, AX_HI=6'"
#${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd,    "FILE=./cfg/axis_main.plc, PLC_ID=1, INC=.:${ecmccfg_DIR}, PLC_MACROS='PLC_ID=1, AX_M1=12, AX_M2=13, AX_S1=5, AX_S2=6, GRP_ID_SA=${GRP_realAxes_ID}, GRP_ID_MA=${GRP_virtualAxes_ID},DBG='"

#- Add state machine to sync the virtual and physical axes (the groups are defined in the yaml axis-cfg files) 
${SCRIPTEXEC} ${ecmccfg_DIR}addMasterSlaveSM.cmd "NAME=Slit_SM, MST_GRP_NAME=virtualAxes, SLV_GRP_NAME=realAxes"


