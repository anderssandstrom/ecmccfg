
# Add a Slave 
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=${EL1252_SID},HW_DESC=${HW_DESC=EL1252}"

# Run some custom CPP logic
${SCRIPTEXEC} ${ecmccfg_DIR}loadCppLogic.cmd,     "ASYN_PORT=${ASYN_PORT=},MACROS='S_ID=${S_ID=4}',REPORT=1, DIR=${${MODULE}_DIR}/lib/${EPICS_HOST_ARCH}/,FILE=lib${MODULE}.so,EPICS_SUBST="

#- Load custom PVs manually
dbLoadTemplate(custom_pvs.subs,     "P=${IOC}:,PORT=CPP.${ASYN_PORT=},S_ID=${S_ID=4},PV=CPP-MY_PORT")
