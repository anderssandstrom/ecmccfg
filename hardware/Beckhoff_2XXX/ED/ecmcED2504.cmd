# WARNING: UNTESTED
# WARNING: NOT WORKING - NEEDS INVESTIGATION
# The INT32 legacy PDO mapping reaches OP and the process-data readbacks follow
# the requested duty/period values, but no PWM output has been observed.
# Use ED2504_F32 for the currently working configuration.
#-d /**
#-d   \brief Hardware configuration for ED2504
#-d   \details Four-channel PWM integer legacy mode with four digital inputs
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "ED2504")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x09c81052")
epicsEnvSet("ECMC_EC_REVISION"           "0x00100000")
epicsEnvSet("ECMC_HW_PANEL"               "ED2504")

ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- Each fixed RxPDO contains U16 pulse width, 16 alignment bits, and a U32
#- period in microseconds (16..1000000 us = 62.5 kHz..1 Hz).
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x11,U16,PWM_Width01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x0000,0x00,U16,PWM_Gap01,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x13,U32,PWM_Period01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x7020,0x11,U16,PWM_Width02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x0000,0x00,U16,PWM_Gap02,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x7020,0x13,U32,PWM_Period02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1640,0x7040,0x11,U16,PWM_Width03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1640,0x0000,0x00,U16,PWM_Gap03,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1640,0x7040,0x13,U32,PWM_Period03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1660,0x7060,0x11,U16,PWM_Width04)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1660,0x0000,0x00,U16,PWM_Gap04,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1660,0x7060,0x13,U32,PWM_Period04)"

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcED2504-common.cmd
