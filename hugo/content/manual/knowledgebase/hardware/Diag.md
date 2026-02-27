+++
title = "Diagnostics"
weight = 16
chapter = false
+++

### Diagnostics

The more advanced Bechoff EtherCAT slaves, like drives and encoder readers, have a diagnostics buffer which can be read with the `ec_diagnostic_messages.py` tool:

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

Searching the web for the slave type and error code normally gives you the information:
* 0x4411 : Warning "Drive. DC-Link undervoltage. (Warning). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8406 : Error   "Drive. DC-Link undervoltage. (Error). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8105 : Error   "General. PD-Watchdog. Communication between the fieldbus and the output stage is secured by a Watchdog."

Here we can see that the drive is missing DC-link voltage (motor power). The watchdog error probably happens during startup of the IOC and is nothing to worry about.

