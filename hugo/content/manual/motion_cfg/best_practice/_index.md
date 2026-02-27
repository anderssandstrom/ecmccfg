+++
title = "motion best practice"
weight = 30
chapter = false
+++

## best practice
Here you can find some best practice configurations for common use cases.
The complete examples with startup files can be found [here](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice)

### [stepper and BISS-C](stepper_biss_c)
Example closed loop configurations for stepper and linear BISS-C encoder:
1. EL7041-0052 and EL5042 (CSV)
2. EL7062_CSP and EL5042. NOTE, this is **CSP**, with ecmc position loop enabled (EL7062 has firmware bug in CSV)
The complete examples with startup files can be found [here](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_bissc)

### [stepper and incremental]
Example closed loop configurations for stepper and incremental encoder:
1. EL7062_CSP. NOTE, this is **CSP**, with ecmc position loop enabled (EL7062 has firmware bug in CSV)
https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_incremental/el7062

### [servo](servo)
An example configuration of a Ex72xx servo drive with AM8xxx motor.
The complete example with startup file can be found [here](https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/servo)

### Motor record

#### [Auto save restore](motor)
Example of auto save restore configuration for motor record:
https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_openloop_asr

#### [Open loop retries](motor)
Example of open loop configuration with motor recrd retries based on an absolute encoder
https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_openloop_mr_rtry_bissc

#### [No motor record](motor)
Example of configuration without motor:
https://github.com/paulscherrerinstitute/ecmccfg/tree/master/examples/PSI/best_practice/motion/stepper_bissc_no_mr
