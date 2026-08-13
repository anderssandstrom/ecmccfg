+++
title = "startup.cmd"
weight = 11
chapter = false
+++

## startup.cmd
startup.cmd takes the following arguments:
```
 Arguments
 [optional]
 ECMC_VER          = 9.5.4
 EthercatMC_VER    = 3.0.2 (obsolete)
 INIT              = initAll
 MASTER_ID         = 0 <-- put negative number to disable master, aka non ec-mode
 SCRIPTEXEC        = iocshLoad
 NAMING            = mXsXXX (default), ClassicNaming, ESSnaming
 EC_RATE           = 1000
 MODE              = FULL / DAQ
    FULL:  Init ecmc with support for both motion and DAQ (DEFAULT)
    DAQ:   Init ecmc with support for only daq (not motion)
    NO_MR: Init ecmc with support for motion (without motor record) and DAQ
 PVA               = YES / NO
 TMP_DIR           = directory for temporary files
 ENG_MODE          = 1/0. If ENG_MODE is set then PVs used for commissioning will be available
 EC_TOOL_PATH      = Path to ethercat tool defaults to ethercat tool in ECmasterECMC_DIR,
 otherwise            "/opt/etherlab/bin/ethercat"
 MAX_PARAM_COUNT   = Maximum asyn param count, defaults to 1500
 START_EPICS_FIRST = 1/0, default 0. Start EPICS records before ECMC runtime
                     and EtherCAT when set to 1.

 [set by module]
 ECMC_CONFIG_ROOT       = root directory of ${MODULE}
 ECMC_CONFIG_DB         = database directory of ${MODULE}
 EthercatMC_DB          = database directory of EthercatMC
 ECMC_EC_MASTER_ID      = EtherCAT master id in use (for use in later scripts)
 ECMC_EC_SAMPLE_RATE    = EtherCAT bus sampling rate [Hz] (1000 default)
 ECMC_EC_SAMPLE_RATE_MS = EtherCAT bus sampling rate [ms] (1 default)
 ECMC_MODE              = ecmc mode. FULL/DAQ, Defaults to FULL
 ECMC_PVA               = use pva, default NO
 ECMC_SUPPORT_MOTION    = Variable to be used to block use of motion (""/empty=support motion or "#-"=disable motion)
 ECMC_TMP_DIR           = directory for temporary files, defaults to "/tmp/${IOC}/EcMaster_${ECMC_EC_MASTER_ID}}/"
 ECMC_EC_TOOL_PATH      = path to ethercat tool
 ECMC_SAMPLE_RATE_MS    = current record update rate in milliseconds
 ECMC_SAMPLE_RATE_MS_ORIGINAL = ECMC_SAMPLE_RATE_MS (used for restore to default if ECMC_SAMPLE_RATE_MS is changed)
```

Normally these arguments are set when the module is required:
```
require ecmccfg "ENG_MODE=1,MASTER_ID=2"
```

## Start EPICS before EtherCAT

The default, `START_EPICS_FIRST=0`, preserves the traditional startup order:
ECMC enters runtime and starts EtherCAT before `iocInit` completes.

Set `START_EPICS_FIRST=1` when EPICS records must be initialized before ECMC
runtime and EtherCAT start:

```bash
require ecmccfg "START_EPICS_FIRST=1"
```

In this mode, `startup.cmd` allows `iocInit` to reach the IOC-running state and
then schedules ECMC startup asynchronously. The worker waits for
`ECMC_EC_STABILIZATION_TIME` seconds (default `2`) before executing
`Cfg.SetAppMode(1)`.

This ordering can be useful with EPICS autosave. It gives autosave restore and
record/device-support initialization an opportunity to apply restored PV values
before the realtime thread and EtherCAT bus start. For example:

```bash
require ecmccfg "START_EPICS_FIRST=1,ECMC_EC_STABILIZATION_TIME=5"
```

The delay is a time window, not a completion handshake with autosave. Select a
delay long enough for the IOC's restore workload and verify the startup log and
restored values. If a configuration requires a strict guarantee, trigger ECMC
startup from an explicit restore-complete mechanism instead of relying only on
a fixed delay.

PLCs can use `epics_get_started()`, `ec_get_started()`, and
`system_get_started()` to inspect startup readiness. See
[PLC functions]({{< relref "/manual/PLC_cfg/functions.md" >}}).

## EtherCAT startup timeout

When EtherCAT startup fails with messages like `Max wait time 30 second(s)`,
increase the EtherCAT startup timeout before ecmc enters runtime:

```bash
ecmcConfigOrDie "Cfg.SetEcStartupTimeout(100)"
```

The value is in seconds. The default timeout is 30 seconds.

Place the command after `require ecmccfg` or `startup.cmd` has loaded ecmc,
but before `setAppMode.cmd` or `finalize.cmd` starts runtime. In the normal
startup flow, this means before `iocInit`, because `finalize.cmd` is typically
registered to run at init.

This is different from `ECMC_EC_STARTUP_DELAY`. That macro is used by
`setAppMode.cmd` for `Cfg.EcSetDelayECOkAtStartup(...)` and controls a startup
delay/minimum wait, not the maximum OP-state timeout.

## `MASTER_ID=-1`

Setting `MASTER_ID=-1` starts ecmc without claiming an EtherCAT master.
This is the supported master-less or non-EtherCAT mode.

Typical use cases:

- PLC-only IOC logic
- data-storage workflows without fieldbus hardware
- plugin development or testing without EtherCAT
- startup and database testing on systems without realtime EtherCAT access

Example:

```bash
require ecmccfg "MASTER_ID=-1,ENG_MODE=1"
```

In this mode, EtherCAT-dependent hardware setup scripts such as `addSlave.cmd`
are normally not used, but other parts of ecmc still work, for example:

- PLCs loaded with `loadPLCFile.cmd` or `loadYamlPlc.cmd`
- data storage created with `addDataStorage.cmd`
- PLC variables exposed as EPICS PVs
- plugins that do not require an active EtherCAT master

## iocsh startup
ecmc needs to be started with root privileges (or with a user in the realtime group), otherwise ecmc might segfault.
