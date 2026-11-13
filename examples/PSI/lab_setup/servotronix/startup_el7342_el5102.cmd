
require ecmccfg sandst_a "ENG_MODE=1,MASTER_ID=0,ECMC_VER=sandst_a,EC_RATE=2000"

${SCRIPTEXEC} ${ecmccfg_DIR}setRecordUpdateRate.cmd "RATE_MS=0.5"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,  "SLAVE_ID=15, HW_DESC=EL7342"
epicsEnvSet(DRV_ID,${ECMC_EC_SLAVE_NUM})

# cfg motor
< ./el7342_ch01_voice_coil_cvca35-HF-8.0-CRX.cmd

#- Override check for now
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Generic-Ch-Not-Used,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Generic-Ch-Not-Used,CH_ID=2"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,  "SLAVE_ID=10, HW_DESC=EL5102"
epicsEnvSet(ENC_ID,${ECMC_EC_SLAVE_NUM})

$(SCRIPTEXEC) $(ecmccfg_DIR)loadYamlAxis.cmd     "FILE=./cfg/axis.yaml, DRV_ID=$(DRV_ID),ENC_ID=$(ENC_ID), AX_NAME='Axis1', AX_ID=1"

# Total encoder storke is approxm 83400counts

# CSV: Enabling from panel and then setting velo will result in move (takes some time for current to integrate up):
# c6025a-08> dbpf c6025a-08:m0s027-Drv01-Spd 5000

