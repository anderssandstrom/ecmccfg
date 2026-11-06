# Async SDO queue / autosave handoff

Updated 2026-11-06: the implementation now queues scalar requests automatically
and registers startup snapshots through addEcSdoRT.cmd. QUEUE and RESTORE flags
are no longer needed. WRITE_ON_VAL remains optional; manual Val/WrtCmd and
RdCmd remain available, including runtime writes by default. Empty snapshots
produce no restore writes. The example uses automatic startup without a
SDO_AUTO_START setting. The design notes below describe the earlier discussion.

## User requirements

- Extend the existing async SDORT object and retain the existing PV interface.
- Preserve legacy behavior: writing the value stages it; `WrtCmd` initiates a
  write; `RdCmd` must continue to work.
- Optionally support writing a value PV to request a transfer without a
  separate command. This must not silently change existing configurations.
- Serialize requests so autosave restores/bursts do not fail because another
  transfer is busy. Capture each requested payload when queued.
- After a write, upload the actual value, compare it and publish readback.
  Make successful verification distinguishable from merely accepting a request.
- Support PREOP-only startup settings restored by autosave. Delay activation /
  transition to cyclic operation and OP until required writes are verified.
- Account for normal ECMC-first startup, `START_EPICS_FIRST`, and `STARTUP_GATE`.

## Latest proposed simplification

The user suggested retaining the current SDORT objects and **all current PV
names**, but queuing a write request if it arrives before the EtherCAT master
has started. A coordinator would drain these requests sequentially in PREOP,
write/read/verify them, and only then permit master activation.

Important distinction: preserving the interface means a legacy value write
still only stages data; the existing write command queues the transfer. Making
value writes initiate transfers requires an explicit opt-in policy. How that
policy and boot restore processing should work is still to be finalized.

## Findings from current code

- Script is `scripts/addEcSdoRT.cmd` (the user called it `addSDORT.cmd`).
- Native implementation: adjacent checkout
  `../ECMC_latest/ecmc/devEcmcSup/ethercat/ecmcEcAsyncSDO.{h,cpp}`.
- `requestWrite()` / `requestRead()` reject a busy object. There is no shared
  request scheduler. `ecmcEcSlave::execute()` polls each async SDO independently.
- Download completion does not automatically upload/verify the value.
- Scalar staging/readback currently share `buffer_`; queued mode needs immutable
  request snapshots and separate desired/actual storage. Arrays already have
  separate read/write buffers.
- PV templates are `db/core/ecmcSDOAsync*.template`; preserve the existing
  value, command, busy and error PVs. Additional diagnostics, if needed, should
  be optional and minimize native asyn parameter count.
- Startup coordination is in `scripts/finalize.cmd`, `scripts/setAppMode.cmd`
  and `../ECMC_latest/ecmc/devEcmcSup/main/ecmcMainThread.cpp`.
- Normal flow starts ECMC before `iocInit`. With `START_EPICS_FIRST=1`,
  `afterIocRunning` calls `ecmcStartAppModeAsync(...)`.
- `STARTUP_GATE` holds axis initialization/commands and PLC startup; it does
  **not** itself hold slaves in PREOP or delay master activation.

## Proposed startup sequence

1. Configure objects and load PVs, deferring master activation for this mode.
2. Let `iocInit` and autosave boot restore complete.
3. Explicitly collect/process valid restored desired values into a startup batch.
4. A non-RT worker performs sequential PREOP downloads and verification uploads.
5. Required failure leaves activation blocked, with visible error/retry status.
6. On verified completion, activate the master/start cyclic operation, then let
   the normal startup gate wait for bus readiness before releasing motion/PLCs.

PREOP mailbox traffic must already be available: “wait starting the bus” means
delay activation / OP, not stop all EtherCAT communication. IgH provides blocking
SDO upload/download APIs before activation; ECMC already uses them in
`ecmcEcSDO.cpp`. Do not call blocking transfers from the RT thread or while
holding locks needed by EPICS initialization.

## Important constraints / open decisions

- Autosave boot restore writes database fields without processing records. A
  native value-write callback alone will not catch it. Add explicit post-restore
  processing/collection; do not rely on hook registration order within the same
  init phase. Pass 1 runs at `initHookAfterInitDatabase`; a later hook can collect
  final restored values before scheduling the deferred activation worker.
- Handle missing files/values explicitly; never write default zero merely
  because no saved value was restored. Restore-validity handling is unresolved.
- An activation barrier is needed in addition to `STARTUP_GATE`. ECMC-first
  must defer activation for PREOP restore, or the option must require EPICS-first.
- Prevent later static startup SDO downloads from overwriting restored values
  during activation. Resolve duplicate ownership/order for managed SDO indices.
- Decide queue scope (one in flight per master was proposed initially), capacity,
  overflow behavior, ordering and retry policy. No silent drops or overwriting
  an in-flight payload; do not automatically retry potentially side-effecting writes.
- Decide whether runtime requests also use the queue. For PREOP-only endpoints,
  later writes in SAFEOP/OP should fail clearly, without automatically taking a
  running bus back to PREOP. Reads can remain available where supported.
- Preserve `RdCmd` in every mode, serializing explicit reads with queued writes
  and their verification reads. Reads must not replace the desired setpoint.
- With the same PV interface, define busy to cover pending/active/verification
  work and ensure earlier failures are not hidden by later successes. Optional
  request/verified sequence counters and shared status flags were proposed,
  but the latest user preference is to keep the interface unchanged if possible.

## Validation to include when implementing

Legacy staging + write/read commands; optional write-on-value; multiple queued
SDOs; immutable payloads; explicit read ordering; readback mismatch; timeout and
mailbox abort; queue overflow; missing restore data; both startup orders;
activation held until all required writes verify; PREOP-only state enforcement;
no overwrite by static startup SDOs. Start with scalars, then extend arrays.

## Reference documentation

- Autosave restore semantics:
  https://epics-modules.github.io/autosave/autosave.html
- EPICS init hook order:
  https://docs.epics-controls.org/projects/base/en/r7.0.9/initHooks_h.html
- IgH application API / pre-activation SDO transfers:
  https://docs.etherlab.org/ethercat/1.6/doxygen/group__ApplicationInterface.html

No unrelated motion/test work needs to be continued for this SDO task. Inspect
the current worktree before edits; this session also contains unrelated changes.
