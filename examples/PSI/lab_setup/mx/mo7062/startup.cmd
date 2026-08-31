require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1,MX_1=10,MX_REPORT=1"

#- Stepper drive
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=6, HW_DESC=MO7062-0100"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper, CH_ID=1, MACROS='I_MAX_MA=1000, I_STDBY_MA=100, U_NOM_MV=24000,L_COIL_UH=3050,R_COIL_MOHM=2630'"
#- Use autotune to get the controller parameters, resistance, and inductance (trigger in hw expert panel)
#- Then copy the MACROS field from panel and apply it with "Drive-Generic-Ctrl-Params" like below
#- Note: "Motor-Generic-2Phase-Stepper" also requires defining R and L (put any value).
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Drive-Generic-Ctrl-Params,    CH_ID=1, MACROS='L_COIL_UH=3100,R_COIL_MOHM=2620,I_TI=12,I_KP=59,V_TI=150,V_KP=176,P_KP=10'"

#- Must tell ecmc that channel is not used since otherwise monitoring of SDO settings will prevent IOC from start
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Generic-Ch-Not-Used,          CH_ID=2'"
epicsEnvSet(DRV_SID,${ECMC_EC_SLAVE_NUM})

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,              DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${DRV_SID}, ENC_SID=${DRV_SID}, ENC_CH=01"

