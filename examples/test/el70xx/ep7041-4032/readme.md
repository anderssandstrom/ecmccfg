# Test scripts for EP7041-4032 (stepper with BISS)
This EP module appears like 2 slaves on the bus, first one drive and second BISS-C:
```
1  0:1  PREOP  +  EP7041-4032 1K. Schrittmotor-Endstufe (50V, 5A)
2  0:2  PREOP  +  EP7041-0000 1K. BiSS-C Encoder
```
** Note: The BISS-C interface is named EP7041-0000 which can be confusing.**

* The drive, EP7041-4032, can be configured as a EP7041-3102 (which is same as EL7041 exept the R_COIL setting)
* The BISS-C encoder, EP7041-0000, can be configured like a channel of EL5042.

## Open points
* According to doc the stepper drive defaults to 256 levels of microstepping but in reality it st ill seems to be 64 levels.
* Microstepping should be configurable but not tested.

