+++
title = "EL7411 OPT and CSTCA"
weight = 23
chapter = false
+++

`EL7411_OPT` adds CSV, CSP, CST and CSTCA choices through the shared Ex72xx
OPT dispatcher, with an EL7411-specific PDO and timing policy. The existing
`EL7411` and `EL7411_CSP` descriptors, substitutions and panels are unchanged.

## Examples and defaults

```iocsh
# Same four PDOs as the legacy EL7411 CSV configuration.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7411_OPT"

# Torque with externally commanded electrical commutation angle.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7411_OPT,OPT='MODE=CSTCA,DIAG=1,INFO2=INPUTS'"

# Position control with optional touch-probe status and temperature.
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd "HW_DESC=EL7411_OPT,OPT='MODE=CSP,TP=1,DIAG=1,INFO2=TEMP'"
```

Configure the motor and feedback after loading the slave, using the appropriate
EL7411 motor/encoder configuration for the installed hardware. The wrapper sets
`ECMC_EC_COMP_TYPE=EL7411`; it does not replace motor or feedback commissioning.

| Option | Default | Choices |
| --- | --- | --- |
| `MODE` | `CSV` | `CSV`, `CSP`, `CST`, `CSTCA` |
| `TP` | `0` | `0` or `1`; optional touch-probe status only |
| `DIAG` | `0` | `0` or `1`; actual velocity, torque and DC voltage |
| `INFO2` | `NONE` | `NONE`, `INPUTS`, `TEMP` |
| `ENC_STAT` | `0` | `0` only; EL7411 has no documented EL72xx encoder-status PDO |

Channel 1 overrides (`MODE_1`, `TP_1`, `DIAG_1`, `INFO2_1`, `ENC_STAT_1`)
follow the shared option precedence. Second-channel options are rejected.
Invalid combinations fail before slave reset or hardware configuration.
`INFO2=ERRORS` is not offered for EL7411; use the **HW** diagnostic-buffer button.

The default process image contains drive control, velocity demand, primary
position and drive status only. Default CSP similarly matches the existing
`EL7411_CSP` PDO set. With `MODE=CSP,DIAG=1`, following error is additionally
mapped at `0x6010:06`. Torque offset is not mapped on EL7411.

`INFO2=INPUTS` uses a separate EL7411 record template: its hardware-enable/STO
input level is bit 12, whereas the EL72xx template uses bit 8. The shared inputs
panel displays that level through `Drv01-STO01`; this is a diagnostic input
level, not a complete safety-state assessment. The Info2 selector SDO is written
as a one-byte value for EL7411.

## CSTCA target and readbacks

CSTCA uses target torque plus an externally commanded electrical angle. The
startup SDO `0x7010:03` is set to 11. CSV, CSP and CST use 9, 8 and 10.

| Logical EtherCAT entry | PDO | Object | Type |
| --- | --- | --- | --- |
| `torqueSetpoint01` | `0x1602` | `0x7010:09` | S16 |
| `commutationAngle01` | `0x1603` | `0x7010:0E` | U16 |

The following PV suffixes use the normal slave prefix
`$(IOC):m$(MasterID)s$(SlaveID)-`:

| Writable target | Demand readback | Units |
| --- | --- | --- |
| `Drv01-Trq` | `Drv01-Trq-RB` | Percent, 0.1 per raw count |
| `Drv01-ComAngle` | `Drv01-ComAngle-RB` | Electrical degrees, 360/65536 per raw count |

The angle target is bounded to 0…359.9945068359375 degrees, corresponding to
raw U16 values 0…65535. The angle readback reports the commanded PDO value;
it is not a measured rotor angle. CSTCA controls the electrical angle directly,
so it can produce motor movement when enabled.

## Panels

The wrapper uses the existing 128 × 500 OPT overview, including its **HW**
EtherCAT diagnostic-buffer shortcut. `CfgMode=3` identifies CSTCA; CSV/CSP/CST
retain values 0/1/2. The channel panel shows a **CSTCA details** link only when
that mode is configured. The existing Ex72xx CSTCA support on this branch is retained.

`ecmcEX72XX_OPT_cstca.ui` provides torque controls and a writable angle,
angle demand readback and **>** trend button in a compact 350 × 332 panel.
Press Enter to write torque or angle. With `DIAG=1`, actual torque is also
shown. With `DIAG=0`, it displays **Not mapped** and does not subscribe to an
absent actual-torque PV. DS402 enable/disable and the state guide remain
available without an axis object. Coordinate direct target writes with the
axis configuration whenever an axis controls the drive.

CSV/CSP/CST, diagnostics, touch-probe and temperature panels are shared with
[Ex72xx OPT]({{< relref "/manual/knowledgebase/hardware/EX72xx_OPT.md" >}}).
Velocity and position demand records default to the legacy raw scale (1, RAW).
`VEL_ESLO`, `VEL_EGU`, `POS_ESLO` and `POS_EGU` can override demand/velocity
record scaling; they do not change the drive's SDO scaling. Primary encoder
position retains the existing raw-position record convention.

## Timing and validation

The default DC schedule and current initialization match the legacy EL7411:
Sync 0 is 62500 ns, Sync 1 is the application period minus 62500 ns, both
`0x1C32` and `0x1C33` receive sync-mode 3 and the application period, and the
initial peak-current SDO is 1000 mA. Motor configuration can overwrite that
current setting. `SYNC_0_CYCLE`, `SYNC_0_SHIFT`, `SYNC_1_CYCLE`, `SYNC_1_SHIFT`,
`WATCHDOG_DIVIDER` and `WATCHDOG_INTERVALS` use the shared override conventions.
No EtherCAT port-wiring check is enabled. The shared startup-delay policy is
retained.

Static integration checks compare default CSV/CSP mappings to the legacy
configurations, exercise all mode/feature combinations, expand databases,
verify angle scaling and limits, follow visible panel links and compile the
Qt panels. They do not connect to a drive; commissioning on target hardware
remains necessary.

Mapping sources: Beckhoff [EL7411 standard objects](https://infosys.beckhoff.com/content/1033/el7411/10024855819.html),
[configuration data](https://infosys.beckhoff.com/content/1033/el7411/10030254603.html),
and [commissioning with status word and control word](https://infosys.beckhoff.com/content/1033/el7411/11335831691.html).
