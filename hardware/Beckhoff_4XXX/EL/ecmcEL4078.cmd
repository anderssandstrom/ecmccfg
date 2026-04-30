#-d /**
#-d   \brief hardware script for EL4078
#-d   \details 8 channel analog output 16bit, 2kHz, Float32
#-d   \author Anders Sandström
#-d   \file
#-d   \note SDOS
#-d   \param [out] SDO 0x1011:01 --> 1684107116 \b reset
#-d
#-d   \note TODO: Check if entry index is correct (0x1, it is 0x11 in twincat)
#-d
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL4078")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x0fee3052")

#- verify slave, including reset
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=true"

ecmcFileExist(${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd,1)

#- ############ Config PDOS: Channel 1
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=01,ECMC_PDO=0x1622,ECMC_ENTRY=0x7000,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 2
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=02,ECMC_PDO=0x1646,ECMC_ENTRY=0x7010,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 3
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=03,ECMC_PDO=0x166a,ECMC_ENTRY=0x7020,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 4
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=04,ECMC_PDO=0x168e,ECMC_ENTRY=0x7030,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 5
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=05,ECMC_PDO=0x16b2,ECMC_ENTRY=0x7040,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 6
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=06,ECMC_PDO=0x16d6,ECMC_ENTRY=0x7050,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 7
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=07,ECMC_PDO=0x16fa,ECMC_ENTRY=0x7060,ECMC_ENTRY_OFFSET=0x13"

#- ############ Config PDOS: Channel 8
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogOutput_16bit_F32.cmd "CH_ID=08,ECMC_PDO=0x171e,ECMC_ENTRY=0x7070,ECMC_ENTRY_OFFSET=0x13"

ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a20,0x6000,0x01,U16,status01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a41,0x6010,0x01,U16,status02)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a62,0x6020,0x01,U16,status03)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a83,0x6030,0x01,U16,status04)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1aa4,0x6040,0x01,U16,status05)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1ac5,0x6050,0x01,U16,status06)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1ae6,0x6060,0x01,U16,status07)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1b07,0x6070,0x01,U16,status08)"

#- Default panel
epicsEnvSet("ECMC_HW_PANEL"              "EL4078")
