
# EP7041-4032 appears as 2 slaves:
#  1  0:1  PREOP  +  EP7041-4032 1K. Schrittmotor-Endstufe (50V, 5A)
#  2  0:2  PREOP  +  EP7041-0000 1K. BiSS-C Encoder


require ecmccfg sandst_a "ENG_MODE=1,MASTER_ID=0,ECMC_VER=v11.0.3_RC4"

# EP7041-4032    1Ch Stepper
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=22,HW_DESC=EP7041-4032"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=1500, I_STDBY_MA=1000, U_NOM_MV=48000,SPEED_RANGE=2'"
epicsEnvSet(DRV_SID,${ECMC_EC_SLAVE_NUM})

 EP7041-0000  1Ch BiSS-C Encoder, RLS-LA11
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EP7041-0000"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
epicsEnvSet(ENC_SID,${ECMC_EC_SLAVE_NUM})

${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,          DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${DRV_SID}, ENC_SID=${ENC_SID}, ENC_CH=01"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd,    "FILE=./cfg/enc_open_loop.yaml, DEV=${IOC}, ENC_SID=${DRV_SID}"

