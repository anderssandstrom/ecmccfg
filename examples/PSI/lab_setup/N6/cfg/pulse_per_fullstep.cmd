# WARNING: ORDER-CORRECTED DIAGNOSTIC TRIAL, NOT YET VERIFIED
#- Previous revision wrote 0x3203:01=0 before enabling the interface, so its
#- repeated abort could have occurred before the interface-enable writes.
#- This version writes 0x3203:01 exactly once, after configuring interface 1.
#- Initial 0x3203:01=8 write failed while 0x60E6:01 was zero (disabled).
#- Do not bypass a rejected source write; see README.md for test history.
#- N6 FIR-v2542, 200-full-step open-loop motor; load after applyComponent
#- and before applyConfig, with the drive disabled. N6_SID is the slave.
#- Candidate ratio: 1 pulse per 16384 source increments = 1 full step IF
#- the pulse generator uses the same native resolution as positionActual01.
#- Verify source, channel assignment and pulse count on hardware (README.md).

#- Hold both pulse-generator output gates low during setup.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${N6_SID=${ECMC_EC_SLAVE_NUM}},binaryOutputArray01,0)"

#- Queue SDOs for startup/reconnection. First suppress any saved generation
#- ratio and disable the free-running source used when no feedback is selected.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x03,0,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x01,0,2)"

#- Replace saved selections for this OPEN-LOOP example: bits 0..2 stay zero
#- (original position/velocity selection masks). Do not write interface 1
#- until its resolution is configured: even a zero write may be rejected
#- while that interface is disabled. Its single selection write is below.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x02,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x03,0,1)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x04,0,1)"

#- Reported 0x60E6:01=0 disables interface 1. Set its nominal native resolution
#- for this 200-full-step motor: (200/4 pole pairs) * 65536 = 3276800 incr/rev.
#- These are U32 fields. Do not use this value for a different motor setup.
#- 0x3202 stays at zero (open-loop); no unit or motor-model settings are changed.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60EB,0x01,1,4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x60E6,0x01,3276800,4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3203,0x01,8,1)"

#- Clock/direction (A/B), denominator 16384; all 0x205C fields are S16.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x02,1,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x04,16384,2)"

#- Source 0x20 = pulse generator. Subindices 2/3 are physical outputs 1/2,
#- gated by bits 16/17 of the EXISTING 0x60FE:01 PDO. Subindex 1 is brake.
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3252,0x02,0x2010,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x3252,0x03,0x2011,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${N6_SID=${ECMC_EC_SLAVE_NUM}},0x205C,0x03,1,2)"

#- The FIR-v2508 N6 dictionary lists only 0x3250:01. Do not queue the
#- undocumented 0x3250:08 enable from the manual's generic routing example.
#- Arm outputs 1/2 (0x00030000); other output bits remain zero. Writing the
#- existing BO01-Arr record to 0 disarms both. This example owns the output word.
ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${N6_SID=${ECMC_EC_SLAVE_NUM}},binaryOutputArray01,196608)"
