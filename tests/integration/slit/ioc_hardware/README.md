# Real-hardware slit IOC

Run from this directory with the normal IOC launcher:

```sh
cd /path/to/ecmccfg/tests/integration/slit/ioc_hardware
iocsh startup.cmd
```

The `iocsh` launcher calls `iocInit` after loading the startup file. Its registered
`atInit` hook applies the EtherCAT configuration and starts ECMC runtime. The
launcher checks for the literal text `iocInit` anywhere in the startup file,
including comments, and suppresses its automatic call if it finds it. Keep that
text out of `startup.cmd` unless an explicit initialization command is intended.

Default IOC/PV prefix: **HWSLIT:**. The startup explicitly selects `SIM=0` and
asserts real backend 0 on EtherCAT master 0. Engineering PVs remain available.
`HARDWARE_IOC`, `ECMCCFG_HW_VER` and `ECMC_HW_VER` override the IOC name and
installed module versions (default versions: `sandst_a`). Install matching ECMC
encoder-power support and current ecmccfg YAML templates before using this setup.

This configuration is based on the existing slit lab configuration and the
colocated simulation fixture, with the hardware arrangement supplied by the user:

| Position | Terminal | Use |
| --- | --- | --- |
| 0 | EK1100 | Coupler |
| 5 | EL2008 | Brake release: output 01 = TR_LO, output 02 = TR_HI |
| 9 | EL5042 | Channel 1: TR_HI BiSS; channel 2 unused |
| 12 | EL7031 | TR_HI stepper; internal counter encoder 1 |
| 14 | EL7041-0052 | TR_LO stepper; internal counter encoder 1 only |
| 25 | EL2794 | Channel 1: TR_HI encoder supply, active high; channels 2–4 unused |

Axis names and indices remain `TR_LO`=5, `TR_HI`=6, `CENTERY`=12 and `GAPY`=13.
The virtual slit kinematics, dynamic soft limits and master/slave state machine
are unchanged. Both physical axes use real drive-status input bits 11/12 for
backward/forward limits. No dedicated home cam or external interlock is wired
by this file; the inherited constant inactive interlock is explicit in the YAML.
Cam homing is disabled and no synthetic status bit 13 is linked.

## Encoder feedback and auto-power

TR_LO runs purely on its incremental internal counter; it does not configure an
EL5042 channel or encoder power output. TR_HI creates its counter first and then
loads `cfg/biss-c.yaml` as encoder 2. That YAML enables auto-power using
`ec0.s25.binaryOutput01.0`, with encoder 1 as its always-powered backup.

The configured warm-up delay is 0.1 s, timeout 5 s, settled idle delay 2 s and
permitted wake discrepancy 0.02 mm. EL5042 ready bit 2, warning bit 0 and error
bit 1 are linked normally. Auto-power is independent of drive auto-disable.
Edit `cfg/biss-c.yaml` to change these values or disable power control.

After a completed settled move, ECMC references and selects the tracking
counter before switching off the BiSS supply. A new move powers and validates
BiSS before switching back. The first wake has no previously aligned counter
reference for mismatch comparison; see the encoder-power documentation.
Use the normal axis/encoder expert panels for mode and power-hold controls.

## Commissioning values inherited from the lab setup

The declared hardware layout, brake wiring, limit polarity, motor currents,
scaling and absolute offset must match the installed rack and mechanics. This
configuration has been checked offline, not commissioned against physical hardware.

- Internal counter scale: 12800 counts/mm; CSV command scale: 32768 counts per 10 mm/s.
- TR_HI BiSS: 4096 counts/mm, 26 absolute bits, engineering offset -1380 mm.
- Physical soft limits: -1 to +1 mm; physical motion velocity: 1 mm/s.
- HI motor: 1000 mA maximum, 500 mA standby, 24 V, coil resistance 1230 mOhm.
- LO motor: 1000 mA maximum, 500 mA standby, 48 V, coil resistance 1230 mOhm.
- Brake release/close-ahead: 250/200 RT cycles at 1000 Hz.

Adjust these YAML/component values for the hardware before commissioning. The
startup keeps all axes disabled and issues no moves, homing or set-position
commands. Because TR_LO uses incremental feedback, its startup coordinate is
not a measured absolute mechanical reference.

## Operation

Operate manually through normal motor/native motion PVs and panels under
`HWSLIT:`. This directory contains configuration only, with no Python plant,
simulation profile, simulation marker or fault-injection runner. The existing
slit acceptance runner intentionally remains SIM-only and must reject this IOC.
The hardware configuration does not change the existing `ioc/` simulation setup.
