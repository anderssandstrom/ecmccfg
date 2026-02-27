+++
title = "best practice"
weight = 6
chapter = false
+++

### links to best practice:
* [General](../general_cfg/best_practice/)
* [Motion](../motion_cfg/best_practice/)
* [PLC](../plc_cfg/best_practice/)

### ECMC core notes (from ecmc release docs)
For recent core changes and recommendations, see the ecmc release notes (e.g. `RELEASE.md` in the ecmc repo).
Highlights to factor into your configurations:
- Use native axis auto-enable/disable (`axis.autoEnable`), added in ecmc v11.
- Keep SDO verification enabled to catch drive current/SDO mismatches before startup.
- You can declare PLC variables with `VAR ... END_VAR` blocks for clearer PLC code.
- Motion parameters can be set via motor record fields (PCOF/ICOF/DCOF) but values must be 100× smaller than native ecmc settings.
