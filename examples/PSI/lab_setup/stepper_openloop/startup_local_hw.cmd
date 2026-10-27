##############################################################################
## Example config for open loop only

require ecmccfg "ENG_MODE=1,MASTER_ID=0"

# 0:11 - EL7031    1Ch Stepper

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=10,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper, MACROS='I_MAX_MA=1000, I_STDBY_MA=200, U_NOM_MV=24000, R_COIL_MOHM=1230,SPEED_RANGE=2'"
epicsEnvSet(DRV_SID,${ECMC_EC_SLAVE_NUM})
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis_open_loop.yaml,    DEV=${IOC}_TEST, AX_NAME=M1, AXIS_ID=4, DRV_SID=${DRV_SID}, ENC_SID=${DRV_SID}, ENC_CH=01" 


