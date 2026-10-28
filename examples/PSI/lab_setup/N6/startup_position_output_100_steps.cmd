#- Dedicated 100-full-step output and raw open-loop counter axis trial.
#- See README_position_output_100_steps.md for observed firmware behavior.
#- Bench observation 2026-10-28: fresh start -> first output edge at 100 full steps.
#- After method-35 homing -> first edge at 50, then 150, 250, ... full steps.
#- The following edge spacing remains 100 full steps; this shift is repeatable.
#- Homing once at startup is a proposed way to obtain a consistent 50-step first
#- edge. It is not automatic here; trigger M1 homing before the measurement.
#- Run from this directory instead of startup.cmd or startup_pulse_per_fullstep.cmd.
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a

#- Fine counter and optional homing PDOs; HOMING maps parameters, it does not home.
#- Axis homing uses sequence 26 with automatic mode switching; see README.
#- Optional diagnostics default off; startup_opt_all.cmd enables both.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=N6-1-1-1-S_OPT,OPT='RAW_POS=1,HOMING=1,CAPTURE=${N6_CAPTURE=0},ANALOG_IN=${N6_ANALOG_IN=0}'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
epicsEnvSet(DRV_SID,$(ECMC_EC_SLAVE_NUM))

#- Initialize disabled with zero velocity before loading the axis controller.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${DRV_SID},driveControl01,0)"
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${DRV_SID},velocitySetpoint01,0)"

#- Position output follows the motor so its position units take precedence.
#- ARM changes only output 1's gate; the brake and other outputs are preserved.
#- N6_IO_24V=0 selects 5 V logic outputs (also the component default).
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PositionOutput,CH_ID=1,MACROS='FULL_STEPS=100,OUTPUT=1,ARM=1,N6_IO_24V=0'"

#- Bench readings support raw 0x6063 as the open-loop counter with 0x60E6:01=0.
#- Keep sensorless feedback disabled. Do not use coarse 0x6064 for axis control.
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/axis_position_output.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${DRV_SID},ENC_SID=${DRV_SID}"
