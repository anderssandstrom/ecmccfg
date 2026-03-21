+++
title = "best practice"
weight = 6
chapter = false
+++

### Links to Best Practice
* [General]({{< relref "/manual/general_cfg/best_practice.md" >}})
* [Motion]({{< relref "/manual/motion_cfg/best_practice/_index.md" >}})
* [PLC]({{< relref "/manual/PLC_cfg/best_practice.md" >}})

### ECMC Core Notes (From ecmc Release Docs)
For recent core changes and recommendations, see the ecmc release notes (for example `RELEASE.md` in the ecmc repo).
Highlights to consider in your configurations:
- Use native axis auto-enable/disable (`axis.autoEnable`), added in ecmc v11.
- Keep SDO verification enabled to catch drive current/SDO mismatches before startup.
- You can declare PLC variables with `VAR ... END_VAR` blocks for clearer PLC code.
- Motion parameters can be set via motor record fields (PCOF/ICOF/DCOF) but values must be 100× smaller than native ecmc settings.
