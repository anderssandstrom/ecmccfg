+++
title = "hardware"
weight = 16
chapter = false
+++

## Topics
{{% children %}}
---

## Scope
Most field issues are not EtherCAT protocol faults but physical/system integration problems:
- cabling
- missing or partial power
- drive/motor/encoder mismatch
- wrong slave/axis mapping in configuration

## First Checks (Before Any Restart)
1. Open `ecmcMain.ui` and inspect overall status:
   - realtime thread
   - EtherCAT master
   - slave overview
   - motion axes and PLCs
2. Confirm slave states from shell (`ethercat slaves`) and/or `iocsh`.
3. Verify that expected slaves are in `OP`.

```bash
caqtdm -macro "IOC=<iocname>" ecmcMain.ui
```

`red` channels are not automatically wrong; they can also indicate intentionally unconnected signals.

{{% notice warning %}}
Do not blindly restart the IOC with partially working EtherCAT hardware.
This can leave the IOC in a non-recovering startup state.
{{% /notice %}}

## Device-Specific Articles
Use the pages below for terminal/drive-specific diagnostics:
- [Diagnostics]({{< relref "/manual/knowledgebase/hardware/Diag.md" >}})
- [ELxxxx]({{< relref "/manual/knowledgebase/hardware/ELxxxx.md" >}})
- [EL1xxx]({{< relref "/manual/knowledgebase/hardware/EL1xxx.md" >}})
- [EL5042]({{< relref "/manual/knowledgebase/hardware/EL5042.md" >}})
- [EL51xx]({{< relref "/manual/knowledgebase/hardware/EL51xx.md" >}})
- [Ex70x1]({{< relref "/manual/knowledgebase/hardware/EL70x1.md" >}})
- [EL7062]({{< relref "/manual/knowledgebase/hardware/EL7062.md" >}})
- [EL72xx]({{< relref "/manual/knowledgebase/hardware/EL72xx.md" >}})
- [EL9xxx]({{< relref "/manual/knowledgebase/hardware/EL9xxx.md" >}})
- [Hardware issues]({{< relref "/manual/knowledgebase/hardware/hardware_issues.md" >}})
- [Technosoft iPOS4808, iPOS8020]({{< relref "/manual/knowledgebase/hardware/iPOSXXXX.md" >}})
