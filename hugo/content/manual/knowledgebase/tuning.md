+++
title = "tuning"
weight = 15
chapter = false
+++

### Tuning

An ecmc motion system usually contains three cascaded loops:
* Position loop
* Velocity loop
* Current (torque) loop

For many applications, default drive parameters are already good enough. For higher performance requirements, expect iterative tuning.

#### Loop ownership by mode
Which loop is tuned in ecmc versus drive depends on operation mode:

* `CSP`: trajectory in ecmc, control loops in drive
* `CSV`: trajectory + position loop in ecmc, velocity/current loops in drive
* `CSP_PC` (dual position loop): position loop active in both ecmc and drive

`CST` exists for some drives, but it is not a standard ecmc axis-object mode.

For full mode details, see [CSV/CSP/CSP_PC modes]({{< relref "/manual/motion_cfg/modes_CSV_CSP_CSP_PC.md" >}}).

#### Before tuning: verify scaling first
Bad tuning behavior is often caused by scaling or backlash issues, not PID gains.

Recommended quick check:
1. Set `Kp=0`, `Ki=0`, `Kd=0`.
2. Execute a move and compare setpoint vs actual position.
3. Interpret result: different slopes between setpoint and actual indicate scaling mismatch; similar slopes with offset/hysteresis indicate backlash.

#### Position loop
The position loop parameters are available through PVs. For many axes, pure P control is enough.

For runtime inspection and tuning of controller-related parameters via the ecmc command parser, use [ecmc_cfg_tool]({{< relref "/manual/motion_cfg/ecmc_cfg_tool.md" >}}), especially the dedicated controller app (`cntrl`).

Typical sequence:
1. Run repeated forward/backward moves.
2. Increase `Kp` until oscillation starts.
3. Reduce `Kp` to about 40% of that oscillation threshold.
4. Add small `Ki` and `Kd` only when needed (for example backlash handling or `CSP_PC`).

#### Velocity and Current loop
These control loops need to be tuned in the drive.

For EL70x1, see [EL70x1 tuning]({{< relref "/manual/knowledgebase/hardware/EL70x1.md#tuning" >}}).
For other drives, consult the dedicated manual.

#### EL7062
EL7062 provides autotune and can identify:
* Resistance
* Inductance
* Current-loop `Kp/Ti`
* Velocity-loop `Kp/Ti`

See [EL7062]({{< relref "/manual/knowledgebase/hardware/EL7062.md" >}}).

#### Backlash
Tuning systems with backlash can be difficult. Sometimes a D-part helps to reduce spikes in the centralized ecmc position loop controller output, and a small I is almost always needed to reach the final position. To conclude, the following is normally good:
* Low velocity
* Small I part to integrate the backlash
* Some D-part to dampen the output mainly from integrator

Backlash diagnosis should start with identifying where the mechanical play is located:
* Between motor and encoder: usually affects loop behavior more than final positioning accuracy.
* Between encoder and final mechanics/load: usually affects final positioning accuracy more than loop stability.
* Combination of both: tune and mechanical mitigation are both often needed.

Always evaluate backlash size against required positioning tolerance/accuracy before selecting compensation strategy.

If the system cannot be tuned, it may be necessary to run the system in open loop (with the option of using motor record retries). Note, this is not a good option for axes involved in a kinematic system.

##### Motor record backlash compensation
The motor record backlash compensation fields can be used if needed. Basically they ensure that the system always approaches from the same direction by issuing two move commands:
1. A first move that is longer `target + BDST` or shorter `target - BDST` (depending on which direction to approach from)
2. An approach command to go to the final target position

* BDST: Distance for the second approach move command
* BVEL: Velocity for approach move
* BACC: Acceleration for approach move

For synchronized systems, see the constraints in the next section before enabling backlash compensation.

#### Synchronized systems (master/slave)
For synchronized systems, treat compensation features with extra care:
* Prefer fixing mechanical backlash first; software compensation can conflict with synchronized execution.
* Avoid motor-record backlash compensation and open-loop retries on slaved physical axes.
* Master/slave systems should be run through one synchronization state machine so only one axis group accepts commands at a time.
* If a slaved axis enters interlock/error/limit, resolve the slaved axis condition first, then reset/recover the synchronization state machine.

For setup patterns, see:
* [Native master/slave state machine]({{< relref "/manual/upgrades.md#native-masterslave-state-machine" >}})
* [Synchronization examples]({{< relref "/manual/examples.md" >}})

#### Notes
* Many small Beckhoff EL/EP drives (48 V class) do not support full autotune.
* Virtual axes do not use physical PID loops; tuning applies to physical axes.
* Advanced ecmc options (for example inner/near-target parameter sets and anti-windup behavior) are configured in axis YAML. See [axis YAML settings]({{< relref "/manual/motion_cfg/axisYaml.md" >}}).

#### Control mode in practice: closed loop vs open loop
Most systems should run in closed loop. Open loop can be used as a fallback strategy for stepper systems together with motor-record retries.

Open-loop-with-retries workflow (high level):
1. Disable axis motion.
2. Select open-loop counter as primary encoder for control.
3. Align/set open-loop counter position.
4. Configure motor-record retry fields (`RTRY`, `RMOD`, `RDBL`, `RDBD`, `URIP`) and test carefully.

For synchronized axes, follow the constraints in the synchronized-systems section above.

Detailed configuration examples:
* [Motor record and retries]({{< relref "/manual/motion_cfg/motor.md" >}})
* [Best practice: stepper + BISS-C]({{< relref "/manual/motion_cfg/best_practice/stepper_biss_c.md" >}})
