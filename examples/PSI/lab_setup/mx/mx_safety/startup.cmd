#require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1,MX_1=10,MX_REPORT=1"
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"

#Master1
#   0  0:0   PREOP  +  MB1100-0002 (Bluetooth gateway)
#   1  0:1   INIT   E  0x00000000:0x00000000
#   2  0:2   PREOP  +  MO7062-0100-1112 2-channel motion interface, stepper motor, 24 
#   3  0:3   PREOP  +  MO2338-0000-1112 8-channel digital combi, 24�V DC/0.5�A, M12
#   4  0:4   PREOP  +  MO1918-0000-1112 | 8-channel digital input, 24 V DC, M12, TwinS
#   5  0:5   INIT   E  0x00000000:0x00000000
#   6  0:6   INIT   +  0x00000000:0x00000000
#   7  0:7   PREOP  +  MS1010-1002-1334 Power infeed + forwarding, 230 V AC/10 A, 24 V
#   8  0:8   PREOP  +  MO7221-9018-1114 1-channel motion interface, servomotor, 24 V D
#   9  0:9   PREOP  +  MO7221-9018-1124 1-channel motion interface, servomotor, 48 V D
#  10  0:10  PREOP  +  MO2424-0000-1110 4-channel digital output, 24 V DC/0.5 A, pneum
#  11  0:11  PREOP  +  MS1010-0021-1114 Power infeed, 24 V DC/10 A, 48 V DC/10 A, B17
#  12  0:12  PREOP  +  MS4208-2003-1112 EtherCAT power output, EtherCAT, 24 V DC, 8 A,
#

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=0, HW_DESC=MB1100-0002"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=2, HW_DESC=MO7062-0100"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd    "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000, I_STDBY_MA=100, U_NOM_MV=24000,L_COIL_UH=3050,R_COIL_MOHM=2630'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd    "COMP=Drive-Generic-Ctrl-Params,    CH_ID=1, MACROS='L_COIL_UH=3100,R_COIL_MOHM=2620,I_TI=12,I_KP=59,V_TI=150,V_KP=176,P_KP=10'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd    "COMP=Generic-Ch-Not-Used,          CH_ID=2'"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=3, HW_DESC=MO2338-0000-1112"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=4, HW_DESC=MO1918-0000"
${SCRIPTEXEC} ${ecmccfg_DIR}addFSoEConn.cmd,      "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=01"
${SCRIPTEXEC} ${ecmccfg_DIR}addFSoEConn.cmd,      "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=02"
${SCRIPTEXEC} ${ecmccfg_DIR}finishFSoEMaster.cmd, "SFTY_MASTER_SID=4"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=7, HW_DESC=MS1010-1002-1334"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=8, HW_DESC=MO7221-9016-1114"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd    "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"
$(SCRIPTEXEC) $(ecmccfg_DIR)loadYamlAxis.cmd      "FILE=./cfg/axis.yaml, DRV_ID=$(ECMC_EC_SLAVE_NUM), AX_NAME='M1', AX_ID=1"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=9, HW_DESC=MO7221-9016-1114"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd    "COMP=Motor-Beckhoff-AM8121-XFX0, MACROS='I_MAX_MA=1355'"
$(SCRIPTEXEC) $(ecmccfg_DIR)loadYamlAxis.cmd      "FILE=./cfg/axis.yaml, DRV_ID=$(ECMC_EC_SLAVE_NUM), AX_NAME='M2', AX_ID=2"

#- Setup FSoE com
${SCRIPTEXEC} ${ecmccfg_DIR}linkFSoEConn.cmd,     "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=01,SFTY_SLAVE_SID=8,SFTY_SLAVE_CONN=01"
${SCRIPTEXEC} ${ecmccfg_DIR}linkFSoEConn.cmd,     "SFTY_MASTER_SID=4,SFTY_MASTER_CONN=02,SFTY_SLAVE_SID=9,SFTY_SLAVE_CONN=01"

