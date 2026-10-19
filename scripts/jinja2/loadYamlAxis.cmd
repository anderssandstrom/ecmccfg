#==============================================================================
# loadYamlAxis.cmd
#-d /**
#-d   \brief Script for loading Axis from yaml file via `jinja2`
#-d   \details adds an Axis, based on a yaml config file
#-d   \author Niko Kivel, Anders Sandström, Felix Maier
#-d   \file
#-d   \param FILE the yaml-file containing the PLC definition
#-d   \param DEV  the device name (optional, defaults to ${IOC}), automatically appended with a `:`
#-d   \param PREFIX  the device PREFIX, will _NOT_ be appended with a `:`
#-d   \note Example calls:
#-d   \note - call
#-d   \code
#-d     ${SCRIPTEXEC} "./loadYamlAxis.cmd" "FILE=./axis1.yaml"
#-d     ${SCRIPTEXEC} "./loadYamlAxis.cmd" "FILE=./axis1.yaml, DEV=foobar"
#-d     ${SCRIPTEXEC} "./loadYamlAxis.cmd" "FILE=./axis1.yaml, PREFIX=MTEST-STEPPER:X:"
#-d   \endcode
#-d */

on error halt
ecmcFileExist("${FILE}",1)
epicsEnvSet(FILE_TEMP_1,${ECMC_TMP_DIR}${FILE}_1)
epicsEnvSet(FILE_TEMP_2,${ECMC_TMP_DIR}${FILE}_2)
epicsEnvSet(FILE_TEMP_3,${ECMC_TMP_DIR}${FILE}_3)
epicsEnvSet(FILE_TEMP_PROFILE,${ECMC_TMP_DIR}${FILE}_profile.yaml)


# step 1: get filename (need to check if filename contains other macros also). Basically run the filename in this iocsh
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_ECB,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_JINJA,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","#-","")
  ${ECMC_YAML_AXIS_ECB}ecb --yaml ${FILE} --action readkey --key plc.file --output ${FILE_TEMP_1}
  ${ECMC_YAML_AXIS_ECB}system '[ ! -s ${FILE_TEMP_1} ] || sed -i "s/^\(.*\)$/epicsEnvSet(ECMC_PLC_FILENAME, \"\1\")\n/" ${FILE_TEMP_1}'
  ${ECMC_YAML_AXIS_ECB}system '[   -s ${FILE_TEMP_1} ] || echo "epicsEnvSet(ECMC_PLC_FILENAME, \"NONE\")\n" >> ${FILE_TEMP_1}'
#- else
  ${ECMC_YAML_AXIS_JINJA}system ". ${ECMC_CONFIG_ROOT}pythonVenv.sh -d ${ECMC_TMP_DIR}; python ${ECMC_CONFIG_ROOT}ecmcPlcGetFileName.py ${FILE} ${FILE_TEMP_1}"
epicsEnvUnset(ECMC_YAML_AXIS_ECB)
epicsEnvUnset(ECMC_YAML_AXIS_JINJA)

# PLC filename with expanded macros:
#- system "cat ${FILE_TEMP_1}"
${SCRIPTEXEC} "${FILE_TEMP_1}"
epicsEnvShow(ECMC_PLC_FILENAME)

#- cleanup
system "rm -rf ${FILE_TEMP_1}"
epicsEnvUnset(FILE_TEMP_1)

# step 2: Set plc.file (write new yaml file)
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_ECB,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_JINJA,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","#-","")
  ${ECMC_YAML_AXIS_ECB}ecb --yaml ${FILE} --action updatekey --key plc.file --value ${ECMC_PLC_FILENAME=} --output ${FILE_TEMP_2}
#- else
  ${ECMC_YAML_AXIS_JINJA}system ". ${ECMC_CONFIG_ROOT}pythonVenv.sh -d ${ECMC_TMP_DIR}; python ${ECMC_CONFIG_ROOT}ecmcPlcSetFileName.py ${FILE} ${FILE_TEMP_2} ${ECMC_PLC_FILENAME=}"
epicsEnvUnset(ECMC_YAML_AXIS_ECB)
epicsEnvUnset(ECMC_YAML_AXIS_JINJA)

ecmcFileExist("${FILE_TEMP_2}",1)

#- cleanup
epicsEnvUnset(ECMC_PLC_FILENAME)


#- Expand optional hardware profiles natively before backend validation.
#- Manual PDO configurations pass through unchanged. Errors halt this script.
ecmcExpandHwProfiles("${FILE_TEMP_2}", "${FILE_TEMP_PROFILE}", "${ECMC_CONFIG_ROOT}hardwareProfiles.json")

#- step 3: parse yaml file
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_ECB,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","","#-")
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_AXIS_JINJA,"'$(ECMC_CFG_TOOL=jinja)'='ecb'","#-","")
  ${ECMC_YAML_AXIS_ECB}ecb --yaml ${FILE_TEMP_PROFILE} --schemafile ${ECMC_CONFIG_ROOT}ecbSchema.json --schema axis --template ${ECMC_CONFIG_ROOT}axis_main.jinja2 --templatedir ${ECMC_CONFIG_ROOT} --output ${FILE_TEMP_3}
#- else
  #- setup python venv and run `plcYamlJinja2.py` must be in the same 'system'-context
  ${ECMC_YAML_AXIS_JINJA}system ". ${ECMC_CONFIG_ROOT}pythonVenv.sh -d ${ECMC_TMP_DIR}; python ${ECMC_CONFIG_ROOT}axisYamlJinja2.py -d ${ECMC_TMP_DIR} -T ${ECMC_CONFIG_ROOT} -D ${FILE_TEMP_PROFILE} -o ${FILE_TEMP_3}"
epicsEnvUnset(ECMC_YAML_AXIS_ECB)
epicsEnvUnset(ECMC_YAML_AXIS_JINJA)

#- cleanup
system "rm -rf ${FILE_TEMP_2}"
epicsEnvUnset(FILE_TEMP_2)
#- Keep expanded YAML for inspection when KEEP_HW_PROFILE=1.
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_PROFILE_REMOVE,"${KEEP_HW_PROFILE=0}=0","","#-")
${ECMC_YAML_PROFILE_REMOVE}system "rm -f ${FILE_TEMP_PROFILE}"
ecmcEpicsEnvSetCalcTernary(ECMC_YAML_PROFILE_SHOW,"${KEEP_HW_PROFILE=0}=0","#-","")
${ECMC_YAML_PROFILE_SHOW}epicsEnvShow(FILE_TEMP_PROFILE)
epicsEnvUnset(ECMC_YAML_PROFILE_REMOVE)
epicsEnvUnset(ECMC_YAML_PROFILE_SHOW)
epicsEnvUnset(FILE_TEMP_PROFILE)

#- set device name, default to ${IOC}
epicsEnvSet("ECMC_PREFIX"      "${PREFIX=${DEV=${IOC}}:}")

#- check for ECMC-format PLC file and load the PLC
ecmcFileExist("${FILE_TEMP_3}",1)
#- system "cat ${FILE_TEMP_3}"
${SCRIPTEXEC} "${FILE_TEMP_3}"

#- cleanup
system "rm -rf ${FILE_TEMP_3}"
epicsEnvUnset(FILE_TEMP_3)


#- reset PREFIX
epicsEnvSet("ECMC_PREFIX"      "${SM_PREFIX}")

ecmcEpicsEnvSetCalc(ECMC_AXIS_COUNT, "$(ECMC_AXIS_COUNT=0)+1")
