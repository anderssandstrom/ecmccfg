#- Script to add a slave and load a CPP logic "so" file
#-
#- MACROS:
#    IOC       : IOC prefix 
#-   S_ID      : Slave id of EL1252 (or defined by HW_DESC )
#-   HW_DESC   : Slave type, defaults to EL1252
#-   ASYN_PORT : Asyn port name, defaults to CPP.LOGIC<index>, 
#-               index is a increased by 1 for each loaded CPP logic.


# Add a Slave 
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,         "SLAVE_ID=${S_ID},HW_DESC=${HW_DESC=EL1252}"

# Run some custom CPP logic
${SCRIPTEXEC} ${ecmccfg_DIR}loadCppLogic.cmd,     "ASYN_PORT=${ASYN_PORT=},MACROS='S_ID=${S_ID=4}',REPORT=1, DIR=${${MODULE}_DIR}/lib/${EPICS_HOST_ARCH}/,FILE=lib${MODULE}.so,EPICS_SUBST="

#- Load custom PVs manually
dbLoadTemplate(custom_pvs.subs,     "P=${IOC}:,PORT=CPP.${ASYN_PORT=},S_ID=${S_ID=4},PV=CPP-MY_PORT_${S_ID}")
