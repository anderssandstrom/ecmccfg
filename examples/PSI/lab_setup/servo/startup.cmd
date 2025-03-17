##############################################################################
## Example config for ep7211-0034

require ecmccfg v10.1.0_RC1 "ENG_MODE=1,ECMC_VER=sandst_a"

#- ############################################################################
#- Configure hardware
#- ethercat slaves
#- Master0
#- ...
#- 16  0:16  PREOP  +  EP7211-0034 1K. MDP742 Servo-Motor-Endstufe mit OCT (50V, 4,5A 
#- ...

epicsEnvSet ECMC_EC_STARTUP_DELAY_EL72XX 0
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,        "SLAVE_ID=28, HW_DESC=EP7211-0034_ALL_FB"
#- Limit torque to 50% of motor rated torque.  Rated current = 2710mA, set to half I_MAX_MA=1355
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd   "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"
$(SCRIPTEXEC) $(ecmccfg_DIR)loadYamlAxis.cmd     "FILE=./cfg/axis.yaml, DRV_ID=$(ECMC_EC_SLAVE_NUM), AX_NAME='Axis1', AX_ID=1"
