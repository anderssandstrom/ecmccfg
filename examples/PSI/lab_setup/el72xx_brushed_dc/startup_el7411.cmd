##############################################################################
## Example config for EL7041 and EL5042

require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=v11.2.0_RC1"

require ecb
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=16,HW_DESC=EL7411_OPT, OPT='MODE=CSTCA,INFO2=NONE'"

# Maxon 245833 - initial conservative settings

# Max current [mA peak]
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8011,0x11,500,4)"

# Rated current [mA peak]
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8011,0x12,500,4)"

# Pole pairs
# Artificial value for our CSTCA experiment
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8011,0x13,1,1)"

# Torque constant [mNm/A]
# Same provisional value we used on EL7211
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8011,0x16,30,4)"

# Winding inductance
# Same provisional value as previous test
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8011,0x19,15,2)"

# Nominal DC link voltage [mV]
ecmcConfigOrDie "Cfg.EcAddSdo(${EC_SLAVE_NUM},0x8010,0x19,48000,4)"


# EL7411 slave 16 / Maxon brushed DC experiment

# Don't perform commutation finding
ecmcConfigOrDie "Cfg.EcAddSdo(16,0x8010,0x04,0,1)"

# Encoder power OFF
ecmcConfigOrDie "Cfg.EcAddSdo(16,0x8008,0x02,0,1)"


