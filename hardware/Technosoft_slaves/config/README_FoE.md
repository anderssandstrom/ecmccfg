# Technosoft EasyMotion Config over FoE (File over EtherCAT)

## Requirements from Technosoft CoE manual (https://technosoftmotion.com/wp-content/uploads/2019/10/P091.064.EtherCAT.iPOS_.UM.pdf):
1. The FoE file must start with “FOESW_”.
2. The entire FoE file name length must not exceed 14 characters (actually including extension).
3. A Setup data file can be transferred via FoE protocol only in OP, PREOP and SAFEOP (BOOTSTRAP rejects download)
4. The password to program a FoE setup data file is 0. (Seems to not be used)

## Configure drive (download file, write file):
1. Identify correct bin configuration file (see sub-dirs in "ecmccfg/hardware/Technosoft_slaves/config/")
2. Allow writes in BOOT by writing `1` to `0x210c 0x0`: `ethercat download -m<masterid> -p<slaveid> 0x210c 0x0 1`
3. Set the drive EtherCAT state to BOOT (even though the manual states that download should be performed in PREOP, OP or SAFEOP): `ethercat states -m<masterid> -p<slaveid> BOOT`
4. Download file: `ethercat -m<masterid> -p<slaveid> foe_write <filename>`
3. Power cycle of drive is needed in order to load the new config.

### Example:
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







## Upload file (read file):
1. You must know the name of the file on the slave
2. ethercat -p<slaveid> foe_read <filename> > <output filename>
Note: Seems the "-o" or "--output-file" is not working.

### Example:
```
ethercat -m0 -p0 foe_read FOESW_8020.bin > test.bin

```

## Generate new config file in EasyMotion Studio:
1. Make your configuration
2. Application->Create EtherCAT FOE File->Setup Only
3. Choose filename and save (note: max 14 chars).
4. Store the file in ecmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/<suitable_file_name>
5. Add a README.md file in cmccfg/hardware/Technosoft_slaves/config/FoE/<suitable_dir_name>/ describing the config:
* Drive type (8020BX-CAT or 4808BX-CAT)
* DC-link voltage (48V)
* Control mode (normally always CSV)
* ...
