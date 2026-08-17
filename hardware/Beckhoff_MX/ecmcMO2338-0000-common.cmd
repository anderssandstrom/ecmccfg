#- Common PDO configuration for MO2338-0000-1111 and MO2338-0000-1112
#- Both variants use product code 0x812b6c8b and the same PDO mapping.
#- NOTE: On an MO2338-0000-1112, the BO02 LED was observed to remain off even
#- when BO_Arr/BO-Arr-RB bit 1 was set, pin 2 measured 24 V, and all BO
#- diagnostics were clear. Verify the process-image readback and output voltage;
#- do not use the BO02 LED alone to determine the electrical output state.

#- RX PDO 0x1610: BO Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1610,0x7080,0x1,U8,BO_Arr)"
#- BO_Arr B0..B7=Output

#- RX PDO 0x1680: EFU Outputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},1,2,0x1680,0x7100,0x1,U16,EFU_Ctrl)"
#- EFU_Ctrl B0=Enable
#- EFU_Ctrl B1=Control via Process Data
#- EFU_Ctrl B2=Reset
#- EFU_Ctrl B3..B15=gap

#- TX PDO 0x1a00: BI Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a00,0x6000,0x1,U8,BI_Arr)"
#- BI_Arr B0..B7=Input

#- TX PDO 0x1a01: BI Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a01,0x6001,0x1,U16,BI_Stat)"
#- BI_Stat B0=Wirebreak
#- BI_Stat B1=Power Supply Missing
#- BI_Stat B2=Wirebreak
#- BI_Stat B3=Power Supply Missing
#- BI_Stat B4=Wirebreak
#- BI_Stat B5=Power Supply Missing
#- BI_Stat B6=Wirebreak
#- BI_Stat B7=Power Supply Missing
#- BI_Stat B8=Wirebreak
#- BI_Stat B9=Power Supply Missing
#- BI_Stat B10=Wirebreak
#- BI_Stat B11=Power Supply Missing
#- BI_Stat B12=Wirebreak
#- BI_Stat B13=Power Supply Missing
#- BI_Stat B14=Wirebreak
#- BI_Stat B15=Power Supply Missing

#- TX PDO 0x1a10: BO Diagnosis
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x6080,0x1,U16,BO_Stat01)"
#- BO_Stat01 B0=Ch1 Overcurrent
#- BO_Stat01 B1=Ch1 Overload
#- BO_Stat01 B2=Ch1 gap
#- BO_Stat01 B3=Ch1 Short to 24V
#- BO_Stat01 B4=Ch1 Power Supply Missing
#- BO_Stat01 B5=Ch2 Overcurrent
#- BO_Stat01 B6=Ch2 Overload
#- BO_Stat01 B7=Ch2 gap
#- BO_Stat01 B8=Ch2 Short to 24V
#- BO_Stat01 B9=Ch2 Power Supply Missing
#- BO_Stat01 B10=Ch3 Overcurrent
#- BO_Stat01 B11=Ch3 Overload
#- BO_Stat01 B12=Ch3 gap
#- BO_Stat01 B13=Ch3 Short to 24V
#- BO_Stat01 B14=Ch3 Power Supply Missing
#- BO_Stat01 B15=Ch4 Overcurrent
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x60b0,0x2,U16,BO_Stat02)"
#- BO_Stat02 B0=Ch4 Overload
#- BO_Stat02 B1=Ch4 gap
#- BO_Stat02 B2=Ch4 Short to 24V
#- BO_Stat02 B3=Ch4 Power Supply Missing
#- BO_Stat02 B4=Ch5 Overcurrent
#- BO_Stat02 B5=Ch5 Overload
#- BO_Stat02 B6=Ch5 gap
#- BO_Stat02 B7=Ch5 Short to 24V
#- BO_Stat02 B8=Ch5 Power Supply Missing
#- BO_Stat02 B9=Ch6 Overcurrent
#- BO_Stat02 B10=Ch6 Overload
#- BO_Stat02 B11=Ch6 gap
#- BO_Stat02 B12=Ch6 Short to 24V
#- BO_Stat02 B13=Ch6 Power Supply Missing
#- BO_Stat02 B14=Ch7 Overcurrent
#- BO_Stat02 B15=Ch7 Overload
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a10,0x60e0,0x4,U8,BO_Stat03)"
#- BO_Stat03 B0=Ch7 gap
#- BO_Stat03 B1=Ch7 Short to 24V
#- BO_Stat03 B2=Ch7 Power Supply Missing
#- BO_Stat03 B3=Ch8 Overcurrent
#- BO_Stat03 B4=Ch8 Overload
#- BO_Stat03 B5=Ch8 gap
#- BO_Stat03 B6=Ch8 Short to 24V
#- BO_Stat03 B7=Ch8 Power Supply Missing

#- TX PDO 0x1a80: EFU Inputs
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6100,0x1,U16,EFU_Stat)"
#- EFU_Stat B0=Warning
#- EFU_Stat B1=Error
#- EFU_Stat B2=Tripped
#- EFU_Stat B3=Enabled
#- EFU_Stat B4..B13=gap
#- EFU_Stat B14..B15=Input Cycle Counter
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x0000,0x00,U16,EFU_Gap,0)"
ecmcConfigOrDie "Cfg.EcAddEntryDT(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,3,0x1a80,0x6100,0x12,F32,EFU_Curr)"

#- DC mode: Synchron (FreeRun/SM-Synchron)
ecmcFileExist(${ecmccfg_DIR}applySlaveDCconfig.cmd,1)
${SCRIPTEXEC} ${ecmccfg_DIR}applySlaveDCconfig.cmd "ASSIGN_ACTIVATE=0x0,SYNC_0_CYCLE=0,SYNC_0_SHIFT=0,SYNC_1_CYCLE=0,SYNC_1_SHIFT=0"
