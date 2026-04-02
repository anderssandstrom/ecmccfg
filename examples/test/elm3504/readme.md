# ELM3504 example

This example shows how to add an `ELM3504_Scalar` slave:

- [elm3504.cmd](./elm3504.cmd)

If you want to use the ELM3504 as temperature feedback in a heat-control application,
see the best-practice example where a motion axis is reused as the heat controller:

- [README.md](../../PSI/best_practice/general/heat_control/README.md)
- [startup.cmd](../../PSI/best_practice/general/heat_control/startup.cmd)
- [axis.yaml](../../PSI/best_practice/general/heat_control/cfg/axis.yaml)

In that setup:

- `EL2535-0002` is used as the heater output
- `ELM3504` with PT1000 is used as the feedback input
- the ecmc motion axis is configured as the heat controller
