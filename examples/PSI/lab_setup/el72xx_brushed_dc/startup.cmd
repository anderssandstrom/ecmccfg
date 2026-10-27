##############################################################################
## Example config for EL7041 and EL5042

require ecmccfg sandst_a "ENG_MODE=1,ECMC_VER=v11.2.0_RC1"

require ecb
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "SLAVE_ID=17,HW_DESC=EL7211-9014_OPT, OPT='MODE=CSTCA,INFO2=NONE'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd  "COMP=Motor-Beckhoff-AM8111-XFX0, MACROS='I_MAX_MA=1355'"

# EL7211-9014 experimental brushed-DC setup
# Motor connected U-V, W unconnected
# 48 V DC link
#
# WARNING: unsupported motor topology - start at LOW CURRENT
 
# ------------------------------------------------------------
# Amplifier
# ------------------------------------------------------------
 
# Nominal DC link voltage = 48 V
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x19,48000,4)"
 
# Current values interpreted as RMS
# Bit 0 = 1 for RMS
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x54,1,4)"
 
 
# ------------------------------------------------------------
# Motor
# ------------------------------------------------------------
 
# Max current: 500 mA RMS for initial testing
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x11,500,4)"
 
# Rated current: 500 mA RMS
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x12,500,4)"
 
# Pole pairs: 1
# Mostly irrelevant for our fixed-angle CSTCA experiment
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x13,1,1)"
 
# Commutation offset
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x15,0,2)"
 
# Torque constant
# Leave 0 for initial current-control experiment
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x16,30,4)"
 
# Winding inductance
# DON'T GUESS THIS.
# Unit is 0.1 mH.

# Example ONLY if motor L = 1.0 mH:
# ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x19,30,2)"



