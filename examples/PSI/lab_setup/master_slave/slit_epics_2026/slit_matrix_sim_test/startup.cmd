# Dedicated simulation-only slit acceptance IOC; run from this directory.
# Based on ../slit_matrix/startup_test_sim.cmd; original configuration is untouched.
# Use a separate IOC/PV namespace so the test never shares normal device PVs.
epicsEnvSet("IOC", "${TEST_IOC=SIMSLIT}")
require ecmccfg ${ECMCCFG_TEST_VER=sandst_a} "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000,ECMC_VER=${ECMC_TEST_VER=sandst_a},SIM=1"
on error halt
asynSetTraceMask(${ECMC_ASYN_PORT}, -1, 0x01)
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"

# Only the terminals used by the slit; omit the unrelated test-rack inventory.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
# Brake coils: output 01 = LO, output 02 = HI; 1 releases the brake.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=5,HW_DESC=EL2008"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=9,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=2"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=12,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=24000,R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_ax6_HI.yaml,DRV_SLAVE=12,ENC_SLAVE=12,ENC_CHANNEL=01,M_ID=0"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd "FILE=./cfg/biss-c.yaml,DEV=${IOC},ENC_SID=9,ENC_CH=01"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=14,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,MACROS='I_MAX_MA=1000,I_STDBY_MA=500,U_NOM_MV=48000,R_COIL_MOHM=1230'"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_ax5_LO.yaml,DRV_SLAVE=14,ENC_SLAVE=14,ENC_CHANNEL=01,M_ID=0"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd "FILE=./cfg/biss-c.yaml,DEV=${IOC},ENC_SID=9,ENC_CH=02"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_vax5_YCEN.yaml,AX_ID=12,M_ID=0,DRV_SLAVE=14"
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./cfg/axis_vax6_YGAP.yaml,AX_ID=13,M_ID=0,DRV_SLAVE=14"
# Brake delays are RT cycles (1000 Hz): release after 250 ms, close 200 ms
# before normal amplifier disable. Deliberately long enough to observe via CA.
ecmcConfigOrDie "Cfg.LinkEcEntryToObject(ec0.s5.binaryOutput01,ax5.drv.brake)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeOpenDelayTime(5,250)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeCloseAheadTime(5,200)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeEnable(5,1)"
ecmcConfigOrDie "Cfg.LinkEcEntryToObject(ec0.s5.binaryOutput02,ax6.drv.brake)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeOpenDelayTime(6,250)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeCloseAheadTime(6,200)"
ecmcConfigOrDie "Cfg.SetAxisDrvBrakeEnable(6,1)"
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd "FILE=./cfg/axis_main.plc,INC=./cfg,PLC_MACROS='AX_CEN=12,AX_GAP=13,AX_LO=5,AX_HI=6'"
${SCRIPTEXEC} ${ecmccfg_DIR}addMasterSlaveSM.cmd "NAME=Slit_SM,MST_GRP_NAME=virtualAxes,SLV_GRP_NAME=realAxes"

# Coherent zero-position counter images and ready flags before runtime starts.
# Absolute position = raw/4096 - 1380, so physical zero is raw=5652480.
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.positionActual01,5652480)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.positionActual02,5652480)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.encoderStatus01,4)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.encoderStatus02,4)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s12.driveStatus01,6145)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s14.driveStatus01,6145)"
dbLoadRecords("./test-marker.db", "P=${ECMC_PREFIX}")
