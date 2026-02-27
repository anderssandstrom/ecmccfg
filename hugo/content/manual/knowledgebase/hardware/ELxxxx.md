+++
title = "ELxxxx"
weight = 16
chapter = false
+++

## Power bus - 5V or 24V terminals
24V is the most common signal level for the terminals. However, some also support other voltage levels, for instance 5V or 12V.
In that case, normally the terminal needs to be powered with the same voltage.
For 5V terminals, normally an EL9505 is added before the 5V terminal in the EtherCAT chain, supplying the power bus with 5V.

Example of slaves needing 5V power supply:
* EL1124
* EL1252-0050
* ...

{{% notice warning %}}
**If a 5V terminal is supplied with 24V it will most likely break. Make sure the terminals have the correct power supply __before__ powering the system.**
{{% /notice %}}

{{% notice note %}}
**The voltage level of the power bus after (downstream of) a 5V terminal is normally also 5V. If another voltage is needed, then another system terminal is needed to set a new voltage level of the power bus.**
{{% /notice %}}
