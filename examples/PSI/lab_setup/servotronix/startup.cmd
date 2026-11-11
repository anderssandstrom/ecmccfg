
require ecmccfg servotronix "ENG_MODE=1,MASTER_ID=0,ECMC_VER=sandst_a"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,  "SLAVE_ID=27, HW_DESC=CD02"

# cfg motor
#< ./voice_coil_cvca35-HF-8.0-CRX.cmd
< ./motor_maxon_a_max_245833.cmd

# cfg encoder
< ./encoder_sin_cos1vpp.cmd

#$(SCRIPTEXEC) $(ecmccfg_DIR)loadYamlAxis.cmd     "FILE=./cfg/axis.yaml, DRV_ID=$(ECMC_EC_SLAVE_NUM), AX_NAME='Axis1', AX_ID=1"



# CSV: Enabling from panel and then setting velo will result in move (takes some time for current to integrate up):
# c6025a-08> dbpf c6025a-08:m0s027-Drv01-Spd 5000

