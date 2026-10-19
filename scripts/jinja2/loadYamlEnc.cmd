#==============================================================================
# loadYamlEnc.cmd

#-d /**
#-d   \brief Script for adding Encoder from yaml file via `jinja2`
#-d   \details adds an encoder to an axis, based on a yaml config file
#-d   \author Anders Sandström
#-d   \file
#-d   \param FILE the yaml-file containing the PLC definition
#-d   \param DEV  the device name (optional, defaults to ${IOC}
#-d   \note Example calls:
#-d   \note - call
#-d   \code
#-d     ${SCRIPTEXEC} "./loadYamlEnc.cmd" "FILE=./enc.yaml"
#-d     ${SCRIPTEXEC} "./loadYamlEnc.cmd" "FILE=./enc.yaml, DEV=foobar"
#-d   \endcode
#-d */

#- halt the ioc startup in case of an error
on error halt

epicsEnvSet(ECMC_IS_LOAD_YAML_ENC, 1)
epicsEnvSet(ECMC_ENC_PROFILE_FILE,${ECMC_TMP_DIR}${FILE}_profile.yaml)
ecmcExpandHwProfiles("${FILE}", "${ECMC_ENC_PROFILE_FILE}", "${ECMC_CONFIG_ROOT}hardwareProfiles.json")

#- setup python venv and run `plcYamlJinja2.py`
#- MUST be in the same 'system'-context!!!
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_ENC_ECB,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_ENC_JINJA,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","#-","")
  ${ECMC_YAML_ENC_ECB}ecb --yaml ${ECMC_ENC_PROFILE_FILE} --schemafile ${ECMC_CONFIG_ROOT}ecbSchema.json --schema encoder --template ${ECMC_CONFIG_ROOT}add_encoder.jinja2 --templatedir ${ECMC_CONFIG_ROOT} --output ${ECMC_TMP_DIR}${FILE}.enc
#- else
  ${ECMC_YAML_ENC_JINJA}system ". ${ECMC_CONFIG_ROOT}pythonVenv.sh -d ${ECMC_TMP_DIR}; python ${ECMC_CONFIG_ROOT}encYamlJinja2.py -d ${ECMC_TMP_DIR} -T ${ECMC_CONFIG_ROOT} -D ${ECMC_ENC_PROFILE_FILE} -o ${ECMC_TMP_DIR}${FILE}.enc"
epicsEnvUnset(ECMC_YAML_ENC_ECB)
epicsEnvUnset(ECMC_YAML_ENC_JINJA)

#- set device name, default to ${IOC}
epicsEnvSet("ECMC_PREFIX"      "${DEV=${IOC}}:")

#- check for ECMC-format PLC file and load the PLC
ecmcFileExist("${ECMC_TMP_DIR}${FILE}.enc",1)
${SCRIPTEXEC} "${ECMC_TMP_DIR}${FILE}.enc"

#- cleanup
system "rm -rf ${ECMC_TMP_DIR}${FILE}.enc"
#- Keep expanded YAML for inspection when KEEP_HW_PROFILE=1.
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_PROFILE_REMOVE,"${KEEP_HW_PROFILE=0}=0","","#-")
${ECMC_YAML_PROFILE_REMOVE}system "rm -f ${ECMC_ENC_PROFILE_FILE}"
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_PROFILE_SHOW,"${KEEP_HW_PROFILE=0}=0","#-","")
${ECMC_YAML_PROFILE_SHOW}epicsEnvShow(ECMC_ENC_PROFILE_FILE)
epicsEnvUnset(ECMC_YAML_PROFILE_REMOVE)
epicsEnvUnset(ECMC_YAML_PROFILE_SHOW)
epicsEnvUnset(ECMC_ENC_PROFILE_FILE)
epicsEnvUnset(ECMC_IS_LOAD_YAML_ENC)
#- reset PREFIX
epicsEnvSet("ECMC_PREFIX"      "${SM_PREFIX}")
