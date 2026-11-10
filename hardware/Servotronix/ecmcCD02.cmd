#-  ecmc hardware config for: CD02 EtherCAT Drive (CoE)
#- Implicit default mapping
#- source ESI file: /psi.ch/.nfs-server/nfs32.psi.ch/8210_8214/sandst_a/projects/servotronix/Servotronix_CDHD2_PC0_RV0_12C18003_2_38_6C1_20230605.xml
#- selected slave: type=CD02, product=0x2ec, revision=0x12c18003
#- selected mapping id: M01 of 1

#  Vendor Id:       0x000002e1
#  Product code:    0x000002ec
#  Revision number: 0x12c18003
#  Serial number:   0x00000000

epicsEnvSet("ECMC_EC_HWTYPE"             "CD02")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x000002e1")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x2ec")
epicsEnvSet("ECMC_EC_REVISION"           "0x12c18003")
epicsEnvSet("ECMC_HW_PANEL"              "$(ECMC_EC_HWTYPE)")

#- verify slave
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd

#- RX PDO 0x1600: RxPDO 1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x6040,0x0,U16,driveControl01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x6060,0x0,S8,modesOp01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x607a,0x0,S32,positionSetpoint01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1600,0x60b8,0x0,U16,touchProbeControl01)"

#- RX PDO 0x1601: RxPDO 2
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x60ff,0x0,S32,velocitySetpoint01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1601,0x6071,0x0,S16,torqueSetpoint01)"

#- RX PDO 0x1602: RxPDO 3

#- RX PDO 0x1603: RxPDO 4

#- TX PDO 0x1a00: TxPDO 1
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6041,0x0,U16,driveStatus01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6061,0x0,S8,modesOpDisplay01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6064,0x0,S32,positionActual01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6077,0x0,S16,torqueActual01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x603f,0x0,U16,errorCode01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x60fd,0x0,U32,binaryInputArray01)"

#- TX PDO 0x1a01: TxPDO 2
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x60b9,0x0,U16,touchProbeStatus01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x60ba,0x0,S32,touchProbePosition01)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x606c,0x0,S32,velocityActual01)"

#- TX PDO 0x1a02: TxPDO 3

#- TX PDO 0x1a03: TxPDO 4

#- DC mode: DC-Synchronous
ecmcEpicsEnvSetCalc("ECMC_TEMP_PERIOD_NANO_SECS",1000/${ECMC_EC_SAMPLE_RATE=1000}*1E6)
ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x300,SYNC_0_CYCLE=${ECMC_TEMP_PERIOD_NANO_SECS},SYNC_0_SHIFT=0,SYNC_1_CYCLE=${ECMC_TEMP_PERIOD_NANO_SECS},SYNC_1_SHIFT=0"
epicsEnvUnset(ECMC_TEMP_PERIOD_NANO_SECS)

#- CoE InitCmd startup SDOs from ESI (Mailbox/CoE/InitCmd)
#- NOTE: ESI Transition qualifiers are informational only and kept as comments.
#- NOTE: ecmc startup SDO commands are always applied in transition PREOP -> OP.
#- InitCmd[01] Transition=PS
#-   Comment: Opmode
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x6060,0x0,9,1)"

