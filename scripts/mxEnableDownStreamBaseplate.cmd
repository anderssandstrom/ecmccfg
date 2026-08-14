#==============================================================================
#- mxEnableDownStreamBaseplate.cmd
#- Arguments:
#-d /**
#-d   \brief Enables the downstream Beckhoff MX-System baseplate.
#-d   \details Sets port 3 of the MB1120 backplane junction to Auto and can
#-d            list the slaves before and after the change.
#-d   \file
#-d   \param MB1120_SID (optional) MB1120 slave position, defaults to 10
#-d   \param MASTER_ID (optional) EtherCAT master ID, defaults to
#-d                    ECMC_EC_MASTER_ID or 0
#-d   \param ECMC_EC_TOOL_PATH (optional) EtherCAT command path set by
#-d                            startup.cmd; defaults to
#-d                            /opt/etherlab/bin/ethercat
#-d   \param REPORT (optional) List EtherCAT slaves before and after the
#-d                         register write when greater than 0, defaults to 0
#-d   \param RESCAN_DELAY (optional) Delay in seconds before rescanning,
#-d                              defaults to 3
#-d   \note This script must only be executed before addMaster.cmd claims the
#-d         EtherCAT master.
#-d */

ecmcEpicsEnvSetCalcTernary(MX_BASEPLATE_REPORT, "${REPORT=0}>0", "", "#-")

${MX_BASEPLATE_REPORT}system "${ECMC_EC_TOOL_PATH=/opt/etherlab/bin/ethercat} slaves -m${MASTER_ID=${ECMC_EC_MASTER_ID=0}}"
system "${ECMC_EC_TOOL_PATH=/opt/etherlab/bin/ethercat} reg_write -m${MASTER_ID=${ECMC_EC_MASTER_ID=0}} -p${MB1120_SID=10} -e -t uint32 0x0100 0x00070001"
system "sleep ${RESCAN_DELAY=3}"
system "${ECMC_EC_TOOL_PATH=/opt/etherlab/bin/ethercat} rescan -m${MASTER_ID=${ECMC_EC_MASTER_ID=0}}"
${MX_BASEPLATE_REPORT}system "${ECMC_EC_TOOL_PATH=/opt/etherlab/bin/ethercat} slaves -m${MASTER_ID=${ECMC_EC_MASTER_ID=0}}"

epicsEnvUnset(MX_BASEPLATE_REPORT)
