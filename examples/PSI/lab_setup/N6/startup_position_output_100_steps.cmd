#- Dedicated DRIVE-ONLY 100-full-step output trial; see README_position_output_100_steps.md.
#- No ECMC axis or automatic motion: use the existing N6 drive records manually.
#- Run from this directory instead of startup.cmd or startup_pulse_per_fullstep.cmd.
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a

#- Use the original PDOs; suppress record initialization of the output gate.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=N6-1-1-1-S,MACROS='PINI=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0,N6_POS_UNIT=0x02AC0000'"
epicsEnvSet(DRV_SID,$(ECMC_EC_SLAVE_NUM))

#- Start with the drive disabled and zero velocity. There is no axis controller.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${DRV_SID},driveControl01,0)"
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${DRV_SID},velocitySetpoint01,0)"

#- Append after the motor component so the final SDO units match this trial.
${SCRIPTEXEC} ./cfg/position_output_100_steps.cmd "N6_SID=${DRV_SID}"

#- Do not load axis_position_output.yaml: its raw 0x6063 feedback is invalid
#- with sensorless feedback disabled, and enabling that interface caused 0x7305.
#- The original axis.yaml is also unsuitable with this coarse 0x6064 scaling.
