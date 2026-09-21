#-d /**
#-d   \brief hardware script for PSI_TEST_01
#-d   \details SOES demo Slave from PSI ESI XML
#-d   \author Anders Sandstroem
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "PSI_TEST_01")
epicsEnvSet("ECMC_HW_PANEL"              "PSI_TEST_01")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x00000E44")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x000AB123")

#- verify slave
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

#- =============================================================================
#- SyncManager 2: Outputs
#- =============================================================================
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1400,0x7000,0x01,U32,ledBlinkRate01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1400,0x7000,0x02,U8,ledonoff01)"

#- =============================================================================
#- SyncManager 3: Inputs
#- =============================================================================
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x01,F32,counter01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x02,U32,uptime01)"
