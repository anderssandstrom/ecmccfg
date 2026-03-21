+++
title = "Technosoft iPOS4808, iPOS8020"
weight = 24
chapter = false
+++

## Scope
Use this page for Technosoft iPOS drive setup, especially FoE-based base
configuration and the PSI-supported starter configurations.

## iPOSXXXX

Main use cases for Technosoft drives at PSI are applications requiring:
* high currents
* STO (Safe Torque Off)
* DC motors

### Configuration
Technosoft drives are powerful, but they are not especially simple to integrate.
Many settings are not exposed as normal CoE SDOs, so a base configuration needs
to be created in one of the Technosoft tools and downloaded before the drive is
used for the first time. That step is normally only needed once. These base
configurations contain most of the setup, and only smaller adjustments can
later be made over SDOs from the EtherCAT master.

These configurations can be transferred in several ways:
* RS232: Technosoft Easy Motion Studio 1, EasySetup
* RS232: Technosoft Easy Motion Studio 2
* CoE: CAN bus over EtherCAT, mailbox protocol (by writing to generic memory interface addresses; not intuitive)
* FoE: File over EtherCAT, mailbox protocol (`Easy Motion Studio 2 -> Export -> FoE -> Complete Config`)

To avoid downloading a configuration to each drive over local `RS232`, a few
generic configurations have been developed and exported via `FoE` and/or `CoE`:
1. Open-loop stepper, 48V, STO (no support for encoders). Encoders need to be connected to other EtherCAT slaves like EL5042 or EL5102.
  * Max current, standby current, and current-control parameters can be set over SDO.
2. Pure voltage control for brushed DC motors

These configuration files can be found in `ecmccfg/hardware/Technosoft_slaves/config/`.

These configurations are intentionally basic and do not expose all hardware
features supported by the drive. For example, the following is not covered:
* encoders, which need dedicated configuration files for each BiSS bit count and cannot realistically be configured only over SDOs
* ...

### Download config over FoE (File over EtherCAT)

**NOTE: The configuration normally only needs to be downloaded once, before the first use of the drive.**

Requirements from Technosoft CoE manual (`https://technosoftmotion.com/wp-content/uploads/2019/10/P091.064.EtherCAT.iPOS_.UM.pdf`):
1. Find an appropriate configuration in `ecmccfg/hardware/Technosoft_slaves/config/`
2. The FoE file must start with “FOESW_”.
3. The entire FoE file name length must not exceed 14 characters (including extension).
4. A setup data file can be transferred via FoE protocol only in BOOT (manual states differently, but mailbox size in OP and PREOP is wrong).
5. The password to program a FoE setup data file is `0` and appears not to be used in practice.

#### Configure drive (download file, write file)
1. Identify the correct binary configuration file in `ecmccfg/hardware/Technosoft_slaves/config/`.
2. Allow writes in BOOT by writing `1` to `0x210c 0x0`: `ethercat download -m<masterid> -p<slaveid> 0x210c 0x0 1`
3. Set drive EtherCAT state to BOOT (even though the manual states download should be made in PREOP, OP or SAFEOP): `ethercat states -m<masterid> -p<slaveid> BOOT`
4. Download file: `ethercat -m<masterid> -p<slaveid> foe_write <filename>`
5. Power-cycle the drive so the new configuration is loaded.

#### Example
Example:
* Master id: 0
* Slave id:  21
* Config file (binary): "FOESW_OL48.bin"
```bash
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
### Upload file (read file)
**NOTE 1: Normally upload of the configuration is not needed!**

1. You must know the name of the file on the slave
2. `ethercat -m<masterid> -p<slaveid> foe_read <filename> > <output filename>`

**Note: `-o` or `--output-file` does not appear to work here.**

#### Example
```bash
ethercat -m0 -p0 foe_read FOESW_8020.bin > test.bin
```

#### Generate new config file in EasyMotion Studio 1
1. Create the configuration in EasyMotion Studio.
2. Select `Application -> Create EtherCAT FOE File -> Setup Only`.
3. Choose filename and save (note: max 14 chars).
4. Store the file in `ecmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/<suitable_file_name>`
5. Add a `README.md` file in `ecmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/` describing the config:
* Drive type (8020BX-CAT or 4808BX-CAT)
* DC-link voltage (48V)
* Control mode (normally always CSV)
* ...


### ECMC Example Configuration for iPOS4808

```bash
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
#- The values can be taken from EasyMotionStudio or by trial and error (coil resistance and inductance are not used in the iPOS cfgs)
#- After running a tuning test in EasyMotionStudio, a reset is needed (from Easy Motion Studio or over SDO; see motor cfg scripts).
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper,  MACROS='I_MAX_MA=1000,I_STDBY_MA=100,CURR_KP=1.0,CURR_TI=0.26'"

#- #############################################################################
#- AXIS 1
#- The reduced current will be applied automatically by the iPOS4808 (no links needed in axis cfgs)
#- $(SCRIPTEXEC) ($(ecmccfg_DIR)configureAxis.cmd, CONFIG=./cfg/ipos4808_1.ax)
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlAxis.cmd,   "FILE=./cfg/axis.yaml,               DEV=${IOC}, AX_NAME=M1, AXIS_ID=1, DRV_SID=${ECMC_EC_SLAVE_NUM}"
```

## Related Pages
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
- [motion configuration]({{< relref "/manual/motion_cfg/_index.md" >}})
