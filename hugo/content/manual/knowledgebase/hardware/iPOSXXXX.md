+++
title = "Technosoft iPOS4808, iPOS8020"
weight = 24
chapter = false
+++

### iPOSXXXX

Main usecases for Technosoft drives at PSI are for applications requiring:
* High currents
* STO (Safe Torque Off)
* DC motors

#### Configuration
The Technosoft drives are powerful but unfortunately interfacing them is not easy. Many configurations are not exposed as simple CoE, SDOs, so a base configuration in one of the Technosoft softwares needs to be generated and downloaded before the drive is used first time (only needed once). These configurations then contain the main part of the configurations and only small tweaks can be made over SDOs by the EtherCAT master.

These configurations can be loaded in many ways:
* RS232: Technosoft Easy Motion Studio 1, EasySetup
* RS232: Technosoft Easy Motion Studio 2
* CoE: Canbus over EtherCAT, mailbox protocol, (by writing to generic memory interface addresses, not intuitive)
* FoE: File over EtherCAT, mailbox protocol. (`Easy motion studio 2->export->FoE->Complete Config`)

In order to avoid the need to download configs to each drive with local RS232 connection a few generic configurations have been developed and FoE and or CoE configurations have been generated:
1. Open loop stepper, 48V, STO (no support for encoders). Encoders needs to be connected to other EtherCAT slaves like EL5042 or EL5102.
  * Max current, Standby current  and current control parameters can be set over SDO
2. Pure voltage control for brushed DC motors

These configurations files can be found in `ecmccfg/hardware/Technosoft_slaves/config/`.

Note: These configurations are very basic and does not allow for use of all hardware supported by the drive. Not supported:
* encoders (not possible to cfg over SDOs), need a dedicated configuration file for each BISS bit count.
* ...

#### Download config over FoE (File over EtherCAT)

**NOTE: The configuration is only needed to be downloaded once before first use of drive!**

Requirements from Technosoft CoE manual (https://technosoftmotion.com/wp-content/uploads/2019/10/P091.064.EtherCAT.iPOS_.UM.pdf):
1. Find an appropriate configuration in `ecmccfg/hardware/Technosoft_slaves/config/`
2. The FoE file must start with “FOESW_”.
2. The entire FoE file name length must not exceed 14 characters (actually including extension).
3. A Setup data file can be transferred via FoE protocol only in BOOT (manual states different, but mailbox size in OP and PREOP are wrong)
4. The password to program a FoE setup data file is 0. (Seems to not be used)

##### Configure drive (download file, write file):
1. Identify correct bin configuration file (see sub-dirs in "ecmccfg/hardware/Technosoft_slaves/config/")
2. Allow writes in BOOT by write 1 to 0x210c 0x0 `ethercat download -m<masterid> -p<slaveid> 0x210c 0x0 1`
3. Set drive ethercat state to BOOT (even though the manual states download should be made in PREOP, OP or SAFEOP): `ethercat states -m<masterid> -p<slaveid> BOOT`
4. Download file: `ethercat -m<masterid> -p<slaveid> foe_write <filename>`
3. Power cycle of drive is needed in order to load the new config.

##### Example:
Example for:
* Master id: 0
* Slave id:  21
* Config file (binary): "FOESW_OL48.bin"
```
# 2. Allow FoE in state BOOT
ethercat download -m0 -p21 0x210c 0x0 1
# 3a. Set slave into state BOOT
ethercat states -m0 -p21 BOOT
# 3b. Check that slave is in boot state
ethercat slaves
# 4. Download configuration file
ethercat foe_write -m0 -p21 FOESW_OL48.bin
# 5. Now power cycle drive
```
#### Upload file (read file):
**NOTE 1: Normally upload of the configuration is not needed!**

1. You must know the name of the file on the slave
2. `ethercat -m<masterid> -p<slaveid> foe_read <filename> > <output filename>`

**Note: Seems the "-o" or "--output-file" is not working.**

##### Example:
```
ethercat -m0 -p0 foe_read FOESW_8020.bin > test.bin
```

##### Generate new config file in EasyMotion Studio 1:
1. Make your configuration
2. Application->Create EtherCAT FOE File->Setup Only
3. Choose filename and save (note: max 14 chars).
4. Store the file in ecmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/<suitable_file_name>
5. Add a README.md file in cmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/ describing the config:
* Drive type (8020BX-CAT or 4808BX-CAT)
* DC-link voltage (48V)
* Control mode (normally always CSV)
* ...


#### Ecmc example configuration for iPOS4808

```
require ecmccfg "ENG_MODE=1"

#- Note the "_2" in iPOS4808BX_2
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd, "SLAVE_ID=21, HW_DESC=iPOS4808BX_2"
epicsEnvSet("ECMC_EC_SLAVE_NUM_DRIVE",        "$(ECMC_EC_SLAVE_NUM)")

#- NOTE USE HW_DESC = iPOS4808BX_2  (iPOS4808BX is for legacy)

#- Apply component: Oriental motor PKE244A
#- For IPOS4808 some macros are mandatory:
#-  * I_CTRL_GAIN   : Current loop gain
#-  * I_CTRL_INT    : Current loop integrator gain
#-  * I_MAX_MA      : Mandatory if Motor-Generic-2Phase-Stepper is used
#-  * I_STDBY_MA    : Mandatory if Motor-Generic-2Phase-Stepper is used
#- The values can be taken from EasyMotionStudio or by trial and error (BTW, coil resistance and inductance are not used in the iPOS cfgs)
#- After running a tuning test in EasyMotionStudio, a reset is needed (from easymotion studio or over SDO (see motor cfg scripts).)
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=1000,I_STDBY_MA=100,CURR_KP=1.0,CURR_TI=0.26'"

#- #############################################################################
#- AXIS 1
#- The reduced current will be applied automatically by the iPOS4808 (no links needed in axis cfgs)
#- $(SCRIPTEXEC) ($(ecmccfg_DIR)configureAxis.cmd, CONFIG=./cfg/ipos4808_1.ax)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,               DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${ECMC_EC_SLAVE_NUM}"
```
