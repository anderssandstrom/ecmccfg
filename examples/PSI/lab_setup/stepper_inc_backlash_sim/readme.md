# Test setup for backlash
Simulated with a coupling made of electrical tape (much deadband)

## Notes
It's good to have:
* Low velocity
* Small I part to integarte the backlash
* Some D-part to dampen the output mainly from integrator

If system is not possible to tune then it could be needed to run the system in open loop.

## Motor record backlash compensation
The motor record backlash compensation fields can be used if needed. Basically they ensure that the system approaches always from the same direction by issueing two move commands:
1. A first move that is longer `target + BDST` or shorter `target - BDST` (depending on which dir to approach from)
2. An approach command to go to the final taeget position

* BDST: Distance for the second approach move comamnd
* BVEL: Velocity for approach move
* BACC: Acceleration for approach move

If the motion axis in a synchronized system then using the motor record backlash field is not a good approach.

