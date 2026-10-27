#- Experimental drive-side pulse generator; see README.md before use.
#- Order-corrected diagnostic trial: a single 0x3203:01 write follows interface
#- setup. Earlier trials aborted at that object; see README.md for details.
require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=sandst_a,MASTER_ID=1"
require ecmccomp sandst_a

#- Reuse the original PDOs. PINI=0 avoids a record initialization write
#- overwriting the output-enable word initialized by the pulse setup.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "HW_DESC=N6-1-1-1-S,MACROS='PINI=0'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,CH_ID=1,MACROS='I_MAX_MA=400,I_STDBY_MA=100,STEPS=200,INV_DIR=0'"
epicsEnvSet(DRV_SID,$(ECMC_EC_SLAVE_NUM))

${SCRIPTEXEC} ./cfg/pulse_per_fullstep.cmd "N6_SID=${DRV_SID}"

#- Original 0x6064 position and native scaling are retained.
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd, "FILE=./cfg/axis.yaml,DEV=${IOC},AX_NAME=M1,AXIS_ID=1,DRV_SID=${DRV_SID},ENC_SID=${DRV_SID},ENC_CH=01"
