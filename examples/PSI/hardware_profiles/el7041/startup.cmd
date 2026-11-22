# Example fragment for an EL7041 single-axis IOC.
# Include from an IOC startup after ecmccfg initialization.
# Adjust motor current/voltage and motion scaling to the real installation.
${SCRIPTEXEC} "${ecmccfg_DIR}addMaster.cmd" "MASTER_ID=0"
${SCRIPTEXEC} "${ecmccfg_DIR}addSlave.cmd" "HW_DESC=EK1100,SLAVE_ID=0"
${SCRIPTEXEC} "${ecmccfg_DIR}addSlave.cmd" "HW_DESC=EL7041,SLAVE_ID=1"
epicsEnvSet(DRV_SLAVE,1)
# Optional: configure motor parameters with applyComponent.cmd for the installed motor.
${SCRIPTEXEC} "${ecmccfg_DIR}loadYamlAxis.cmd" "FILE=./cfg/axis.yaml,DEV=${IOC}"
${SCRIPTEXEC} "${ecmccfg_DIR}applyConfig.cmd"
