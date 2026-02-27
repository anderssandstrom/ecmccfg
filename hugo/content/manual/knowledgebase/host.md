+++
title = "host / ecmc server"
weight = 17
chapter = false
+++

## Topics
1. [PSI specific](#psi-specific)
2. [ECMC server cfg repository](#ecmc-server-cfg-repository)
3. [Preferred NICs](#preferred-nics)
4. [Latency issues / lost frames](#latency-issues--lost-frames)
5. [EtherCAT rate (EC_RATE)](#ethercat-rate-ec_rate)

### PSI specific
#### ECMC server cfg repository
The repository `ecmc_server_cfg` is used at PSI as a host configuration template for ecmc servers.

Typical deployment location on host:
```bash
/ioc/hosts/<hostname>/cfg
```

Main content:
- `ETHERCATDRVR`: EtherCAT driver selection and network interface mapping (`DEVICE_MODULES="igb generic"` plus optional `LINK_DEVICES`/`LINK_DEVICE_MACS`).
- `AutoStart.sh`: executes startup scripts in `AutoStart/` in lexical order.
- `AutoStart/S00-install-ethercat-drvr`: installs/starts EtherCAT driver package and service (where applicable).
- `AutoStart/S10-performance`: sets CPU governor to `performance` and disables turbo.
- `AutoStart/S10-ecmc-python-venv`: copies the PSI ecmc Python venv to `/tmp` (Debian-version dependent).
- `AutoStart/S10-eth-irq-prio`: sets EtherCAT IRQ thread priority (relevant when generic driver is used).

{{% notice warning %}}
`ecmc_server_cfg` is a template. Always validate and adapt settings for the specific machine, and reboot to apply host-level changes.
{{% /notice %}}

#### iocsh startup
ecmc needs to be started with root privileges (or with a user in the realtime group); otherwise ecmc might segfault.

#### c6025-0010 startup
Need to change boot setting:
* At PSI: make normal Warewulf and PacketFence setup, don't forget the USB dongle.
* Go to boot menu
* Boot menu: Set boot option 1 to "USB stick"
* Advanced->Network stack configuration: Enable network stack and PXE support
* Save and exit

#### No visible slaves
Wrong MAC addresses in the EtherCAT configuration could lead to EtherCAT masters "waiting for devices":
```
dmesg
...
[ 1154.773837] EtherCAT: Requesting master 2...
[ 1154.773839] EtherCAT ERROR 2: Master still waiting for devices!
[ 1169.412719] EtherCAT: Requesting master 1...
[ 1169.412721] EtherCAT ERROR 1: Master still waiting for devices!
[ 1169.518489] EtherCAT: Requesting master 0...
[ 1169.518491] EtherCAT ERROR 0: Master still waiting for devices!
[ 1169.518829] EtherCAT: Requesting master 2...
[ 1169.518830] EtherCAT ERROR 2: Master still waiting for devices!
...
```
Check that the correct MAC addresses are defined for the EtherCAT masters. At PSI the MACs are defined in the `ETHERCATDRVR` file (`/ioc/hosts/<hostname>/cfg/ETHERCATDRVR`).

### Preferred NICs

igb driver (ec_igb):
* Intel Corporation I210 Gigabit Network Connection (rev 03)
* Intel Corporation I350 Gigabit Network Connection (rev 01)

### Latency issues / lost frames

High latency, more than 30% of the EtherCAT cycle time, can result in lost EtherCAT frames, which means data is lost. High latency of the `ecmc_rt` thread can be related to:
1. The generic device driver is used
2. High load on system
3. ...

#### Generic device driver is used
Check which driver is in use by running (on the ecmc server):
```
lsmod | grep ec_
```
If `ec_master` is using the `ec_generic` driver then a switch to the `igb` driver is recommended.

The file `/ioc/hosts/<hostname>/cfg/ETHERCATDRVR` lists the available drivers.

The recommended contents of the `ETHERCATDRVR` file are:
```
DEVICE_MODULES="igb generic"
```
In this case, the system will first try to use the `igb` driver. If not possible, it will fall back to the generic driver.
After editing the file, the host needs to be rebooted in order for the changes to take effect.

#### High load on system

** Reduce sample rate**
Reducing the EtherCAT cycle time is often very efficient when it comes to reducing latency. Do not run ecmc systems faster than needed.
The default ecmc sample rate is 1kHz, which in many cases is not needed.

The sample rate is defined when require ecmccfg (example set to 500Hz, instead of 1kHz):
```
require ecmccfg "EC_RATE=500"
```
{{% notice info %}}
There are some restrictions on the sample rate. Normally, a rate in the range 100Hz-1kHz is a good choice. For other rates, please check the documentation of the slaves in use. See the "EtherCAT rate" heading below for more information.
{{% /notice %}}

** Affinity**
Setting the affinity of the ecmc real-time thread can often improve performance. First check how many cores the controller has.
{{% notice warning %}}
At PSI, core 0 is always isolated, do not move any threads to core 0.
{{% /notice %}}

In order to pin the ecmc thread to a single core, add the following lines to the startup script (after `setAppMode.cmd`):
```
#- go active (create ecmc_rt)
${SCRIPTEXEC} ${ecmccfg_DIR}setAppMode.cmd

#- Set affinity of ecmc_rt (core 5)
epicsThreadSetAffinity ecmc_rt 5
```
If more than one ecmc IOC is running on the server, then make sure the `ecmc_rt` threads run on different cores.

Further tuning might include moving other CPU-intensive threads to dedicated cores, for instance the EPICS thread `cbLow`:
```
afterInit "epicsThreadSetAffinity cbLow 6"
```
{{% notice info %}}
`cbLow` is created at `iocInit`, therefore `epicsThreadSetAffinity` must be executed with the `afterInit` command.
{{% /notice %}}

{{% notice note %}}
The affinity can also be set with the tools accessible in the EPICS module MCoreUtils.
{{% /notice %}}

### EtherCAT rate (EC_RATE)
The default EtherCAT frame rate in ecmc is set to 1kHz. For most applications this is however not needed and can therefore be reduced. A reduced EtherCAT rate reduces the load on the controller. In general, a good value for the frame rate is in the range 100Hz to 1kHz. For motion systems, a frame rate of 100Hz..500Hz is normally enough. Rates outside the 100Hz..1kHz range is normally not a good idea, and some slaves might not support it. However, in special cases both lower and higher rates might be possible and required.

Example: Set rate to 500Hz
```
require ecmccfg "EC_RATE=500"
...
```
For more information see the chapter describing startup.cmd.

As a comparison, TwinCAT default EtherCAT rates are:
* 100Hz for PLC
* 500Hz for motion

#### Lower rates
Issues that could occur in rates below 100Hz:
* triggering of slave watchdogs
* issues with dc clock syncs (DC capable slaves normally performs best with at a rate of at least 500Hz)
* some slaves might not support it

#### Higher rates
Issues that could occur at rates over 1kHz:
* missed frames
* issues with dc clock syncs
* some slaves might not support it.

NOTE: Some slaves might support a high rate but could have built-in signal filters of several ms, which makes sampling at higher frequencies unnecessary.

In order to successfully run an ecmc EtherCAT system at higher rates, some tuning might be needed:
* minimize slave count (and ensure that the slaves support it)
* minimize amount of processing (PLC, motion)
* use a performant host/controller
* use native EtherCAT driver (`igb`, not generic)
* only transfer the needed PVs to EPICS
* affinity: use a dedicated core for the `ecmc_rt` thread and move other high-priority threads to other cores (see "High load on system" above).
* consider use of more than one domain
