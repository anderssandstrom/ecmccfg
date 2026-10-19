# Hardware profile examples

The standard `loadYamlAxis.cmd` and `loadYamlEnc.cmd` loaders expand profiles
inside the IOC using ecmccfg's native `ecmcExpandHwProfiles` command. They use
`ECMC_TMP_DIR` for intermediate YAML and clean up after a successful load.
**Python and modifications to ECB are not required.**

Rebuild/install ecmccfg to register the command, then run each startup from its
own example directory. Edit `cfg/*.yaml` directly. Select `ECMC_CFG_TOOL=ecb`
before loading the axis (the ECB module startup normally selects it).
There is no offline generation step required before starting the IOC.

The optional `make -C examples/PSI/hw_profiles` builds the standalone tool and
writes inspectable `generated/*.yaml` files; the startup scripts do not use them.
See [native profile support](../../../utils/hw_profiles/README.md).

- [EL7041 + EL5042](el7041_el5042/README.md): drive profile and explicit external BiSS-C feedback.
- [EL7062 CSV](el7062_csv/README.md): drive and incremental feedback profiles, plus index/limit-switch homing and swapped-limit examples.

The motor/controller values, terminal addresses, scaling and limits are examples
to adapt to your hardware. Profiles do not configure SDOs or check wiring; the
startup component calls remain necessary. The examples are checked by rendering,
not by running physical drives.

See the [hardware profile manual](../../../hugo/content/manual/motion_cfg/hardware_profiles.md)
for fields and overrides. The optional Python/Jinja backend also accepts the
source profile YAML directly; the generated YAML works with either backend.

Profile discovery is available without Python:

```iocsh
ecmcListHwProfiles
ecmcListCompatibleProfiles(0, 1, 1)
```

The EL7062 startup now uses `EL7062_OPT` and runs these commands. Compatibility
uses registered startup options; it does not probe the bus or check wiring.
Legacy setups (including the EL7041 example) report `UNVERIFIED`. Only EL7062_OPT
has declared profile compatibility in this first version. Disabled default
limit inputs or a mismatched mode are reported with reasons; encoder index
capture availability is shown separately.

Profile names are explicit. To inspect the resolved configuration, add
`KEEP_HW_PROFILE=1` to either YAML loader call; the expanded file is retained
and its path printed.
