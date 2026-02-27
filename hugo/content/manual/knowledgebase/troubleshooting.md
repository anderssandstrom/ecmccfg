+++
title = "Troubleshooting"
weight = 18
chapter = false
aliases = ["/manual/troubleshooting/"]
+++

## Startup issues
- **EtherCAT validation fails**: verify slave order/ids, confirm process image matches hardware, and check for missing power/ESTOP on drives.
- **IOC won’t start after partial hardware failure**: fix cabling/power first; restarting with missing slaves leaves the IOC unusable.

## Motion issues
- **Axis won’t enable**: ensure auto-enable is configured in `axis.autoEnable` (or motor record disabled), check STO and brake signals, and confirm SDOs downloaded for each drive channel.
- **Moves in wrong direction**: prefer inverting at the slave via SDO; alternatives are encoder scaling sign or motor record `DIR` (last resort).
- **Homing stalls**: confirm homing sequence type, switch polarity, and latch wiring; use homing monitoring/tolerances and check limit override logic.
- **Soft limits not respected**: enable target/lag monitoring and confirm motor record soft limits are synced (if enabled).

## PLC/scripting
- **Limit logic overrides**: when using `plcOverride` for limits, write `ax<id>.mon.lowlim/highlim` in PLC code (1 = OK).
- **Command scripts**: run through `SCRIPTEXEC` macros carefully; mismatched macros often break SDO verification.

## Diagnostics
- Use `read_el70xx_diag.sh` or `read_el5042_diag.sh` for Beckhoff drives/encoders.
- Check `iocsh` output for YAML lint/schema errors (v8+).
