+++
title = "Simulation backend (SIM=1)"
weight = 25
chapter = false
+++

`SIM=1` selects ECMC's memory-backed I/O driver for the selected master ID.
Slave and entry declarations create typed memory instead of configuring a
physical EtherCAT master. Motion, PLCs, limits, interlocks and master/slave
coordination continue running in the IOC's normal realtime cycle.

**The memory driver is not a device model.** It does not automatically turn
drive commands into enabled feedback or encoder movement. A separate Python
model, PLC, manual PV client or other model must supply those inputs.

## Start an IOC in simulation mode

Pass `SIM=1` when loading ecmccfg:

```iocsh
require ecmccfg "MASTER_ID=0,SIM=1,EC_RATE=1000"
# Load slave, entry, axis and PLC configuration as usual.
```

| Setting | Behavior |
| --- | --- |
| `SIM=0` or omitted | Existing physical EtherCAT backend |
| `SIM=1` with `MASTER_ID>=0` | Memory backend for that instance |
| `MASTER_ID=-1` | Existing masterless operation; does not create a simulated master |

Startup selects the backend before claiming the instance and skips MX-System
hardware discovery in simulation mode. Backend selection is configuration-only;
choose it before creating that instance's objects. Restart with the appropriate
startup arguments to switch an existing IOC between real and simulated I/O.

For manual ECMC configuration, the corresponding selection is:

```iocsh
ecmcConfigOrDie "Cfg.SetSampleRate(1000)"
ecmcConfigOrDie "Cfg.SetIoBackend(0,1)"
ecmcConfigOrDie "Cfg.EcSetMaster(0)"
```

Set the sample rate before creating objects. Signal names such as
`ec0.s14.positionActual01` stay unchanged, so the normal motion and PLC links
bind the selected backend's storage. Mixed real/simulated instances use distinct
IDs and explicit backend selection; `SIM=1` is not a global override for other
instances. This does not add support for multiple physical EtherCAT masters.

The main ecmccfg panel shows **SIMULATED** in amber or **REAL** in green from
`$(P)MCU-Cfg-Sim-Mode`. That PV describes the startup `SIM` setting; it is not a
runtime backend selector or an inventory of manually configured mixed instances.

## Generated simulation PVs

The normal `setAppMode.cmd`/finalize path automatically generates simulation
field records before runtime when `SIM=1`. Their default prefix is
`${ECMC_PREFIX}SIM:`. For example, an IOC prefix `SIMSLIT:` produces:

| Field direction | Writable PV | Readback PV |
| --- | --- | --- |
| Input to ECMC: status, position, switches | `SIMSLIT:SIM:ec0:s14:driveStatus01` | Same name with `-RB` |
| Output from ECMC: control word, setpoint | `SIMSLIT:SIM:ec0:s14:driveControl01-Set` | `SIMSLIT:SIM:ec0:s14:driveControl01` |

These are **raw I/O values**, not axis engineering values. Position fields
normally contain encoder counts, and control/status fields contain native bit
words. Signed, unsigned, floating-point and 64-bit fields keep their declared
types. Do not assume that writing `1` to a position field means 1 mm.

```sh
# Observe the control word produced by ECMC.
caget SIMSLIT:SIM:ec0:s14:driveControl01
# Inject a status word into the simulated input memory.
caput SIMSLIT:SIM:ec0:s14:driveStatus01 3
caget SIMSLIT:SIM:ec0:s14:driveStatus01-RB
```

The status value above is manual bit injection, not a complete drive model.
An output `-Set` write is also a single write: its axis or PLC owner may replace
it in the next cycle. There is no persistent force/override mode.

The records use automatically created dedicated asyn ports such as
`MC_CPU1_SIM0`, separate from the main `MC_CPU1` parameter table. They share the
same I/O buffers; no second I/O image or additional IOC RT thread is introduced.
Normal axis, PLC and legacy entry parameters remain on the main port.

For a custom prefix, set `ECMC_SIM_PREFIX` **before adding slaves**, so discovery
aliases and generated field records agree. A manually configured IOC can call
`Cfg.SimLoadRecords(<prefix>)` after entry declarations and before runtime or
`iocInit`. Only declared realtime scalar fields at nonnegative slave positions
are generated; aliases and built-in `ZERO`/`ONE` do not create duplicate PVs.

## External Python models and GUI

The tools are in the **ECMC source repository**, under `tools/simulation/`.
Install PyEpics in the client environment and use the normal Channel Access
network settings, including `EPICS_CA_ADDR_LIST` when needed. Start the SIM IOC
first, then run these commands from the ECMC repository root:

```sh
python3 -m pip install pyepics

# Read-only inventory of supported and unsupported configured slaves.
python3 tools/simulation/ioc.py --prefix SIMSLIT:SIM: --list

# Run models for supported drives; observe manual terminal fields.
python3 tools/simulation/ioc.py --prefix SIMSLIT:SIM:

# Optional Tk window with live values and editable simulation fields.
python3 tools/simulation/ioc.py --prefix SIMSLIT:SIM: --gui
```

Discovery follows `FirstSlave`, `ecN:sM:HWType` and `ecN:sM:NxtObjId` aliases
under that single prefix. It reuses normal ecmccfg slave metadata, which must
remain enabled (`DEFAULT_SLAVE_PVS=true`). Unsupported types are listed and
left untouched. Use `--slave 14` to select a slave, `--master N` for another
master, and `--settings models.json` for per-slave scaling and behavior.

| Hardware family | Tool support |
| --- | --- |
| EL7031 variants, EL7041, EL7041-0052, EL7047 | Basic stepper velocity-mode model |
| E*72xx, including supported EL/EP/ELM variants | DS402 CSV/CSP model |
| EL7062, ED7062, MO7062 family | Independent configured DS402 channels 01/02 |
| EL1004, EL1008, EL1808, EL1809 | Manual digital input injection |
| EL2004, EL2008, EL2808 | Digital output readback and single-write controls |
| EL5042, EL5102, EL5101 variants | Manual raw encoder/status fields |

Support also requires compatible configured fields and record types. CST/CSTCA,
drive-motion-control modes, EL7047 position-interface variants and oversampling
arrays are not modeled. Standalone encoder terminals are not automatically
coupled to a drive: supply their feedback relationship in your model.

The GUI shows slave type, command/feedback values and model status. Writable
fields can be edited manually, including drive feedback and output `-Set` PVs.
Active models or PLCs may overwrite those edits. Tkinter and a graphical display
are required only for `--gui`; headless operation remains available.

### Scaling and enable delays

Stepper defaults are 2000 full steps/s at full-scale signed velocity, a
200-step/revolution motor, and 12800 encoder counts/revolution. For example:

```json
{
  "ec0.s14": {
    "full_steps_per_second": 2000,
    "motor_steps_per_rev": 200,
    "encoder_counts_per_rev": 12800,
    "enable_delay": 0.05
  }
}
```

The DS402 model has separate position and velocity scaling. Defaults match the
repository servo example: 2^20 counts/revolution and 2^31 velocity units for
8000 revolutions/s. Override these for the configured motor and drive mode;
scaling is not discovered from SDOs. If CSV and CSP command fields both exist,
select the model mode explicitly in the settings file.

Stepper enable acknowledgement defaults to 50 ms; DS402 forward handshake
transitions default to 10 ms each. CA transport, polling and scheduling add
variable delay. A model error or normal shutdown makes a best-effort fault write
that removes enabled feedback. A disconnected or forcibly killed client cannot
guarantee delivery. Use one model writer per drive; do not run the discovery
models alongside a test plant that owns the same signals.

## Configuration support and limitations

The backend stores scalar PDO declarations, aliases and many configuration
settings in memory. Scalar/configured SDO writes store object-dictionary bytes;
they do not perform mailbox transactions or run device reset logic. Supported
SDO reads/verifications use those stored bytes. DC, watchdog and timing settings
retain configuration metadata without reproducing hardware timing.

Unsupported services, including memory maps, asynchronous SDO requests, SoE and
some specialized link/timing commands, report
`ERROR_MAIN_IO_CONFIG_UNSUPPORTED`. Arbitrary hardware configurations are not
guaranteed to load unchanged.

The driver does not test PDO byte offsets, physical bit packing, endianness,
distributed clocks, network faults, electrical behavior or real drive dynamics.
Python feedback is asynchronous, not cycle-synchronous. Passing a functional
simulation test does not validate real EtherCAT timing or hardware behavior.

Explicit instance-health injection is available with
`Cfg.SimSetHealthy(0,0)` and recovery with `Cfg.SimSetHealthy(0,1)`.
`Cfg.SimSetValue(ec0.s14.positionActual01,123)` injects a typed scalar directly.
An unhealthy instance blocks its bindings/startup readiness; this is not an
emulation of EtherCAT's missed-frame filtering. Physical domain-failure
tolerance remains unchanged.

## Dedicated slit acceptance tests

The separate configuration
`examples/PSI/lab_setup/master_slave/slit_epics_2026/slit_matrix_sim_test/`
provides a simulation-only slit IOC with its own `SIMSLIT:` namespace. The
ECMC repository's modular integration runner supplies its coupled plant:

```sh
# From the ECMC repository root, with the dedicated IOC already running.
python3 tests/integration/slit/run.py --prefix SIMSLIT: --run
```

The default run includes open and closed loop. Select groups with, for example,
`--case limits`, `--case homing`, `--case isolation` or `--case target_write`.
The suite covers motion, limits, faults, encoder feedback/noise, brakes, reduced
torque, synchronization, native/motor interfaces and homing. See
`tests/integration/slit/README.md` and `tools/simulation/README.md` in ECMC for
setup, selection, reports, model settings and applicability limits.

This backend is separate from the local dummy entries described under
[Simulation entries]({{< relref "/manual/general_cfg/ethercat/ethercat_advanced.md#simulation-entries" >}}).
Local `ZERO`, `ONE` and `EcAddSimEntry` values can also be used in a physical IOC.
