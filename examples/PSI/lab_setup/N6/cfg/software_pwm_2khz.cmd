#- Compatibility wrapper for the original PWM bench script.
#- Requires current ecmccomp, N6_OPT and the motor applied first.
#- New startups should apply Drive-Generic-PWMOutput directly.
#- Legacy names N6_PWM_HZ / N6_PWM_ARM are translated here; duty defaults to 50%.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PWMOutput,COMP_S_ID=${N6_SID=${ECMC_EC_SLAVE_NUM}},CH_ID=1,MACROS='FREQUENCY_HZ=${N6_PWM_HZ=2000},DUTY_PERCENT=${N6_PWM_DUTY=50},OUTPUT=1,PWM_ID=0,ARM=${N6_PWM_ARM=0},N6_IO_24V=${N6_IO_24V=0}'"
