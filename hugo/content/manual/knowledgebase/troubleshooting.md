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
- Use the hardware diagnostics guide for `ec_diagnostic_messages.py` usage and interpretation: [Diagnostics]({{< relref "/manual/knowledgebase/hardware/Diag.md" >}}).
- Use `read_el70xx_diag.sh` or `read_el5042_diag.sh` for Beckhoff drives/encoders.
- Check `iocsh` output for YAML lint/schema errors (v8+).

## Error code quick map
| Error | Typical cause |
|---|---|
| `ERROR_MON_BOTH_LIMIT_INTERLOCK` | 24V feed for limits missing, cabling issue. |
| `ERROR_MON_MAX_VELOCITY_EXCEEDED` | Velocity too high, configuration mismatch, or encoder malfunction. |
| `ERROR_MON_POS_LAG_INTERLOCK` | Following error, motion blocked, configuration mismatch (tolerance too tight). |
| `ERROR_MON_STALL` | Motion stall. |
| `ERROR_DRV_HW_ALARM_X` | Hardware error, missing power supply; check dedicated hardware panels. |
| `ERROR_ENC_NOT_READY` | Encoder issue, cabling issue, or missing power supply. |
| `ERROR_EC_LINK_DOWN` | EtherCAT cabling issue, slave power missing. |
| `ERROR_EC_STATUS_NOT_OK` | EtherCAT cabling issue, slave power missing. |
| `ERROR_EC_MAIN_DOMAIN_DATA_FAILED` | EtherCAT cabling issue, slave power missing. |
| `ERROR_AXIS_SLAVED_AXIS_INTERLOCK` | Slaved axis in error (synchronized axes). |
