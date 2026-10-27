# WARNING: UNTESTED ON HARDWARE
#-d /**
#-d   \brief N6 CSV descriptor for the scaled-position output trial.
#-d   \details Standard N6 mapping plus native 0x6063 position feedback.
#-d   \file
#-d */

#- Reuse the original identity, records, component type and panel.
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcN6-1-1-1-S.cmd

#- Keep four TxPDO assignments: append raw position to existing PDO 0x1a03.
#- Axis control uses this entry when 0x6064 is scaled to 100 full steps/count.
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a03,0x6063,0x00,S32,positionActualRaw01)"
