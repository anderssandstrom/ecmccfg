+++
title = "Diagnostics"
weight = 14
chapter = false
+++

## Diagnostics

The more advanced Beckhoff EtherCAT slaves, like drives and encoder readers, have a diagnostics buffer that can be read with the `ec_diagnostic_messages.py` tool:

Example: EL7211-9014
```
python3 ec_diagnostic_messages.py -m3 -s14
 
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

Sometimes the `text_id` values are converted to readable messages by the tool, and sometimes not. In the case above, we need to look up the `text_id` values on Beckhoff's website.

Searching the web for the slave type and error code normally gives you the information:
* 0x4411 : Warning "Drive. DC-Link undervoltage. (Warning). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8406 : Error   "Drive. DC-Link undervoltage. (Error). The DC link voltage of the terminal is lower than the parameterized minimum voltage"
* 0x8105 : Error   "General. PD-Watchdog. Communication between the fieldbus and the output stage is secured by a Watchdog."

Here we can see that the drive is missing DC-link voltage (motor power). The watchdog error probably happens during startup of the IOC and is nothing to worry about.
