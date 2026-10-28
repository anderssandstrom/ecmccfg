#- All optional N6 PDOs: fine counter, drive homing, capture and analog inputs.
#- Run from this directory instead of startup_position_output_100_steps.cmd.
#- Reuse its motor, 100-step output and M1 axis configuration.
#- Capture is mapped but not armed; see README for the capture SDO settings.
iocshLoad "./startup_position_output_100_steps.cmd", "N6_CAPTURE=1,N6_ANALOG_IN=1"
