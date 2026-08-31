require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a
#- Stepper drive
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=N6-1-1-1-S"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=400, I_STDBY_MA=100'"
epicsEnvSet(DRV_SID,$(ECMC_EC_SLAVE_NUM))

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,              DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${DRV_SID}, ENC_SID=${DRV_SID}, ENC_CH=01"

