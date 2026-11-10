
# Servotronix CDHD2-0031DEC2
# Firmware: 2.38.6C1.1.19
# PBA voice coil, 8 mm stroke
# Slave 27, master 0 (slave index is relative to master)
#
# Keep drive DISABLED during configuration.

# Motor type: linear
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x2024,0x00,2,U8)"

# Motor continuous current: 0.7 A = 700 mA
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x6075,0x00,700,U32)"

# Motor peak current: 4.0 A = 4000 mA
# Datasheet: 1 second, 4% duty cycle
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x2036,0x00,4000,U32)"

# Maximum current: 1000 = 100% of rated current
# Conservative initial commissioning limit: 0.7 A
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x6073,0x00,1000,U16)"

# Linear motor force constant: 36 N/A
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x2038,0x00,36.0,F32)"

# Motor inductance: 8.24 mH
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x203A,0x00,8.24,F32)"

# Moving motor mass without load: 0.28 kg
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x203D,0x00,0.28,F32)"

# Resistance: 19.5 ohm at 25 C
# Verify accepted range before enabling:
 ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x207F,0x00,19.5,F32)"
