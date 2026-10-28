#- Experimental software-PWM test, output 1 / PWM generator 0.
#- Load after N6-1-1-1-S_OPT and motor configuration, before applyConfig.
#- This is fixed-frequency PWM, not position-synchronous triggering.
#- Route 0x12 is listed in the N6 FIR-v2542 Modbus TCP manual v1.2.1;
#- verify support on the EtherCAT FIR-v2542 drive. See README_software_pwm.md.
#- N6_PWM_HZ: 500, 1000, 1500 or 2000 (default 2000), duty fixed at 50%.
#- N6_PWM_ARM: initial output-1 gate 0/1 (default 0).
#- N6_IO_24V: shared I/O voltage 0=5 V (default), 1=24 V/+UB_Logic.

#- Validate all choices before changing any output or queuing SDOs.
ecmcEpicsEnvSetCalcTernary(N6_PWM_BAD,"'${ECMC_EC_COMP_TYPE=}'!='N6'","","#-")
${N6_PWM_BAD}ecmcExit Error: software PWM test requires the current slave to be an N6
ecmcEpicsEnvSetCalcTernary(N6_PWM_BAD,"'|${N6_PWM_HZ=2000}|' in '|500|1000|1500|2000|'","#-","")
${N6_PWM_BAD}ecmcExit Error: N6_PWM_HZ must be 500, 1000, 1500 or 2000
ecmcEpicsEnvSetCalcTernary(N6_PWM_BAD,"'${N6_PWM_ARM=0}'!='0' and '${N6_PWM_ARM=0}'!='1'","","#-")
${N6_PWM_BAD}ecmcExit Error: N6_PWM_ARM must be 0 or 1
ecmcEpicsEnvSetCalcTernary(N6_PWM_BAD,"'${N6_IO_24V=0}'!='0' and '${N6_IO_24V=0}'!='1'","","#-")
${N6_PWM_BAD}ecmcExit Error: N6_IO_24V must be 0 (5 V) or 1 (24 V/+UB_Logic)

#- Only output 1 is changed. Preserve brake bit 0 and output gates 2/3.
ecmcConfigOrDie "Cfg.WriteEcEntryEcPath(ec${ECMC_EC_MASTER_ID=0}.s${ECMC_EC_SLAVE_NUM}.binaryOutputArray01.16,0)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x323A,0x01,${N6_IO_24V=0},1)"
#- Hold PWM inactive while selecting frequency and routing.
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x3260,0x02,0,4)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x3260,0x01,${N6_PWM_HZ=2000},4)"
#- High byte 0x12: PWM 0. Low byte 0x10: gate with 60FE:01 bit 16.
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x3252,0x02,0x1210,2)"
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x3260,0x02,50,4)"
ecmcConfigOrDie "Cfg.WriteEcEntryEcPath(ec${ECMC_EC_MASTER_ID=0}.s${ECMC_EC_SLAVE_NUM}.binaryOutputArray01.16,${N6_PWM_ARM=0})"
epicsEnvUnset(N6_PWM_BAD)
