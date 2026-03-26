#-  ecmc hardware config for: EL2535-0002 2Ch. Pulse Width Current Output (24V, 2 A)
#- Standard
#- source ESI file: /Users/sandst_a/sources/Beckhoff_EtherCAT_XML/Beckhoff EL25xx.xml
#- selected slave: type=EL2535-0002, product=0x9e73052, revision=0x170002
#- selected mapping id: M01 of 3

epicsEnvSet("ECMC_EC_HWTYPE"             "EL2535-0002")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x9e73052")
epicsEnvSet("ECMC_EC_REVISION"           "0x170002")
epicsEnvSet("ECMC_HW_PANEL"              "EL2535-XXXX")

#- RX PDO 0x1600: PWM Control Channel 1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x1,U16,PWM01_Ctrl)"
#- PWM01_Ctrl B0=Enable dithering
#- PWM01_Ctrl B1..B4=gap
#- PWM01_Ctrl B5=Enable
#- PWM01_Ctrl B6=Reset
#- PWM01_Ctrl B7..B15=gap
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x7000,0x11,S16,PWM01_Outp)"

#- RX PDO 0x1601: PWM Control Channel 2
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x7010,0x1,U16,PWM02_Ctrl)"
#- PWM02_Ctrl B0=Enable dithering
#- PWM02_Ctrl B1..B4=gap
#- PWM02_Ctrl B5=Enable
#- PWM02_Ctrl B6=Reset
#- PWM02_Ctrl B7..B15=gap
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x7010,0x11,S16,PWM02_Outp)"

#- TX PDO 0x1a00: PWM Status Channel 1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x1,U16,PWM01_Stat)"
#- PWM01_Stat B0=Digital input 1
#- PWM01_Stat B1..B3=gap
#- PWM01_Stat B4=Ready to enable
#- PWM01_Stat B5=Warning
#- PWM01_Stat B6=Error
#- PWM01_Stat B7..B14=gap
#- PWM01_Stat B15=TxPDO Toggle

#- TX PDO 0x1a02: PWM Status Channel 2
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x6010,0x1,U16,PWM02_Stat)"
#- PWM02_Stat B0=Digital input 1
#- PWM02_Stat B1..B3=gap
#- PWM02_Stat B4=Ready to enable
#- PWM02_Stat B5=Warning
#- PWM02_Stat B6=Error
#- PWM02_Stat B7..B14=gap
#- PWM02_Stat B15=TxPDO Toggle
