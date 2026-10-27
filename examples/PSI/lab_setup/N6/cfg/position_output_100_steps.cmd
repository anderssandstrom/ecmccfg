# WARNING: EXPERIMENTAL, VERIFY ON HARDWARE
#- Dedicated to the 200-full-step open-loop N6 lab motor. Load after its motor
#- component, before applyConfig. No writes to 0x3203 or 0x205C are needed.
#- Assumes original feedback-selection masks are zero and INV_DIR=0.

#- Own the output word: disarm first, enable only output 1 at the end.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${N6_SID=${ECMC_EC_SLAVE_NUM}},binaryOutputArray01,0)"

#- Restore the original disabled sensorless interface. Enabling it by setting
#- only a nominal resolution produced 0x7305 (sensor 1 faulty) on this drive.
#- Bench readings on FIR-v2542-B1080909 show the fine open-loop counter in
#- 0x6063 with this interface disabled. Do not enable the sensorless observer.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60E6,0x01,0,4)"

#- Unit 0xAC = full steps, exponent +2: 0x6064 increments every 100 full steps.
#- Only position units change; velocity stays native increments/second.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60A8,0x00,0x02AC0000,4)"

#- Source 0x09 = position 0x6064, divider 1. Low byte 0x10 selects gate bit 16.
#- Subindex 2 = physical output 1, NOT the brake output at subindex 1.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3252,0x02,0x0910,2)"

#- Existing 0x60FE:01 PDO holds bit 16 high. All other output bits stay zero.
#- BO01-Arr=0 disarms; BO01-Arr=65536 rearms. The drive generates the events.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${N6_SID=${ECMC_EC_SLAVE_NUM}},binaryOutputArray01,65536)"
