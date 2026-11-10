
require ecmccfg sandst_a "ENG_MODE=1,MASTER_ID=1,ECMC_VER=sandst_a"

${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,        "SLAVE_ID=27, HW_DESC=CD02"

# cfg motor
< ./voice_coil_cvca35-HF-8.0-CRX.cmd

# cfg encoder
< ./encoder_sin_cos1vpp.cmd


