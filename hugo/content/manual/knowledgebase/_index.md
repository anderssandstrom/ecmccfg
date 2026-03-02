+++
title = "knowledge base"
weight = 10
chapter = false
+++

## Topics
{{% children %}}
---

## Scope
Troubleshooting EtherCAT motion systems can be difficult because errors often span several layers:
- host/controller timing
- EtherCAT communication
- drive/encoder hardware
- axis configuration and control loops

This knowledge base is a practical first-line guide for diagnosis and recovery.

## Quick Triage Flow
1. Start with [panel]({{< relref "/manual/knowledgebase/panel.md" >}}) for full system status from `ecmcMain.ui`.
2. Check [general]({{< relref "/manual/knowledgebase/general.md" >}}) for common startup/runtime failures.
3. Use [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}}) to verify master/slave state from shell.
4. Use [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}}) as a symptom index.
5. Branch into [motion]({{< relref "/manual/knowledgebase/motion.md" >}}), [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}}), or [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}}) depending on symptom.

## By Symptom
### IOC/host performance or timing instability
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})
- [general]({{< relref "/manual/knowledgebase/general.md" >}})

### EtherCAT state / communication issues
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})

### Axis does not move or reports motion faults
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [motion]({{< relref "/manual/knowledgebase/motion.md" >}})
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})

### Need panel-based diagnosis/operation context
- [panel]({{< relref "/manual/knowledgebase/panel.md" >}})

## Topic Map
- [general]({{< relref "/manual/knowledgebase/general.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [motion]({{< relref "/manual/knowledgebase/motion.md" >}})
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})
- [panel]({{< relref "/manual/knowledgebase/panel.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
