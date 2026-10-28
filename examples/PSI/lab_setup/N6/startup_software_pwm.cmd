#- Standalone output-1 software-PWM trial. No motion axis is loaded.
#- Run from this directory instead of the position-output startup.
#- See README_software_pwm.md: 2 kHz carrier, not a position divider.
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a

#- OPT supplies masked gate controls. No extra PDOs are required for PWM.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=N6-1-1-1-S_OPT"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
#- Hold the drive disabled with zero velocity; the PWM needs no motor motion.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},driveControl01,0)"
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM},velocitySetpoint01,0)"
#- Gate stays off until explicitly armed through PosOut01-Ena.
${SCRIPTEXEC} ./cfg/software_pwm_2khz.cmd "N6_PWM_HZ=2000,N6_PWM_ARM=0,N6_IO_24V=0"
