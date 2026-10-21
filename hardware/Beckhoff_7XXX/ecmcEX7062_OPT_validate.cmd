#- Internal validation; no bus operations before both channels pass.
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_MODE,"'${MODE}'!='CSV' and '${MODE}'!='CSP' and '${MODE}'!='CST'","","#-")
${EX7062_BAD_MODE}ecmcExit Error: MODE must be CSV, CSP or CST
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${TP}'!='0' and '${TP}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: TP must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${INPUTS}'!='0' and '${INPUTS}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: INPUTS must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${ENC2}'!='0' and '${ENC2}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: ENC2 must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${EXT_DIAG}'!='0' and '${EXT_DIAG}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: EXT_DIAG must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${TP_DC}'!='0' and '${TP_DC}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: TP_DC must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_BOOL,"'${AUTOTUNE}'!='0' and '${AUTOTUNE}'!='1'","","#-")
${EX7062_BAD_BOOL}ecmcExit Error: AUTOTUNE must be 0 or 1
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_TP_DC,"${TP_DC}==1 and (${TP}==0 or ${CAP_TP_DC}==0)","","#-")
${EX7062_BAD_TP_DC}ecmcExit Error: TP_DC requires TP=1 and a supported EL/ED7062
#- MO support deliberately retains the known working fixed CSV process image.
ecmcEpicsEnvSetCalcTernary(EX7062_BAD_FIXED,"${FIXED_PDOS}==1 and ('${MODE}'!='CSV' or ${TP}!=1 or ${INPUTS}!=0 or ${ENC2}!=1 or ${DIAG=1}!=1 or ${EXT_DIAG}!=0 or ${TP_DC}!=0)","","#-")
${EX7062_BAD_FIXED}ecmcExit Error: MO7062 OPT requires CSV, TP=1, INPUTS=0 (no digital inputs), ENC2=1, DIAG=1, EXT_DIAG=0 and TP_DC=0
ecmcEpicsEnvSetCalcTernary(EX7062_CSV,"'${MODE}'='CSV'","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_CSP,"'${MODE}'='CSP'","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_CST,"'${MODE}'='CST'","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_TP,"${TP}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_INPUTS,"${INPUTS}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_ENC2,"${ENC2}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_EXT_DIAG,"${EXT_DIAG}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_TP_DC,"${TP_DC}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_AUTOTUNE,"${AUTOTUNE}==1","","#-")
ecmcEpicsEnvSetCalcTernary(EX7062_FOLLOWING,"'${MODE}'='CSP' and ${EXT_DIAG}==1","","#-")
