+++
title = "EL9xxx"
weight = 23
chapter = false
+++

## Topics
1. [Over-current protection](#over-current-protection)
2. [Passive terminals](#passive-terminals)

---
## Over-current protection
In the standard setup at PSI, over-current protection modules are used to feed 24V to both the EtherCAT communication bus (E-bus) and the power bus of the EtherCAT slaves. If the over-current protection is not enabled, then the EtherCAT slaves will not receive power.

The first time (and only the first time) a system is used, the over-current modules need to be enabled in order to allow current to flow. Enabling is done by push buttons in the LED area of the module. The long horizontal LEDs are in fact buttons that can be used to activate or trip the over-current protection.

{{% notice warning %}}
**Before pressing any button, check the electrical drawings and make sure it's safe to power on the system.**
{{% /notice %}}

### EL9221-5000
The EL9221-5000 has one channel and therefore only the top button is needed to be pressed.

### EL9227-5500
The EL9227-5500 is a 2-channel module and normally both channels need to be enabled by pressing both the top and bottom long LED. If only one is pressed, it could result in communication power being fine while power to the I/O bus is missing. This can result in strange issues. Both EL9227-5500 and EL9221-5000 have dedicated panels where over-current protection status can be seen.

## Passive terminals
Some terminals are passive. Passive terminals are not EtherCAT slaves and do not communicate over EtherCAT (not equipped with EtherCAT slave controller). Passive terminals are normally used to simplify electrical connections (avoiding external terminals). For instance for distributing potential, 24V and 0V, an EL9184 can be used (8Ch 24V and 8Ch 0V).

The passive terminals will not show up as an EtherCAT slave when issuing the `ethercat slaves` command. However, they are normally visible in the electrical drawings. This could result in the slave ID in the electrical drawing **NOT** corresponding to the EtherCAT slave index used when configuring ecmc. In the worst case, this could lead to the wrong hardware/drive being configured.

{{% notice warning %}}
**When configuring ecmc, make sure the EtherCAT slave index is correct. Do not blindly trust the electrical drawings since a passive terminal could introduce a shift in the slave indices.**
{{% /notice %}}
