#-##############################################################################
#- ecRegRead.cmd
#-
#- Read an EtherCAT ESC register during IOC configuration and store the result
#- in an EPICS environment variable.
#-
#- Required arguments:
#-
#-   SLAVE_ID
#-       EtherCAT slave position.
#-
#-   ADDR
#-       EtherCAT ESC register address.
#-       Example: 0x0130
#-
#-   TYPE
#-       Datatype passed to "ethercat reg_read -t".
#-       Example: uint16
#-
#-   ENV_VAR
#-       EPICS environment variable receiving the value.
#-
#- Optional arguments:
#-
#-   FORMAT
#-       HEX (default) or DEC. Selects the hexadecimal or decimal value
#-       from the ethercat integer register read output.
#-
#-   MASTER_ID
#-       EtherCAT master index.
#-       If omitted, no -m option is passed to the ethercat command and the
#-       currently selected/default EtherCAT master is used.
#-
#-
#- Example using default master:
#-
#-   ${SCRIPTEXEC} ecRegRead.cmd, \
#-       "SLAVE_ID=9,ADDR=0x0130,TYPE=uint16,ENV_VAR=MY_REG_VALUE"
#-
#- Example with explicit master:
#-
#-   ${SCRIPTEXEC} ecRegRead.cmd, \
#-       "MASTER_ID=1,SLAVE_ID=9,ADDR=0x0130,TYPE=uint16,ENV_VAR=MY_REG_VALUE"
#-
#- Example returning decimal:
#-
#-   ${SCRIPTEXEC} ecRegRead.cmd, \
#-       "SLAVE_ID=9,ADDR=0x0130,TYPE=uint16,ENV_VAR=MY_REG_VALUE,FORMAT=DEC"
#-
#-##############################################################################

system("${ecmc_DIR}ec_reg_read.sh '${MASTER_ID=${ECMC_EC_MASTER_ID}}' ${SLAVE_ID} ${TYPE} ${ADDR} ${ENV_VAR} ${ECMC_TMP_DIR}ecReg_${SLAVE_ID}.cmd '${FORMAT=HEX}'")

< ${ECMC_TMP_DIR}ecReg_${SLAVE_ID}.cmd
