#- Compatibility wrapper for the original dedicated lab script.
#- Requires current ecmccomp and N6_OPT/POS_OUT with the motor applied first.
#- New startups should apply Drive-Generic-PositionOutput explicitly.
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PositionOutput,COMP_S_ID=${N6_SID=${ECMC_EC_SLAVE_NUM}},CH_ID=1,MACROS='FULL_STEPS=100,OUTPUT=1,ARM=1'"
