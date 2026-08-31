# TESTED
#- ecmc hardware config for: MS2210-0021-1114
#- EtherCAT power infeed, 24 V DC/10 A and 48 V DC/10 A
#- Source ESI: Beckhoff MSxxxx.xml
epicsEnvSet("ECMC_EC_HWTYPE",        "MS2210-0021-1114")
epicsEnvSet("ECMC_EC_VENDOR_ID",     "0x00000002")
epicsEnvSet("ECMC_EC_PRODUCT_ID",    "0xa4deec8b")
epicsEnvSet("ECMC_EC_REVISION",      "0x010338aa")
epicsEnvSet("ECMC_HW_PANEL"          "${ECMC_EC_HWTYPE}")

#- SM0, TxPDO 0x1a00: packed one-byte power status.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,0,0x1a00,0x6000,0x01,U8,Pwr_Stat)"
#- Pwr_Stat B0..B3=gap, B4=Power Good, B5..B7=gap

#- No mailbox, output PDO, watchdog, or Distributed Clocks mode is specified.
