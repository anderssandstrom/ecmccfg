
# Beckhoff EL7342 - Channel 1
# Two-wire linear voice coil
# Replace ${ECMC_EC_SLAVE_NUM} with actual EtherCAT slave index

# Maximum current: 700 mA for initial testing
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x01,700,U16)"

# Nominal current: 700 mA
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x02,700,U16)"

# Motor supply voltage (example for 24 V supply)
# Enable ONLY if actual power supply is 24 V
# ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x03,48000,U16)"

# Coil resistance: 19.5 ohm / 0.01 ohm = 1950
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x04,1950,U16)"

# Reduced current in both directions: 700 mA
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x05,700,U16)"
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8020,0x06,700,U16)"

# Monitor motor current in Info Data 1
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8022,0x11,2,U8)"

# Monitor motor coil voltage in Info Data 2
ecmcConfigOrDie "Cfg.EcAddSdoDT(${ECMC_EC_SLAVE_NUM},0x8022,0x19,1,U8)"

