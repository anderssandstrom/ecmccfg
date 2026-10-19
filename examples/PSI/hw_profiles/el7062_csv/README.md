The startup loads `cfg/axis.yaml` directly. The loader expands profiles natively
in the IOC, using temporary storage under `ECMC_TMP_DIR`.

# EL7062 CSV with incremental index homing

`startup.cmd` describes EK1100 at slave 0 and EL7062 at 1. It configures channel 1,
marks channel 2 unused, and sets touch probe 1 to the secondary encoder's index
(`TP1_POS_SRC=SEC,TP1_TRG=INDEX`). Adapt motor and controller parameters first.

`cfg/axis.yaml` uses two independent profiles:

- `beckhoff/EL7062/CSV`: DS402 drive, channel 1 PDO links and raw denominator 2147483648.
- `beckhoff/EL7062/incremental`: secondary position feedback, 32-bit incremental counter and selected touch-probe homing links.

The drive numerator is 2880000 (360 * 8000), following the existing EX7062 CSV
example. Encoder scaling uses 1048576 effective reported position counts per
motor revolution and 360 degrees per revolution. The component's `ST_ENC_RES=2000`
is a hardware encoder setting, not the effective PDO position scaling. Confirm
both representations against your configured terminal.

`low-limit-index` expands to homing sequence 11 with latch arm command 17, width 5
and latch count 1. Low/high limits use `binaryInputs01` bits 0/1. Change the method
to `high-limit-index` for sequence 12. Homing speeds and the reference position
remain explicit. The startup configures homing but does not initiate a home move.

`cfg/encoder.yaml` demonstrates the same profile in a standalone encoder file.
It is not loaded by `startup.cmd`, because the axis already contains that encoder.
For an existing axis that needs this as an additional encoder, select that axis
and load it with:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}loadYamlEnc.cmd "FILE=./cfg/encoder.yaml,DEV=${IOC},DRV_SID=1"
```

Choose primary encoder selection and reference relationships explicitly for that
axis. No additional encoder is made primary by this standalone example.

For ordinary low-limit switch homing, load `cfg/axis_limit_home.yaml` instead of
`cfg/axis.yaml` in the startup. It selects `encoder.homing.type: 1` and generates
no latch/touch-probe links. For that variant, `TP1_POS_SRC` and `TP1_TRG` are not
needed in the encoder component call. Do not load both axis files as axis 1.
The drive profile supplies both limit links by default; explicit links override
them. A home switch can use `home: {driveInput: 1}` if DI1 is wired for home and
the low-limit input is assigned elsewhere.

## Swapped limit inputs and polarity

Load `cfg/axis_limits_swapped.yaml` instead of `cfg/axis.yaml` to use DI2 as the
backward/low limit and DI1 as the forward/high limit. The file is a complete axis
configuration using ordinary low-limit homing (sequence 1):

```yaml
input:
  limit:
    backward: {driveInput: 2}
    forward: {driveInput: 1}
```

The swap changes which physical input is used, including by homing. It does not
reverse axis motion or change electrical polarity. To change electrical polarity
independently, uncomment the polarity fields in that file:

```yaml
input:
  limit:
    backwardPolarity: 1
    forwardPolarity: 1
```

ECMC uses `0` for normally closed (the default) and `1` for normally open.
The polarity-only example leaves the profile's default input assignments intact.
Both overrides can also be combined. Use the settings matching the actual wiring.

For troubleshooting, add `KEEP_HW_PROFILE=1` to the `loadYamlAxis.cmd` arguments.
The loader retains the expanded YAML and prints its path. Profile selection is
explicit; `_OPT` compatibility listing is advisory.
