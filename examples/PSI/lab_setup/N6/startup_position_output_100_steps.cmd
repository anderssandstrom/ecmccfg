#- Dedicated 100-full-step output trial; see README_position_output_100_steps.md.
#- Run from this directory instead of startup.cmd or startup_pulse_per_fullstep.cmd.
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a

#- Additional native feedback PDO; suppress record initialization of the gate.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=N6-1-1-1-S_POS_OUT,MACROS='PINI=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0,N6_POS_UNIT=0x02AC0000'"
epicsEnvSet(DRV_SID,$(ECMC_EC_SLAVE_NUM))

#- Append after the motor component so the final SDO units match this trial.
${SCRIPTEXEC} ./cfg/position_output_100_steps.cmd "N6_SID=${DRV_SID}"

#- Dedicated axis uses 0x6063, with conservative commissioning speeds.
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/axis_position_output.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${DRV_SID},ENC_SID=${DRV_SID}"
