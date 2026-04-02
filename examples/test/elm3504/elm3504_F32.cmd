
require ecmccfg v11.0.7_RC1, "IOC=$(IOC),EC_RATE=1000,ECMC_VER=v11.0.7_RC1"

# Scalar
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=21, HW_DESC=ELM3504_F32_Scalar"

# Temperature sensor
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x1,44,2)"    # Interface 1K PT1000 4 wires
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x2E,6,2)"    # 0 Extended Range,1 linear, 6 Scalling Celsius ,7 Kelvin
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x16,1,2)"    # Filter 1 FIR Notch 50 Hz
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x1C,1,0)"    # Enable True RMS
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x1B,10,2)"   # True RMS No. of Samples
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8000,0x18,1,2)"    # Decimation Factor

