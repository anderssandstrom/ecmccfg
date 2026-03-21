require ecmccfg "MASTER_ID=0,ENG_MODE=1"

# EL7041-0052 one-channel stepper terminal
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230,STEPS=400'"

# One PVT-enabled motion axis
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,  "FILE=./cfg/axis.yaml, DEV=${IOC}, DRV_SLAVE=${ECMC_EC_SLAVE_NUM}"

# Explicit PVT controller setup. This is optional for sizes, but recommended
# when you want the PVT workflow to be visible in the startup file.
${SCRIPTEXEC} ${ecmccfg_DIR}pvtControllerConfig.cmd
