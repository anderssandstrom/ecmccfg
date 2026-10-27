require ecmccfg v11.2.0_RC1 "ENG_MODE=1,ECMC_VER=v11.2.0_RC1,MASTER_ID=1,MX_1=10,MX_REPORT=1"
#require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=v11.2.0_RC1,MASTER_ID=1"
require ecmccomp sandst_a
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"

#
#   0  0:0   PREOP  +  MB1100-0002 (Bluetooth gateway)
#   1  0:1   INIT   E  0x00000000:0x00000000
#   2  0:2   INIT   E  0x00000000:0x00000000
#   3  0:3   INIT   E  0x00000000:0x00000000
#   4  0:4   PREOP  +  MS1010-1002-1334 Power infeed + forwarding, 230 V AC/10 A, 24 V
#   5  0:5   PREOP  +  MO7062-0100-1112 2-channel motion interface, stepper motor, 24 
#   6  0:6   PREOP  +  MO2338-0000-1112 8-channel digital combi, 24�V DC/0.5�A, M12
#   7  0:7   PREOP  +  0x00000002:0x811fbc0b
#   8  0:8   INIT   E  0x00000000:0x00000000
#   9  0:9   PREOP  +  MB1120 backplane junction
#  10  0:10  PREOP  +  MS4210-1003-1114 EtherCAT power output, EtherCAT, 24 V DC/2x 10
#  11  0:11  PREOP  +  MS1110-0000 | System-Modul, EtherCAT Verl�ngerung


${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MB1100-0002"
${SCRIPTEXEC} ${ecmccfg_DIR}ignoreSlaves.cmd,     "COUNT=3"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MS1010-1002-1334"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MO7062-0100_OPT"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MO2338-0000"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MO1008-0000"
${SCRIPTEXEC} ${ecmccfg_DIR}ignoreSlaves.cmd,     "COUNT=1"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MB1120"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MS4210-1003-1114"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "HW_DESC=MS1110-0000"

