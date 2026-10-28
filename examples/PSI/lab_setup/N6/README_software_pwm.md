# N6 software-PWM frequency trial

Run `startup_software_pwm.cmd` from this directory instead of the 100-step
position-output startup. The user reported this PWM trial working on
N6-1-1-1-S / FIR-v2542-B1080909 (2026-10-28). Detailed measured frequency,
duty and jitter were not supplied. No axis is loaded, the drive controlword
and velocity command are zero, and output 1 starts disarmed. No additional
PDOs or NanoJ program are needed. The motor component is applied to satisfy
the normal slave configuration requirements; the test does not enable motion.

## Component packaging

Build/install the updated ecmccomp containing `Drive-Generic-PWMOutput`.
The dedicated startup now calls it directly after the motor:

```text
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Drive-Generic-PWMOutput,CH_ID=1,MACROS='FREQUENCY_HZ=2000,DUTY_PERCENT=50,OUTPUT=1,PWM_ID=0,ARM=0,N6_IO_24V=0'"
```

Frequency accepts plain integers 50..2000 Hz; duty accepts 0..100 percent.
Physical output 1..3 and PWM generator 0/1 are selectable. Settings are
startup SDO configuration, not live frequency/duty EPICS controls. The
original `cfg/software_pwm_2khz.cmd` is a compatibility wrapper only.
Other outputs may use PWM or position routing, but the component rejects
shared-generator conflicts, competing claims on one output and conflicting
shared I/O settings. Identical generator settings can feed multiple outputs.
The first output defaults to 5 V; later outputs inherit that level.

## What this test establishes

The N6 manual distinguishes software PWM (up to 2 kHz) from other output
sources (up to 500 Hz). Software PWM has an SDO-set frequency and duty cycle;
it is not a position-based clock. A successful 2 kHz scope measurement does
not establish that `6064` position routing can exceed 500 Hz, nor that the
100-full-step edges can be reproduced with PWM. The carrier can run with
the motor stationary. Gating a carrier also does not guarantee one pulse
at each position or a position-aligned carrier phase.

The older EtherCAT v1.1.0 manual lists the 2 kHz limit and `3260` frequency/
duty objects, but omits the software-PWM routing entries from its table.
The newer **N6 Modbus TCP** v1.2.1 manual for FIR-v2542 explicitly lists
`0x12xx` for PWM 0 (`3260`) and frequency in hertz. That is the basis for
this EtherCAT experiment. The subsequent bench report confirms operation
on the tested drive; it does not establish support on other variants.
If the drive rejects the SDO, record its abort and firmware; do not substitute
brake PWM or change sensorless/feedback settings to work around it.

## Can PWM follow the open-loop counter?

No direct counter-clock or position-synchronization setting is documented
for `3260`: it exposes frequency and duty cycle. Routing selects either
the PWM source (`0x12`) or a counter/position divider, not both. Its gate
selects a bit in `60FE:01`, not a position source.

A PLC can use `6063`/`6064` to control that gate, producing position-windowed
PWM bursts, but the carrier remains time-based. This does not give one
edge per configured number of full steps or a defined position phase.
The normal 1 ms PLC/EtherCAT cycle cannot individually place 250 microsecond
edges. There is no documented SDO-only path here that turns the working
2 kHz carrier into a 2 kHz position-synchronous output. The existing
position-divider route retains its documented 500 Hz limit.

## Settings

| Setting | Value | Meaning |
| --- | --- | --- |
| `323A:01` | `0` | 5 V outputs and 5 V input thresholds; shared I/O selector |
| `3260:01` | `2000` | PWM 0 carrier frequency, Hz |
| `3260:02` | `50` | 50% duty cycle |
| `3252:02` | `0x1210` | PWM 0 to physical output 1; gate bit 16 |
| `60FE:01`, bit 16 | Initially `0` | Arm with the existing `PosOut01-Ena` PV |

The component first disarms the selected gate and queues duty 0 before changing frequency
and routing, then queues duty 50. It preserves the brake bit and other gate
bits, does not write position units or homing parameters, and saves nothing
to drive flash. It does replace output 1's position routing with PWM.
The dedicated trial replaces position routing on output 1. Do not assign
both components to output 1; distinct physical outputs can coexist.
Restart with the 100-step startup to restore the position-output configuration.

## Scope procedure

1. Connect a suitable scope/counter to **X4 pin 5** (output 1), referenced to
   **X4 pin 8** (GNDD). This startup selects 5 V I/O; the motor power supply
   is unrelated to that selection.
2. Start the dedicated IOC and check for SDO errors. Output 1 is disarmed.
3. Arm it using the actual slave prefix:

   ```bash
   caput <prefix>PosOut01-Ena 1
   caget <prefix>PosOut01-Ena-RB
   ```

4. Measure the physical signal, not just the gate readback. At 2 kHz/50%,
   expect a **500 microsecond full period**, **250 microseconds high** and
   **250 microseconds low**. Alternating edges are 250 microseconds apart;
   rising-edge frequency is 2 kHz, not 4 kHz.
5. Disarm with `caput <prefix>PosOut01-Ena 0` and verify switching stops.
6. Repeat gate off/on and, if needed, compare 500/1000/1500/2000 Hz. Change
   `FREQUENCY_HZ` in the component call and restart for each frequency.
   These are suggested checkpoints; any plain integer 50..2000 is accepted.

Record firmware, requested/measured frequency, duty, voltage, load, rise/fall
times and jitter. Compare against the existing position-output waveform
separately. A gate readback confirms the command bit, not the physical output.
The newer manual permits a wider frequency parameter range than the stated
2 kHz software-PWM output limit. An accepted SDO value is not proof of the
physical output frequency; this candidate stays at or below 2 kHz.
The user reported the output working. Record numerical scope results
before treating frequency accuracy, duty or jitter as verified.

Useful readbacks for master 1 / slave 0:

```bash
ethercat upload -m1 -p0 --type string 0x100A 0
ethercat upload -m1 -p0 --type uint8 0x323A 1
ethercat upload -m1 -p0 --type uint32 0x3260 1
ethercat upload -m1 -p0 --type uint32 0x3260 2
ethercat upload -m1 -p0 --type uint16 0x3252 2
```

`ARM=1` can arm at startup; keep the default `0` for initial scope
setup. `N6_IO_24V=1` selects nominal 24 V/+UB_Logic and also changes digital
input thresholds. `DUTY_PERCENT=50` is the tested default, with other integer values 0..100
configurable through the component. `PWM_ID=0` selects the tested generator;
1 selects generator 1 (`3261`, route source `0x13`). Other choices still
need commissioning. Input pull-up is inherited from the motor unless
`N6_INPUT_PULLUP` explicitly overrides it. Options are validated before
the component changes an output.

## References

- [N6 EtherCAT manual v1.1.0, FIR-v2508](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_EtherCAT_Technical-Manual_V1.1.0.pdf): section 7.1.2.3 and object `3260`.
- [N6 Modbus TCP manual v1.2.1, FIR-v2542](https://www.nanotec.com/fileadmin/files/Handbuecher/Motorsteuerungen/n6/fir-v2508/N6_ModbusTCP_Technical-Manual_V1.2.1.pdf): section 7.1.2.3 and object `3260`; source `0x12` and frequency units.
