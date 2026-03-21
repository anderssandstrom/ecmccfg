#- Example config for SmarAct MCS2 with one linear and one rotary axis
require ecmccfg "MASTER_ID=0,ENG_MODE=1"

#- SmarAct CSP updates benefit from fast record updates during commissioning
${SCRIPTEXEC} ${ecmccfg_DIR}setRecordUpdateRate.cmd "RATE_MS=1"

#- MCS2 slave with one linear positioner on channel 1 and rotary positioners on channels 2 and 3
epicsEnvSet(MCS2_SLAVE_NUM,15)
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,        "SLAVE_ID=${MCS2_SLAVE_NUM}, HW_DESC=MCS2"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd   "COMP=SmarAct-SLC1750ds, CH_ID=1, MACROS='HOME_VELO=1000,HOME_ACC=1000'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd   "COMP=SmarAct-SR2013s,   CH_ID=2"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd   "COMP=SmarAct-SR2013s,   CH_ID=3, MACROS='HOME_VELO=10000,HOME_ACC=1000'"

#- Axis 1: linear stage on channel 1
epicsEnvSet(MCS2_CHID,1)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,    "FILE=./cfg/axis_lin.yaml, DEV=${IOC}"

#- Axis 3: rotary stage on channel 3
epicsEnvSet(MCS2_CHID,3)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,    "FILE=./cfg/axis_rot.yaml, DEV=${IOC}"
