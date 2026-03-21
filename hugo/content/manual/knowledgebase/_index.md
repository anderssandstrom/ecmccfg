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

## Start Here
1. Open [panel]({{< relref "/manual/knowledgebase/panel.md" >}}) for a quick full-system view from `ecmcMain.ui`.
2. Use [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}}) to verify master/slave state from the host.
3. Use [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}}) as the symptom-based entry page.
4. Then go to the detailed page for the relevant layer or device.

## By Symptom
### IOC does not start or stops during startup
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [general]({{< relref "/manual/knowledgebase/general.md" >}})
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})

### Host performance, latency, or timing instability
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})
- [general]({{< relref "/manual/knowledgebase/general.md" >}})

### EtherCAT master or slaves are missing, down, or in the wrong state
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
- [general]({{< relref "/manual/knowledgebase/general.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})

### Axis does not enable, does not move, or reports motion faults
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [motion]({{< relref "/manual/knowledgebase/motion.md" >}})
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})

### Need panel-based diagnosis or operation context
- [panel]({{< relref "/manual/knowledgebase/panel.md" >}})

## By Layer
- [general]({{< relref "/manual/knowledgebase/general.md" >}}) for common IOC startup/runtime failures.
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}}) for host-side EtherCAT verification.
- [motion]({{< relref "/manual/knowledgebase/motion.md" >}}) for axis behavior, limits, following errors, and manual motion diagnostics.
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}}) for control-loop and motion-quality issues.
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}}) for NICs, drivers, latency, and deployment details.
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}}) for device-specific notes.

## Tools
- [panel]({{< relref "/manual/knowledgebase/panel.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})

## Topic Map
- [general]({{< relref "/manual/knowledgebase/general.md" >}})
- [ethercat command line interface]({{< relref "/manual/knowledgebase/ethercatCLI.md" >}})
- [troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}})
- [motion]({{< relref "/manual/knowledgebase/motion.md" >}})
- [tuning]({{< relref "/manual/knowledgebase/tuning.md" >}})
- [host / ecmc server]({{< relref "/manual/knowledgebase/host.md" >}})
- [panel]({{< relref "/manual/knowledgebase/panel.md" >}})
- [hardware]({{< relref "/manual/knowledgebase/hardware/_index.md" >}})
