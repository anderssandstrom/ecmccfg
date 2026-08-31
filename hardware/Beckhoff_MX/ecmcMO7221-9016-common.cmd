# WARNING: UNTESTED
#- Common PDO and runtime configuration for MO7221-9016-1114 (24 V) and
#- MO7221-9016-1124 (48 V). Their PDO and CoE layouts are identical.

#- This family rejects the optional restore-default write to 0x1011:01.
ecmcFileExist(${ecmccfg_DIR}slaveVerify.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=0"

#- Info data 1: DC link voltage [mV]; Info data 2: PCB temperature [0.1 degC].
#- EcWriteSdo applies them now; EcAddSdo replays them after a slave power loss.
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x39,2,1)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x3A,4,1)"

#- The PDO mapping objects are fixed/read-only, but their SM assignments are
#- writable. Apply the CSV assignment immediately in PREOP so domain entry
#- registration also works after a cold start. The factory RxPDO assignment is
#- 0x1610 + 0x1611 (target position), while CSV requires 0x1612.
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x00,0,1)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x01,0x1610,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x02,0x1612,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x03,0x1616,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C12,0x00,3,1)"

#- Likewise make every predefined fixed TxPDO used below active before entry
#- registration. PDO 0x1a16 is configurable and is added normally afterwards.
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x00,0,1)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x01,0x1a00,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x02,0x1a02,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x03,0x1a10,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x04,0x1a12,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x05,0x1a13,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x06,0x1a14,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x07,0x1a15,2)"
#ecmcConfigOrDie "Cfg.EcWriteSdo(${ECMC_EC_SLAVE_NUM},0x1C13,0x00,7,1)"

#- SM2 outputs: CSV control, target velocity, and torque offset.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7010,0x01,U16,driveControl01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1612,0x7010,0x06,S32,velocitySetpoint01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1616,0x7010,0x0A,S16,torqueOffset01)"

#- SM3 inputs: feedback position/status and drive feedback values.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x11,U32,positionActual01)"
#- Keep the complete fixed 16-bit PDO size: B0..B12 reserved,
#- B13=TxPDO state, B14..B15=input cycle counter. The packed registration is
#- intentional; the firmware does not expose 0x6000:0F for registration.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a02,0x6000,0x0E,U16,feedbackStatus01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6010,0x01,U16,driveStatus01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a12,0x6010,0x07,S32,velocityActual01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a13,0x6010,0x08,S16,torqueActual01)"
#- Info-data PDO maps 0x1a14/0x1a15 are writable, unlike the fixed maps above.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a14,0x6010,0x12,U16,voltageActual01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a15,0x6010,0x13,S16,temperatureActual01)"
#- MO-specific safety diagnostic. This is a non-safety-rated indication:
#- 0=safe_state/STO active, 1=ready_state. PDO 0x1a16 is configurable.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a16,0x9010,0x27,U8,outputStageSafetyState01)"

#- Config FSoE
ecmcFileExist(${ecmccfg_DIR}ecmcMO7221-9016-fsoe.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcMO7221-9016-fsoe.cmd

#- The ECMC slave object now exists; retain the info selections for reconnect.
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x39,2,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x3A,4,1)"

ecmcConfigOrDie "Cfg.EcSetSlaveNeedSDOSettings(${ECMC_EC_SLAVE_NUM},1,1)"

#- ESI DC mode: fixed 62500 ns Sync0; Sync1 completes the application cycle.
ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)
ecmcEpicsEnvSetCalc("ECMC_SYNC_1","${ECMC_TEMP_PERIOD_NANO_SECS}-62500")
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C32,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x1C33,0x2,${ECMC_TEMP_PERIOD_NANO_SECS},4)"
ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x700,SYNC_0_CYCLE=62500,SYNC_0_SHIFT=${SYNC_0_SHIFT=0},SYNC_1_CYCLE=${ECMC_SYNC_1}"

#- Initial peak-current limit; motor configuration should overwrite it.
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8011,0x11,100,4)"

ecmcEpicsEnvSetCalc("ECMC_TEMP_WATCHDOG_1",1000/${ECMC_EC_SAMPLE_RATE=1000}*1000)
ecmcEpicsEnvSetCalc("ECMC_TEMP_WATCHDOG_2",${ECMC_TEMP_WATCHDOG_1}*10)
ecmcConfigOrDie "Cfg.EcSlaveConfigWatchDog(${ECMC_EC_SLAVE_NUM},${ECMC_TEMP_WATCHDOG_1},${ECMC_TEMP_WATCHDOG_2})"

epicsEnvSet(ECMC_EC_STARTUP_DELAY,${ECMC_EC_STARTUP_DELAY_EL72XX=10})
epicsEnvUnset(ECMC_TEMP_PERIOD_NANO_SECS)
epicsEnvUnset(ECMC_SYNC_1)
epicsEnvUnset(ECMC_TEMP_WATCHDOG_1)
epicsEnvUnset(ECMC_TEMP_WATCHDOG_2)
