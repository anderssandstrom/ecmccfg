require ecmccfg v11.2.0_RC1 "ENG_MODE=1,MASTER_ID=0,ECMC_VER=v11.2.0_RC1"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=35,HW_DESC=EL7211-9014_STD"
#- Limit torque to 50% of motor rated torque.  Rated current = 2710mA, set to half I_MAX_MA=1355
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=36,HW_DESC=EL7211-9014_OPT, OPT='MODE=CST'"
#- Limit torque to 50% of motor rated torque.  Rated current = 2710mA, set to half I_MAX_MA=1355
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "HW_DESC=EL7211-9014_OPT, OPT='MODE=CSV'"
#- Limit torque to 50% of motor rated torque.  Rated current = 2710mA, set to half I_MAX_MA=1355
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "HW_DESC=EL7211-9014_OPT, OPT='MODE=CSP'"
#- Limit torque to 50% of motor rated torque.  Rated current = 2710mA, set to half I_MAX_MA=1355
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"

