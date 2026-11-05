# Offline Python simulator and harness checks

Run all checks in separate processes, without an IOC or ECMC source checkout:

```sh
python3 tests/run_simulation_checks.py
```

These scripts test the external hardware models and the live suite's verdicts
using controlled CA boundaries. They do not replace ECMC's standalone C++
controller tests or execute live IOC acceptance tests. GUI checks use Tk/Xvfb
when available. Optional GUI checks report skips when those tools are absent.

| Check | Coverage |
| --- | --- |
| `test_el7041_model.py` | Separate Python drive model: supplied full-step/microstep scaling, signed velocity, rollover, enable/reset, limits, native PV directions and failure cleanup; no CA network |
| `test_ds402_model.py` | Separate DS402 CSV/CSP model: enable sequence, fault reset edge, quick stop, configurable scaling, counter rollover, native PV validation and discovery dispatch; no CA network |
| `test_simulation_gui.py` | Digital terminal layouts, retained input state, input/output writes, read-only fallback, worker reporting and optional real Tk/Xvfb controls/shutdown smoke test; fake CA |
| `test_simulation_terminals.py` | Encoder scalar layouts/widths, exact U64 edits, manual drive fields, oversampling notice and independent dual-channel 7062 CSV/CSP dispatch; fake CA |
| `test_slit_acceptance.py` | Offline infrastructure for the separate live slit suite: coupled stepper/EL5042 arithmetic, injection, brake wiring, fake native PV publication, SIM guard, modular selection and JSON/JUnit reports; never runs live IOC cases |
| `test_slit_backlash.py` | Mechanical play with separate drive-counter and EL5042 load feedback, reversal take-up, validation, model cleanup and live backlash case selection |
| `test_slit_homing.py` | Position-based home/limit geometry, independent travel bound, capability/config links, motor/native case enumeration, delayed Busy/DMOV/MOVN/Homed assertions and negative controls |
| `test_slit_plant_timing.py` | Production plant loop with controlled CA latency: separate CA context lifecycle, unchanged watchdog, per-operation timings, first-failure retention before drive trip, and plant/controller error classification |
| `test_slit_isolation.py` | Execute blocked virtual command and physical jog release/STOP cases against controlled responses; reject virtual faults, pending/accepted/queued requests, other-blade motion, failed stops and replay |
| `test_slit_interfaces.py` | Controlled boundary checks of motor/native/mixed/text bursts, STOP and recovery, disabled-state-machine isolation, exact MCU-Cmd replies, and zero-AtTarget completion/STOP verdicts; no live IOC |
| `test_slit_native.py` | Execute real native case/helper methods against controlled responses; verify momentary execute requests versus sequencer status and reject early/ignored motion, wrong relative mode, faults and failed STOP |
| `test_slit_limit_sync.py` | Real live soft-limit-sync case methods with delayed propagation, missing-update negative controls and restoration of original pairs/flags |
| `test_slit_boundaries.py` | Execute live limit recovery/bounce, coordinated STOP and encoder-wrap case methods with controlled responses; negative controls reject ignored limits, replay, failed STOP and missing wraps/jumps |
| `test_slit_motion_requests.py` | Motor moves use per-request completion; ordinary STOP puts bypass the active record's notify queue; bounded arrival/ramp-down, rejection and pre-cleanup diagnostics; fake PVs |
| `test_slit_soft_limits.py` | Direction-specific warning/interlock can stop an invalid target before the boundary; unrelated faults, wrong direction, motion, no diagnostic and overruns must not pass; no IOC |
| `test_simulation_ioc.py` | Prefix-only sparse slave discovery via hardware metadata, supported-model catalog, independent model workers, missing/cyclic metadata and read-only listing; controlled PVs and clocks |
| `test_slit_enable_timeout.py` | Live missing-enable case methods with a virtual native drive timer: adequate wait budget, rejection of brake release and wrong errors, and reproduction of the old eight-second deadline failure |
| `test_slit_recovery.py` | Live case methods with controlled CA/plant state: encoder recovery without replay, secondary isolation, cancellation while a brake opens; negative controls reject automatic restart and late release |
| `test_slit_noise.py` | Seeded bounded EL5042 measurement noise, unchanged mechanics/internal counts, freeze/reset, invalid amplitudes; negative controls reject missing at-target loss/recovery, faults and disable |
| `test_slit_preparation.py` | Delayed restored plant bits, state-machine RESET completion, fresh motor readback and acknowledged SYNC before setup's zero move; missing acknowledgements block preparation |
