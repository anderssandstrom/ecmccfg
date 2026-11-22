# Hardware-profile axis examples (draft)

Two example *configuration fragments* are included:

- `el7041/startup.cmd` + `el7041/cfg/axis.yaml` — EL7041 CSV single-channel stepper.
- `el7062/startup.cmd` + `el7062/cfg/axis.yaml` — EL7062 channel 1 in CSV mode.

Run in an IOC initialized with ecmccfg and the matching ECMC hardware
abstraction branch. These are not complete standalone IOC applications.

Both illustrate the intended hardware abstraction:

```yaml
drive:
  slave: $(DRV_SLAVE)
  numerator: 10.0

encoder:
  slave: $(DRV_SLAVE)
  numerator: 1.0
```

The drive's `velocitySetpoint01`, `driveControl01`, `driveStatus01`,
and the encoder's `positionActual01` come from hardware profiles, rather
than being repeated in the axis YAML. The example hardware profiles also
supply `drive.denominator: 32768` and `encoder.denominator: 12800`.
Axis-specific `denominator` values can still override those defaults.

**Safety and verification:** The sample numerical scaling assumes a particular
200-step motor, microstepping setup, and mechanics. Replace it with the
actual motor, microstep settings, gear ratio and engineering units.
Set appropriate motor/drive components (rated current, voltage, resistance,
inductance, and controller parameters) before enabling the drive.

The `ONE.0` limit links are **demonstration placeholders only**; they do
not provide end-stop protection. Replace them with tested hardware limit
inputs and validate polarity before any real movement. The EL7062 example
only targets channel 1; channel 2 needs its own verified profile.

These examples have not been validated by an IOC build or hardware test.
