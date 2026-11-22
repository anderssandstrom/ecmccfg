# Example fragment for EL7062 channel 1 in CSV mode.
# Choose current, coil voltage/resistance/inductance for the actual motor.
${SCRIPTEXEC} "${ecmccfg_DIR}addMaster.cmd" "MASTER_ID=0"
${SCRIPTEXEC} "${ecmccfg_DIR}addSlave.cmd" "HW_DESC=EK1100,SLAVE_ID=0"
${SCRIPTEXEC} "${ecmccfg_DIR}addSlave.cmd" "HW_DESC=EL7062,SLAVE_ID=1"
epicsEnvSet(DRV_SLAVE,1)
epicsEnvSet(DRV_CHANNEL,1)
epicsEnvSet(ENC_FEEDBACK,openloop)  # Optional: incremental selects the _2 PDO
# Motor-specific parameters are intentionally not guessed here.
# Use the existing Motor-Generic-2Phase-Stepper component for channel 1.
${SCRIPTEXEC} "${ecmccfg_DIR}loadYamlAxis.cmd" "FILE=./cfg/axis.yaml,DEV=${IOC}"
${SCRIPTEXEC} "${ecmccfg_DIR}applyConfig.cmd"
