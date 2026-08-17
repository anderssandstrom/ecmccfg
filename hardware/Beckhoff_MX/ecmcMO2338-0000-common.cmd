#- Common PDO configuration for MO2338-0000-1111 and MO2338-0000-1112
#- Both variants use product code 0x812b6c8b and the same PDO mapping.
#- NOTE: On an MO2338-0000-1112, the BO02 LED was observed to remain off even
#- when DOS_Ctrl/DOS-Ctrl-RB bit 1 was set, pin 2 measured 24 V, and all DOS
#- diagnostics were clear. Verify the process-image readback and output voltage;
#- do not use the BO02 LED alone to determine the electrical output state.

#- RX PDO 0x1610: DOS Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7080,0x1,U8,DOS_Ctrl)"
#- DOS_Ctrl B0..B7=Output

#- RX PDO 0x1680: EFU Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1680,0x7100,0x1,U16,EFU_Ctrl)"
#- EFU_Ctrl B0=Enable
#- EFU_Ctrl B1=Control via Process Data
#- EFU_Ctrl B2=Reset
#- EFU_Ctrl B3..B15=gap

#- TX PDO 0x1a00: DIP Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x1,U8,DIP_Stat)"
#- DIP_Stat B0..B7=Input

#- TX PDO 0x1a01: DIP Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6001,0x1,U16,DIP_Stat_02)"
#- DIP_Stat_02 B0=Wirebreak
#- DIP_Stat_02 B1=Power Supply Missing
#- DIP_Stat_02 B2=Wirebreak
#- DIP_Stat_02 B3=Power Supply Missing
#- DIP_Stat_02 B4=Wirebreak
#- DIP_Stat_02 B5=Power Supply Missing
#- DIP_Stat_02 B6=Wirebreak
#- DIP_Stat_02 B7=Power Supply Missing
#- DIP_Stat_02 B8=Wirebreak
#- DIP_Stat_02 B9=Power Supply Missing
#- DIP_Stat_02 B10=Wirebreak
#- DIP_Stat_02 B11=Power Supply Missing
#- DIP_Stat_02 B12=Wirebreak
#- DIP_Stat_02 B13=Power Supply Missing
#- DIP_Stat_02 B14=Wirebreak
#- DIP_Stat_02 B15=Power Supply Missing

#- TX PDO 0x1a10: DOS Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x1,U16,DOS_Stat)"
#- DOS_Stat B0=Overcurrent
#- DOS_Stat B1=Overload
#- DOS_Stat B2=gap
#- DOS_Stat B3=Short to 24V
#- DOS_Stat B4=Power Supply Missing
#- DOS_Stat B5=Overcurrent
#- DOS_Stat B6=Overload
#- DOS_Stat B7=gap
#- DOS_Stat B8=Short to 24V
#- DOS_Stat B9=Power Supply Missing
#- DOS_Stat B10=Overcurrent
#- DOS_Stat B11=Overload
#- DOS_Stat B12=gap
#- DOS_Stat B13=Short to 24V
#- DOS_Stat B14=Power Supply Missing
#- DOS_Stat B15=Overcurrent
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x60b0,0x2,U16,DOS_Stat02)"
#- DOS_Stat02 B0=Overload
#- DOS_Stat02 B1=gap
#- DOS_Stat02 B2=Short to 24V
#- DOS_Stat02 B3=Power Supply Missing
#- DOS_Stat02 B4=Overcurrent
#- DOS_Stat02 B5=Overload
#- DOS_Stat02 B6=gap
#- DOS_Stat02 B7=Short to 24V
#- DOS_Stat02 B8=Power Supply Missing
#- DOS_Stat02 B9=Overcurrent
#- DOS_Stat02 B10=Overload
#- DOS_Stat02 B11=gap
#- DOS_Stat02 B12=Short to 24V
#- DOS_Stat02 B13=Power Supply Missing
#- DOS_Stat02 B14=Overcurrent
#- DOS_Stat02 B15=Overload
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x60e0,0x4,U8,DOS_Stat03)"
#- DOS_Stat03 B0=gap
#- DOS_Stat03 B1=Short to 24V
#- DOS_Stat03 B2=Power Supply Missing
#- DOS_Stat03 B3=Overcurrent
#- DOS_Stat03 B4=Overload
#- DOS_Stat03 B5=gap
#- DOS_Stat03 B6=Short to 24V
#- DOS_Stat03 B7=Power Supply Missing

#- TX PDO 0x1a80: EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6100,0x1,U16,EFU_Stat)"
#- EFU_Stat B0=Warning
#- EFU_Stat B1=Error
#- EFU_Stat B2=Tripped
#- EFU_Stat B3=Enabled
#- EFU_Stat B4..B13=gap
#- EFU_Stat B14..B15=Input Cycle Counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x0000,0x00,U16,EFU_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6100,0x12,F32,EFU_Current)"

#- DC mode: Synchron (FreeRun/SM-Synchron)
ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x0,SYNC_0_CYCLE=0,SYNC_0_SHIFT=0,SYNC_1_CYCLE=0,SYNC_1_SHIFT=0"
