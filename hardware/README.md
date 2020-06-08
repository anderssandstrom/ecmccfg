# ECMC Hardware Support
This directory contains hardware configuration files. These files maps links ethercat process image adresses to ecmc names.
The ecmc-names can then be used in configirations of an ecmc system. 

There are basically two types of configuratiojs files:
1. Configuration of the EtherCAT cyclic data transfer by defining the PDO:s, Process Data Objects, (and maybe some SDO:s, depending on slave)
2. Confuguration of the slave behaviour by writing to SDO:s, Service Data Objects. This could be to reconfigure a slave to use a certain sensor (i.e. PT100) or to set a maximum motor current, depending on slave.

## PDO:s

The ethercat data needs to be configured by defining the PDO:s. Each PDO can contain several entries.  Each entry is defined by the ecmc command "Cfg.EcAddEntryDT()" with the following syntax:

```
ecmcConfigOrDie "Cfg.EcAddEntryDT(<slave number>,<vendor id>,<product id>,<direction>,<sync. manager id>,<pdo index>,<entry index>,<entry offset>,<ecmc type>,<ecmc name>,<update in realtime>)"
```
Most of the data needed by the "Cfg.EcAddEntryDT()" command can be obtained by the EtherCAT tool.

### Slave Position
ethercat slaves

### Vendor Id
ethercat slaves -v -p<slave number>

### Product Id
ethercat slaves -v -p<slave number>


Args:
1. Slave number : The bus position of the slave
2. Vendor id    : A vendor specific id
3. Product id   : A product type specific id
4. direction    : set to 1 for outputs and 2 for inputs
5. sync. manager id: Id of sync manager
6. pdo index   : PDO index
7. entry index : Entry index
8. 

#-d /**
#-d   \brief hardware script for EL1014
#-d   \details 4ch digital input, 10micros filter
#-d   \author Anders Sandstroem
#-d   \file
#-d */

epicsEnvSet("ECMC_EC_HWTYPE"             "EL1014")
epicsEnvSet("ECMC_EC_VENDOR_ID"          "0x2")
epicsEnvSet("ECMC_EC_PRODUCT_ID"         "0x03f63052")

ecmcConfigOrDie "Cfg.EcSlaveVerify(0,${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID})"

ecmcConfigOrDie "Cfg.EcAddEntryComplete(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,0,0x1a00,0x6000,0x1,1,BI_1)"
ecmcConfigOrDie "Cfg.EcAddEntryComplete(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,0,0x1a01,0x6010,0x1,1,BI_2)"
ecmcConfigOrDie "Cfg.EcAddEntryComplete(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,0,0x1a02,0x6020,0x1,1,BI_3)"
ecmcConfigOrDie "Cfg.EcAddEntryComplete(${ECMC_EC_SLAVE_NUM},${ECMC_EC_VENDOR_ID},${ECMC_EC_PRODUCT_ID},2,0,0x1a03,0x6030,0x1,1,BI_4)"



Most slaves have this information stored and it can be accessed by using the ethercat tool.
ethercat -p<slave index> -pdos

Example for EL5101 incremental encoder terminal at bus position 3:
```bash
ethercat -p3 pdos
SM0: PhysAddr 0x1800, DefaultSize   48, ControlRegister 0x26, Enable 1
SM1: PhysAddr 0x1880, DefaultSize   48, ControlRegister 0x22, Enable 1
SM2: PhysAddr 0x1000, DefaultSize    3, ControlRegister 0x24, Enable 1
  RxPDO 0x1600 "RxPDO-Map Outputs"
    PDO entry 0x7000:01,  8 bit, "Ctrl"
    PDO entry 0x7000:02, 16 bit, "Value"
SM3: PhysAddr 0x1100, DefaultSize    5, ControlRegister 0x20, Enable 1
  TxPDO 0x1a00 "TxPDO-Map Inputs"
    PDO entry 0x6000:01,  8 bit, "Status"
    PDO entry 0x6000:02, 16 bit, "Value"
    PDO entry 0x6000:03, 16 bit, "Latch"
```

### Simple Slaves
For most simple slaves, like digital input/output and analog input/outputs, the output data from the ethercat tool can be used to generate the ecmc configurations. In some cases however, this information is not correct and then differnent approach is needed (see Complex slaves below).

To define one Data of intresset are:these

1. the syncmanagers SM<sm index>


### Complex Slaves














### Using TwinCAT

4.  apply the configuration
    ```bash
       ${SCRIPTEXEC} ${ecmccfg_DIR}applyConfig.cmd
    ```

5. additional configuration
    ```bash
       ecmcConfigOrDie "Cfg.WriteEcEntryIDString(${ECMC_EC_SLAVE_NUM_DIG_OUT},BO_1,1)"
    ```
6. adding a physical motor axis
   ```bash
      epicsEnvSet("DEV",      "STEST-MYDEVICE")
      ${SCRIPTEXEC} ${ecmccfg_DIR}configureAxis.cmd,            "CONFIG=./cfg/axis_1"
   ```

7. adding a virtual motor axis
   ```bash
      ${SCRIPTEXEC} ${ecmccfg_DIR}configureVirtualAxis.cmd,     "CONFIG=./cfg/axis_11_virt"
   ```

8. adding synchronization
   ```bash
      ${SCRIPTEXEC} ${ecmccfg_DIR}applyAxisSynchronization.cmd, "CONFIG=./cfg/axis_1_sync"
      ${SCRIPTEXEC} ${ecmccfg_DIR}applyAxisSynchronization.cmd, "CONFIG=./cfg/axis_11_sync"
   ```   

9. loading a PLC from file
   ```bash
      ${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd, "PLC_ID=0, FILE=./plc/homeSlit.plc, SAMPLE_RATE_MS=100"
   ```   

4. go active
    ```bash
      ${SCRIPTEXEC} ${ecmccfg_DIR}setAppMode.cmd
    ```
