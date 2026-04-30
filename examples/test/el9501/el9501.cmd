
require ecmccfg v11.0.7_RC1 "ECMC_VER=v11.0.7_RC1"

#- Choose voltage range 5 or 20V
#${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=19, HW_DESC=EL9501_5V"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=19, HW_DESC=EL9501_20V"

