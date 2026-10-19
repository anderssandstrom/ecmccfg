The startup loads `cfg/axis.yaml` directly. The loader expands profiles natively
in the IOC, using temporary storage under `ECMC_TMP_DIR`.

# EL7041 drive profile with EL5042 feedback

`startup.cmd` describes EK1100 at slave 0, EL5042 at 1 and EL7041 at 2.
The example uses an RLS LA11 26-bit BiSS-C encoder on EL5042 channel 1.

In `cfg/axis.yaml`, the drive profile supplies the PDO links, stepper drive type,
control/status bits, error bits `[3, 7, 14]` and raw denominator `32768`.
`maxVelocity: 10` supplies the numerator for the assumed 2000 full steps/second,
200 steps/revolution and 1 mm/revolution. Check the terminal's configured velocity
range before using that value. Torque reduction is enabled by the profile default; set `reduceTorqueEnable: false` to disable it.

The EL5042 encoder remains in the existing explicit YAML format. This demonstrates
mixing a drive profile with an independently configured external encoder. Its
resolution, absolute offset, controller gains and travel limits must match the
mechanics. The profile supplies limit inputs from EL7041 drive status bits 11 and 12; explicit `input.limit` links override them.

Use the exact EL7041 hardware mapping; the initial profile does not select or
configure EL7041 variants. The profile changes no motor electrical parameters.
