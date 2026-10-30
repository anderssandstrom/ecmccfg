#-d /**
#-d   \brief hardware script for EL7201
#-d   \details EL7201 Servo terminal with resolver feedback
#-d   \author Anders Sandstroem
#-d   \file
#-d   \param WATCHDOG_DIVIDER Watchdog divider, default 2498 (100 us tick)
#-d   \param WATCHDOG_INTERVALS Watchdog intervals, default 1000 (100 ms)
#-d   \note SDOS
#-d   \param [out] SDO 0x1011:01 --> 1684107116 \b reset
#-d */

#- ###########################################################
#- ############ Information:
#-  Description: EL7201 Servo terminal with resolver feedback
#-
#-  Note: The sync mode can not be written to in newer firmwares:
#-        (0x1C32,0x1,0x1C33,0x1). So then these lines below needs
#-        to be removed or commented out.
#-        The log will then show error like:
#-           EtherCAT ERROR 0-46: SDO download 0x1C32:01 (2 bytes) aborted.
#-           EtherCAT ERROR 0-46: SDO abort message 0x06090030: "Value range of parameter exceeded".
#-           EtherCAT ERROR 0-46: SDO configuration failed.
#-
#- ###########################################################

epicsEnvSet("ECMC_EC_HWTYPE"             "EL7201")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x1c213052")
epicsEnvSet("ECMC_EC_COMP_TYPE"          "EL7201_RES")

#- verify slave, including reset
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=true"

#- common PDOs for CSV
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcEX72XX_CSV.cmd

#- ############ Distributed clocks config EL7201:
#- ECMC_EC_SAMPLE_RATE must match the master rate before loading this script.
#- Trial zero Sync0 shift for intermittent PLL errors during startup.
#- At 500 Hz: Sync0 period = 2000000 ns, shift = 0 ns.

#- NOTE important the sync 1 period needs to be 0!
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x700,SYNC_0_SHIFT=${SYNC_0_SHIFT=0}"

#- applySlaveDCconfig.cmd unsets the period; restore it for the cycle-time SDOs.
ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)

# Peak current (to be overwritten by motor config)
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x11,1000,4)"

#- Beckhoff default: (2498 + 2) * 40 ns * 1000 = 100 ms.
#- Keep watchdog timing independent of the EtherCAT sample rate.
ecmcConfigOrDie "Cfg.EcSlaveConfigWatchDog(${ECMC_EC_SLAVE_NUM},${WATCHDOG_DIVIDER=2498},${WATCHDOG_INTERVALS=1000})"

#- Sync mode
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x1,3,2)"
#- Cycle time
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"
#- Sync mode
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x1,3,2)"
#- Cycle time
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"

epicsEnvUnset(ECMC_TEMP_PERIOD_NANO_SECS)
