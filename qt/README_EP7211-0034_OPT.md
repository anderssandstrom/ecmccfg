# EP7211-0034 option panel

`ecmcEP7211-0034_OPT.cmd` selects `ecmcEP7211-0034_OPT.ui` automatically through
`ECMC_HW_PANEL`. The overview uses the existing 128 x 500 slave frame and the
standard `IOC`, `MasterID` and `SlaveID` macros.

Three input records describe the resolved startup configuration. Their prefix
is the slave's `ECMC_P` (normally `$(IOC):m$(MasterID)s$(SlaveID)-`).

| Suffix | Values |
| --- | --- |
| `CfgMode` | 0 = CSV, 1 = CSP, 2 = CST |
| `CfgTouchProbe` | 0 = Not mapped, 1 = Mapped |
| `CfgInfo2` | 0 = INPUTS, 1 = TEMP |

These are configuration readbacks, not mode selectors or live drive status.
Changing options requires updating the IOC startup configuration and restarting.
The numerical values are part of the panel interface and should remain stable.

The overview always shows the configuration, actual torque, encoder position
and drive status. `Drv01-TrqAct` is loaded once in every mode, with the existing
0.1 percent scaling and torque alarm thresholds. CSV and CSP now additionally
map the signed actual-torque PDO (0x1a03 / 0x6010:08); CST already maps it.
Legacy profiles are unchanged.

Configuration-driven frames expose links to the selected motion-mode details,
Info2 details and, when mapped, touch-probe status. Only the selected detail
panel is opened, so hidden buttons do not create subscriptions to absent feature
records. Detail panels are diagnostic/readback displays; use the axis control
panel for motion commands. A configured feature's connection failure remains a
connection failure, rather than being interpreted as an unavailable feature.
When Info2 is TEMP, the temperature panel explicitly identifies digital inputs
and STO feedback as not mapped.

Manual launch example:

```sh
caQtDM -macro 'IOC=IOC_PREFIX,MasterID=0,SlaveID=1' ecmcEP7211-0034_OPT.ui
```

Before deployment, check the overview and the selected detail panels against a
running IOC for CSV/CSP/CST, both Info2 selections, and touch probe enabled and
disabled. Confirm actual torque readback and EtherCAT OP after the CSV/CSP PDO
change. Qt UI compilation and static record/channel checks do not verify live
Channel Access behaviour or hardware PDO acceptance.
