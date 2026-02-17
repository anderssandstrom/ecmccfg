#-d /**
#-d   \brief hardware script for EL3202-0010
#-d   \details 2 channel PT100 temperature sensor input  (selectable range, high-precision)
#-d   \author Anders Sandstroem
#-d   \file
#-d   \note SDOS
#-d   \param [out] SDO 0x1011:01 --> 1684107116 \b reset
#-d   \note Range: -200…+850°C (Pt); -60…+250°C (Ni); -200…+320°C (high-precision)
#-d */

#- ###########################################################
#- ############ Information:
#-  Description: 2 channel PT100 temperature sensor input  (selectable range, high-precision)
#-
#-  Bits: 16
#-  Connection: 4-wire
#-
#- ###########################################################

epicsEnvSet("ECMC_EC_HWTYPE"             "EL3202-0010")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x0c823052")

#- verify slave, including reset
${SCRIPTEXEC} ${ecmccfg_DIR}slaveVerify.cmd "RESET=true"

#- analog input Ch1
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogInput_16bit.cmd "CH_ID=01,ECMC_PDO=0x1a00,ECMC_ENTRY=0x6000"
#- analog input Ch2
${SCRIPTEXEC} ${ecmccfg_DIR}ecmcAnalogInput_16bit.cmd "CH_ID=02,ECMC_PDO=0x1a01,ECMC_ENTRY=0x6010"

#- Default panel
epicsEnvSet("ECMC_HW_PANEL"              "Ex3xx2")
