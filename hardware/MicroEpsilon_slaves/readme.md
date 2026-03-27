# DT6230


## Configure
Configuration of DT6230 can be done by connecting to the sensor homepage at 169.254.168.150.
A direct connection to the UPPER Ethernet port of the DT6230 will force an IP address on your laptop in the same range, with `255.255.255.0` as netmask.

On the configuration homepage, scaling can be configured depending on which sensor you have connected to the channels.

A setting allowing the DT6230 to connect to EtherCAT is possible (reboot needed).

To switch back to Ethernet, a CoE setting is probably available as for other M&E sensors. Check `0x2100:01, rwrwrw, type 0830, 1 bit, "Ethernet/EtherCAT"`.
