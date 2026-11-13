# Maxon A-max 245833 - brushed DC motor
# Servotronix CDHD2, firmware 2.38.x
# EtherCAT slave ${ECMC_EC_SLAVE_NUM}
#
# TEMPLATE ONLY - Do not apply until motor specifications

# Motor type: rotary
# Verify the rotary motor enum value for CDHD2 firmware 2.38.
 ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x2024,0x00,0,U8)"

# Brushed DC motor commutation
# Value 2 is documented for DC/voice-coil operation in
# VarCom, but CoE support must be verified.
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x203E,0x00,2,U16)"

# Continuous motor current, mA
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x6075,0x00,1000,U32)"

# Peak motor current, mA
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x2036,0x00,1500,U32)"

# Torque constant, Nm/A
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x2039,0x00,1,F32)"

# Motor resistance, ohm
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x207F,0x00,2.7,F32)"

# Motor inductance, mH
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x203A,0x00,0.4,F32)"

# Maximum motor speed, rpm
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x6080,0x00,10000,U32)"


