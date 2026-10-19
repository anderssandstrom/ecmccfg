# Profile expansion runs inside the IOC; no Python or ECB changes required.
on error halt
# Example topology: EK1100 (0), EL7062 (1). Channel 1 used; channel 2 unused.
require ecmccfg "ENG_MODE=1"
require ecmccomp

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=1,HW_DESC=EL7062_OPT"
# Inspect supported profiles and this channel's selected PDO options.
ecmcListHwProfiles
ecmcListCompatibleProfiles(${ECMC_EC_MASTER_ID=0},${ECMC_EC_SLAVE_NUM},1)
# Example motor/controller data: replace with the connected motor's values.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=500,I_STDBY_MA=100,U_NOM_MV=48000,L_COIL_UH=3100,R_COIL_MOHM=2620'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-Ctrl-Params,CH_ID=1,MACROS='L_COIL_UH=3100,R_COIL_MOHM=2620,I_TI=12,I_KP=59,V_TI=150,V_KP=176,P_KP=10'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-Generic-INC,CH_ID=1,MACROS='ST_ENC_RES=2000,TP1_POS_SRC=SEC,TP1_TRG=INDEX'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Generic-Ch-Not-Used,CH_ID=2"

# Low/high limit inputs are binaryInputs01 bits 0/1; home uses low-limit + index.
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${ECMC_EC_SLAVE_NUM}"
