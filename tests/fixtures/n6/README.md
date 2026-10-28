# N6 regression inputs

These files are test-owned inputs, independent of the mutable lab setup in
`examples/PSI/lab_setup/N6`. Tests must read these fixtures rather than the
lab examples. Change a fixture deliberately when changing the test case;
do not synchronize it automatically with example configurations.

- `cfg/axis_position_output.yaml`: fine native-counter scaling in full steps,
  automatic CSV/homing mode switching and sequence-26 homing links. Tests
  render the actual production Jinja templates using this input.
- `startup_position_output_100_steps.cmd`: packaged hardware/component startup
  ordering fixture, inspected as text; not a complete standalone test IOC.
- `cfg/axis.yaml` and `startup_pulse_per_fullstep.cmd`: legacy feedback/startup
  fixtures used by the historical pulse-generator checks.
- `cfg/pulse_per_fullstep.cmd` and `cfg/disable_pulse_source.cmd`: frozen
  command-capture inputs for the rejected pulse-generator trial and recovery.
  They preserve historical ratio/order checks; passing these checks does not
  imply that the drive supports this rejected configuration.

These are hardware-free test inputs, not commissioning instructions. Follow
the Hugo N6 guide and current lab example when operating a drive. Hardware
mapping, database, panel and component tests continue to read the production
sources so changes to those implementations remain covered.
