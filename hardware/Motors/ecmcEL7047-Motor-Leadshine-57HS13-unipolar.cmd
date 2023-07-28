#-d /**
#-d   \brief hardware script for EL7047-Motor-Leadshine-57HS13 (unipolar wiring)
#-d   \details Parmetrization of EL7047 for motor Nanotec Leadshine Tecnology mod. 57HS13 (unipolar wiring)
#-d   \file
#-d */

#- Load common config from EL7041
${SCRIPTEXEC} ${ECMC_CONFIG_ROOT}ecmcEL7041-Motor-Leadshine-57HS13-unipolar.cmd

#- Nominal voltage 48V (unit 10mV)
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0x3,4800,2)"

#- Coil inductance 2.1mH (unit 0.01mH)
ecmcConfigOrDie "Cfg.EcAddSdo(${ECMC_EC_SLAVE_NUM},0x8010,0xA,210,2)"
