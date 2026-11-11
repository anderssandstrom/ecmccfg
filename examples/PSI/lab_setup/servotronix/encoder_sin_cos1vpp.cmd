
# CDHD2 - 1 Vpp Sin/Cos linear encoder
# Firmware 2.38.x
# EtherCAT slave 27
# Drive must be DISABLED

# Primary feedback: analog Sin/Cos 1 Vpp
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x204D,0x00,3,U16)"

# Encoder resolution: lines per motor pitch
# Replace 1000 with actual MENCRES value.
# Do NOT enable until encoder scaling is established.
# ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x608F,0x01,1000,U32)"

# Encoder configuration / index / commutation
# MENCTYPE depends on index and commutation arrangement.
# Do not write a guessed value.
# ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x2029,0x00,VALUE,U16)"

# Optional: automatic Sin/Cos calibration at power-up
# Leave disabled initially; calibrate manually first.
ecmcConfigOrDie "Cfg.EcAddSdoDT(27,0x20BF,0x00,0,U16)"
