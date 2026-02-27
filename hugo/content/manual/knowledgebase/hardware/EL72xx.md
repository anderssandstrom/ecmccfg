+++
title = "EL72xx"
weight = 22
chapter = false
+++

## Topics
1. [Diagnostics](#Diagnostics)
2. [error/warning](#error/warning)
3. [Tuning](#Tuning)
4. [Electrical installation Issues](#Electrical-installation-Issues)
5. [OCT cable failure](#OCT-cable-failure)

### Diagnostics

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

Sometimes the text_id are converted to a readable message by the tool and sometimes not. In the case above we need to look for the meaning of the text_id-s on Beckhoffs website.

Searching for the slave type and error code normally gives you the information:
* 0x4411 : Warning "Drive. DC-Link undervoltage. (Warning). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8406 : Error   "Drive. DC-Link undervoltage. (Error). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8105 : Error   "General. PD-Watchdog. Communication between the fieldbus and the output stage is secured by a Watchdog."

Here we can see that the drive is missing DC-link voltage (motor power). The watchdog error probably happens during startup of the IOC and is nothing to worry about.

### error/warning
If the drive is in error/warning state and not possible to enable:
* Missing power supply
* STO tripped
* Defect cable
* Wrong/messy cabling between connector and actual terminal.
* Phases connected in wrong order resulting in commutation failure
* PD-Watchdog error (see below)

#### PD-Watchdog error
PD watch-dog error once occuerd at restart of system after a complete power down event (yearly shutdown test).

Symptoms:
* Slave goes to OP but stays in fault state (or sometime even not in fault state).
* Position of absulute encoder 0
* Refuse to enable

Diagnistic tool output below:
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
Reason seemed to be that the EtherCAT cable was conencted to the lower port of the EK1100 coupler resulting in worng timing. Steppers worked fine but servos that use DC clocks did not work. After moving the cable a power cycle was needed.

Reset with a power cycle of power bus (comuncation bus can be powered). If EL9227-5500 before in EtherCAT chain, the power-bus can be toggled with channel 1 from panels. At PSI, do not toggle channel 2 since that could be connected to communication bus feed of EK1100, then communication will be lost and can only be recovverd by someone going physically to crate and pushes the button/LED.

{{% notice warning %}}
** PSI: Do not toggle channel 2 of EL9227-5500, this may break power supply to EtherCAT communication bus**
{{% /notice %}}

Note: restarting IOC or switching terminal between INIT and OP did not help for this issue.

### Tuning

{{% notice warning %}}
** Always be prepared to "KILL" or estop the axes while performing tuning**
{{% /notice %}}

* Make sure scaling factors are correct. Test by setting ecmc position controller parameters to 0 and perform a move. This move will basically be an open loop positioning. Normally the actual and setpoint still track very well during the move; if not, then scaling of drive or encoder is most likely wrong. Check gear ratios.
* For most applications the default values for the current loop and velocity loop is good.
* For slow motion, running slow, accurate and smooth, it could be beneficial to reduce velocity Kp and Ti in the drive.

### Electrical installation Issues
Strange issues have occurred if the OCT cable shielding is not kept intact until close to the terminal. Issues were identified when the individual wires were mixed randomly in cable management trays inside a control cabinet (with OCT connector on outside, then going to terminals, then single wires to EL72xx). This is not a good concept. Keep shielding of encoder and motor cables also inside the crate.
The diagnostic buffer of EL72xx showed encoder related error messages.


### OCT cable failure
Once identified defect OCT cable. Symptoms were frequent disabling of the drive, going to fault state.

### Diagnostics

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

Sometimes the text_id are converted to a readable message by the tool and sometimes not. In the case above we need to look for the meaning of the text_id-s on Beckhoffs website.

Searching for the slave type and error code normally gives you the information:
* 0x4411 : Warning "Drive. DC-Link undervoltage. (Warning). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8406 : Error   "Drive. DC-Link undervoltage. (Error). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8105 : Error   "General. PD-Watchdog. Communication between the fieldbus and the output stage is secured by a Watchdog."

Here we can see that the drive is missing DC-link voltage (motor power). The watchdog error probably happens during startup of the IOC and is nothing to worry about.
