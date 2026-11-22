# Simulation-only IOC for hardware profile integration. No physical EtherCAT.
# Run from tests/integration/hardware_profiles/ioc with installed ECMC/ecmccfg.
epicsEnvSet("IOC", "${TEST_IOC=SIMPROFILES}")
require ecmccfg ${ECMCCFG_TEST_VER=sandst_a} "MASTER_ID=0,ENG_MODE=1,EC_RATE=1000,ECMC_VER=${ECMC_TEST_VER=sandst_a},SIM=1"
on error halt
# Only simulated slaves; list all terminal types used in the matrix.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=0,HW_DESC=EK1100"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=2,HW_DESC=EL7031"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=3,HW_DESC=EL7037"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=4,HW_DESC=EL7041-0052"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=5,HW_DESC=EL7047"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=6,HW_DESC=EL7201"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=7,HW_DESC=EL7211-9014_STD"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=8,HW_DESC=EL7221-9014_STD"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=9,HW_DESC=EL7062"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=10,HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=11,HW_DESC=EL5102"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=12,HW_DESC=EL5021"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=13,HW_DESC=EL5101"
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "SLAVE_ID=14,HW_DESC=EL7211-9014_CSP_STD"

# Axes cover family defaults, independent encoder terminals and both modes.
# Explicit per-axis scales are sample values; no motion starts automatically.
# 1: S7031 EL7031 + encoder slave 2; CSV
epicsEnvSet(AX_ID,1)
epicsEnvSet(AX_NAME,S7031)
epicsEnvSet(DRV_SLAVE,2)
epicsEnvSet(ENC_SLAVE,2)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 2: S7037 EL7037 + encoder slave 12; CSV
epicsEnvSet(AX_ID,2)
epicsEnvSet(AX_NAME,S7037)
epicsEnvSet(DRV_SLAVE,3)
epicsEnvSet(ENC_SLAVE,12)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 3: S7041 EL7041-0052 + encoder slave 10; CSV
epicsEnvSet(AX_ID,3)
epicsEnvSet(AX_NAME,S7041)
epicsEnvSet(DRV_SLAVE,4)
epicsEnvSet(ENC_SLAVE,10)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 4: S7047 EL7047 + encoder slave 11; CSV
epicsEnvSet(AX_ID,4)
epicsEnvSet(AX_NAME,S7047)
epicsEnvSet(DRV_SLAVE,5)
epicsEnvSet(ENC_SLAVE,11)
epicsEnvSet(ENC_CH,2)
epicsEnvSet(DRV_CH,2)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 5: S7201 EL7201 + encoder slave 6; CSV
epicsEnvSet(AX_ID,5)
epicsEnvSet(AX_NAME,S7201)
epicsEnvSet(DRV_SLAVE,6)
epicsEnvSet(ENC_SLAVE,6)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 6: S7211 EL7211-9014_STD + encoder slave 7; CSV
epicsEnvSet(AX_ID,6)
epicsEnvSet(AX_NAME,S7211)
epicsEnvSet(DRV_SLAVE,7)
epicsEnvSet(ENC_SLAVE,7)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 7: S7221 EL7221-9014_STD + encoder slave 13; CSV
epicsEnvSet(AX_ID,7)
epicsEnvSet(AX_NAME,S7221)
epicsEnvSet(DRV_SLAVE,8)
epicsEnvSet(ENC_SLAVE,13)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csv.yaml"
# 8: S7062A EL7062 + encoder slave 9; EL7062
epicsEnvSet(AX_ID,8)
epicsEnvSet(AX_NAME,S7062A)
epicsEnvSet(DRV_SLAVE,9)
epicsEnvSet(ENC_SLAVE,9)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_el7062.yaml"
# 9: S7062B EL7062 + encoder slave 9; EL7062
epicsEnvSet(AX_ID,9)
epicsEnvSet(AX_NAME,S7062B)
epicsEnvSet(DRV_SLAVE,9)
epicsEnvSet(ENC_SLAVE,9)
epicsEnvSet(ENC_CH,2)
epicsEnvSet(DRV_CH,2)
epicsEnvSet(ENC_FEEDBACK,incremental)
epicsEnvSet(SWAP_LIMITS,true)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_el7062.yaml"
# 10: S7211C EL7211-9014_CSP_STD + encoder slave 14; CSP
epicsEnvSet(AX_ID,10)
epicsEnvSet(AX_NAME,S7211C)
epicsEnvSet(DRV_SLAVE,14)
epicsEnvSet(ENC_SLAVE,14)
epicsEnvSet(ENC_CH,1)
epicsEnvSet(DRV_CH,1)
epicsEnvSet(ENC_FEEDBACK,openloop)
epicsEnvSet(SWAP_LIMITS,false)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd "FILE=./axis_csp.yaml"
# EL7062 channel 1/2 limits default to binaryInputsXX bits 1/0.
# ECMC uses normally-closed limit polarity, so both bits must be HIGH
# when no end-stop is active. Simulated PDO inputs otherwise start at 0
# and ECMC raises ERROR_MON_BOTH_LIMIT_INTERLOCK once startup finishes.
# Keep hardware-profile links active (including axis 9's swapped links).
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.binaryInputs01,3)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.binaryInputs02,3)"
# Set representative simulated readback/status values without starting motion.
# Do not enable motors or issue move commands in this fixture.
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.driveStatus01,64)"
ecmcConfigOrDie "Cfg.SimSetValue(ec0.s9.driveStatus02,64)"
