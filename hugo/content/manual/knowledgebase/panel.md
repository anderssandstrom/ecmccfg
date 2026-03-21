+++
title = "panel"
weight = 11
chapter = false
+++

## Scope
Use the panel as the fastest operator-level overview when you want to see the
overall state of the IOC, EtherCAT master, slaves, axes, PLCs, plugins, and
data-storage objects in one place.

## Overview Panel
For an overview of an ecmc system, the ecmcMain.ui panel is a good starting point.
The ecmcMain.ui covers most parts of an ecmc system:
* ecmc_rt thread diagnostics:
    - Jitter
    - Cycle time
* EtherCAT:
    - Status
    - Lost frames
    - Slave count
    - master Id
    - Links to dedicated sub panels for each slave type.
* Links to all configured objects:
    - motion expert panels
    - PLC objects
    - plugin objects
    - data storage objects

## Start the Panel
The panel is started with the following syntax:
```bash
caqtdm -macro "IOC=<ioc_name>" ecmcMain.ui
```

## Related Pages
- [knowledge base]({{< relref "/manual/knowledgebase/_index.md" >}})
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
