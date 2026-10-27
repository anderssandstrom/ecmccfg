+++
title = "General configuration"
weight = 7
chapter = false
+++

<!-- Preserve links to the former overview headings. -->
<a id="scope"></a>

General configuration covers IOC startup and behavior shared by axes, PLCs,
plugins, and data services.

<!-- Preserve links to the former overview headings. -->
<a id="by-task"></a>
<a id="topics"></a>
<a id="use-utility-functions-in-startup-scripts"></a>
<a id="configure-generic-data-capturebuffering"></a>
<a id="browse-command-api-details"></a>
<a id="script-authoring--automation-path"></a>

## Choose an area

- [Startup and IOC configuration]({{< relref "/manual/general_cfg/startup/_index.md" >}}) — startup macros and modes, validation, record processing rates, and host recommendations.
- [EtherCAT and commissioning]({{< relref "/manual/general_cfg/ethercat/_index.md" >}}) — supported slaves, domains, DC timing, verification, and safety telegrams.
- [Utilities and reference]({{< relref "/manual/general_cfg/utilities/_index.md" >}}) — script entry points, iocsh helpers, command API, data buffers, lookup tables, and logging.

<!-- Preserve links to the former overview headings. -->
<a id="apply-platform-level-recommendations"></a>
<a id="configure-epics-record-processingupdate-rate"></a>
<a id="new-ioc-bootstrapconfig-path"></a>
<a id="recommended-reading-paths"></a>
<a id="start-and-parameterize-ecmccfg"></a>

## First IOC

1. Follow the [Quickstart]({{< relref "/manual/quickstart.md" >}}) and [Introduction]({{< relref "/manual/introduction.md" >}}) for the startup structure.
2. Set [startup macros]({{< relref "/manual/general_cfg/startup/_index.md" >}}) and choose a [mode]({{< relref "/manual/general_cfg/startup/modes.md" >}}). For hardware-free operation, see `MASTER_ID=-1` in the startup reference.
3. Review [PV processing rates]({{< relref "/manual/general_cfg/startup/PVProcessingRate.md" >}}) and [host recommendations]({{< relref "/manual/general_cfg/startup/best_practice.md" >}}).
4. Run the [startup validator]({{< relref "/manual/general_cfg/startup/startup_validator.md" >}}) before starting the IOC.

For script authoring, start with the [script reference]({{< relref "/manual/general_cfg/utilities/script_reference.md" >}}) and [iocsh utilities]({{< relref "/manual/general_cfg/utilities/iocsh_utils.md" >}}), then use the EtherCAT or data-service guide for the feature you need.

For runtime faults, start with [Troubleshooting]({{< relref "/manual/knowledgebase/troubleshooting.md" >}}).
