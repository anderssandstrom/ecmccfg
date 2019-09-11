#-d /**
#-d   \brief hardware script for EL5002-Encoder-ch2-NJ_LAK12-510
#-d   \details
#-d   \author Anders Sandstroem
#-d   \file
#-d   \note This encoder delivers 33-bit of data:
#-d   \note 32-bit position information
#-d   \note 32-bit position information
#-d   \note 1-bit leading ZERO
#-d   \note WARNING: LSB ist lost --> half the theoretical resolution only!
#-d */

epicsEnvSet("ECMC_EC_SDO_INDEX"               "0x8010")     # CH1=0x8000. CH2=0x8010

#- Call generic config file
${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}ecmcEL5002-Encoder-NJ_LAK12-510.cmd
