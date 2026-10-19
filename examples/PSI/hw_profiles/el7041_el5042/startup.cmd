# Profile expansion runs inside the IOC; no Python or ECB changes required.
on error halt
# Example topology: EK1100 (0), EL5042 (1), EL7041 (2).
require ecmccfg "ENG_MODE=1"
require ecmccomp

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=1,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
epicsEnvSet(ENC_SID,${ECMC_EC_SLAVE_NUM})

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=2,HW_DESC=EL7041"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230'"
# Match motor data and configured full-scale step rate to cfg/axis.yaml.
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${ECMC_EC_SLAVE_NUM},ENC_SID=${ENC_SID},ENC_CH=01"
