# EL3214 example

This example shows how to configure an `EL3214` temperature input terminal with
different PT100/PT1000 channel settings:

- [el3214.script](./el3214.script)

If you want to use temperature feedback together with a heater output, see the
best-practice heat-control example where a motion axis is used as the controller:

- [README.md](../../PSI/best_practice/general/heat_control/README.md)
- [startup.cmd](../../PSI/best_practice/general/heat_control/startup.cmd)
- [axis.yaml](../../PSI/best_practice/general/heat_control/cfg/axis.yaml)

That example uses:

- `EL2535-0002` as heater/PWM output
- `ELM3504` as temperature feedback
- an ecmc motion axis as the control loop for heating
