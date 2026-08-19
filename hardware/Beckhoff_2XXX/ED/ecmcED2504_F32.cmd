# WARNING: UNTESTED
#-d /**
#-d   \brief Hardware configuration for ED2504_F32
#-d   \details Four-channel PWM REAL32 duty/frequency output with four digital inputs
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "ED2504_F32")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x09c81052")
epicsEnvSet("ECMC_EC_REVISION"           "0x00100000")
epicsEnvSet("ECMC_HW_PANEL"               "ED2504_F32")

#- Verify slave identity. RESET is intentionally disabled: this new terminal has
#- no field experience yet and its factory modular configuration is required.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- Factory module assignment (0xF030):
#- odd slots  = 0x001009c8, PWM duty cycle + frequency (REAL32)
#- even slots = 0x002009c8, digital input
#- The corresponding PDO mappings are read-only; register the existing maps.

#- Select PWM_OUT_REAL32_DI explicitly for all four channels.
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0xF030,0x01,0x001009c8,4)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0xF030,0x03,0x001009c8,4)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0xF030,0x05,0x001009c8,4)"
ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0xF030,0x07,0x001009c8,4)"

#- SM2: channel PWM duty cycle [0..1] and frequency [Hz].
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7001,0x12,F32,PWM_Duty01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7001,0x13,F32,PWM_Freq01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x7021,0x12,F32,PWM_Duty02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1620,0x7021,0x13,F32,PWM_Freq02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1640,0x7041,0x12,F32,PWM_Duty03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1640,0x7041,0x13,F32,PWM_Freq03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1660,0x7061,0x12,F32,PWM_Duty04)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1660,0x7061,0x13,F32,PWM_Freq04)"

${SCRIPTEXEC} ${ecmccfg_DIR}ecmcED2504-common.cmd
