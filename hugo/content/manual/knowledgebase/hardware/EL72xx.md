+++
title = "EL72xx"
weight = 22
chapter = false
+++

## Scope
Use this page for EL72xx servo-drive issues such as diagnostics, warning/fault
states, tuning, and installation-related OCT problems.

## Topics
1. [Diagnostics](#diagnostics)
2. [Error/warning](#errorwarning)
3. [Tuning](#tuning)
4. [Electrical installation issues](#electrical-installation-issues)
5. [OCT cable failure](#oct-cable-failure)

## Diagnostics

The diagnostics buffer can be read with the `ec_diagnostic_messages.py` tool:

Example: EL7211-9014
```
python3 ec_diagnostic_messages.py -m1 -s3

DEVICE INFORMATION:
===================

name:		EL7211-9014
master id:	1
slave id:	3
vendor id:	0x2
product id:	0x1c2b3052
host time:	2026-02-05 11:33:41.191176


DIAGNOSTIC MESSAGES:
====================
msg_no  time                        text_id  text  flags  diag_code   dynamic
1       2000-01-01 00:00:00         0x4411         0x1    0x1c21e000  0x0
2       2026-02-05 10:30:39.407639  0x8406         0x2    0x1c21e000  0x0
3       2026-02-05 10:30:39.407639  0x8105         0x2    0x1c21e000  0x0
```

Sometimes the `text_id` values are converted to readable text by the tool, and
sometimes they are not. In the example above, the codes need to be looked up on
Beckhoff's site.

Searching for the slave type and error code normally gives you the information:
* 0x4411 : Warning "Drive. DC-Link undervoltage. (Warning). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8406 : Error   "Drive. DC-Link undervoltage. (Error). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8105 : Error   "General. PD-Watchdog. Communication between the fieldbus and the output stage is secured by a Watchdog."

Here we can see that the drive is missing DC-link voltage, meaning motor power
is missing. The watchdog error most likely happened during IOC startup and is
not the main problem.

## Error/warning
If the drive is in an error or warning state and cannot be enabled, common
reasons are:
* missing power supply
* STO tripped
* defective cable
* incorrect or messy cabling between the connector and the actual terminal
* phases connected in the wrong order, resulting in commutation failure
* PD-Watchdog error (see below)

### PD-Watchdog error
A PD-Watchdog error was once observed when restarting the system after a
complete power-down event during a yearly shutdown test.

Symptoms:
* Slave goes to OP but stays in fault state (or sometimes not even in fault state).
* Position of absolute encoder is 0.
* Refuses to enable.

Diagnostic tool output below:
```
sandst_a@sls-ec-di22-05-01:~$ python3 /ioc/NeedfulThings/ecmc_ec_scripts/ec_diagnostic_messages.py -m3 -s14

DEVICE INFORMATION:
===================

name:		EL7211-9014
master id:	3
slave id:	14
vendor id:	0x2
product id:	0x1c2b3052
host time:	2026-02-24 15:39:38.197238


DIAGNOSTIC MESSAGES:
====================
time                        text_id  text                 flags  dynamic
2026-02-23 14:56:55.174172  0x8105   (error) PD-Watchdog  0x2    0x0000000000000000000000
```
The likely reason was that the EtherCAT cable was connected to the lower port of
the EK1100 coupler, which resulted in incorrect timing. Stepper systems still
worked, but servos using DC clocks did not. After moving the cable, a power
cycle was required.

Recover by power-cycling the power bus; the communication bus can remain
powered. If an `EL9227-5500` is installed before this point in the EtherCAT
chain, the power bus can be toggled with channel 1 from the panels. At PSI, do
not toggle channel 2, since it may be connected to the communication-bus feed
of the `EK1100`. In that case communication is lost and can only be recovered
by someone physically going to the crate and pressing the button/LED.

{{% notice warning %}}
**PSI: Do not toggle channel 2 of EL9227-5500, since this may break power to the EtherCAT communication bus.**
{{% /notice %}}

Restarting the IOC or switching the terminal between `INIT` and `OP` did not
help in this case.

## Tuning

{{% notice warning %}}
**Always be prepared to "KILL" or estop the axes while performing tuning.**
{{% /notice %}}

* Make sure the scaling factors are correct. Test by setting the ecmc position-controller parameters to `0` and performing a move. This effectively becomes an open-loop positioning move. Normally, the actual value and setpoint should still track each other closely during the move; if not, the drive or encoder scaling is most likely wrong. Check gear ratios as well.
* For most applications, the default current-loop and velocity-loop values are good.
* For slow, accurate, smooth motion, it can be beneficial to reduce the velocity `Kp` and `Ti` values in the drive.

## Electrical installation issues
Strange issues have occurred when the OCT cable shielding was not kept intact up
to the terminal. Problems were observed when individual wires were split out and
mixed randomly in cable-management trays inside a control cabinet. This is not a
good installation concept. Keep the shielding of both encoder and motor cables
intact as far as possible, also inside the crate.

In those cases, the EL72xx diagnostic buffer showed encoder-related errors.


## OCT cable failure
One identified issue was a defective OCT cable. Symptoms included frequent drive
disable events and repeated transitions into fault state.

## Related Pages
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
- [Diagnostics]({{< relref "/manual/knowledgebase/hardware/Diag.md" >}})
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
