# Passive PLC metadata records

`db/core/ecmcPlcDiag.db` uses the separate ecmcRTLog port. Do not add periodic
SCAN processing or I/O Intr to these records. Request metadata on demand:
write a unique positive token to PLCnn-DiagCmd with completion, process/read
PLCnn-DiagStat, then process/read PLCnn-DiagData only when status matches.
Validate the token in the waveform header as well (concurrent clients can race).

ECMC admits at most one request per second across all PLCs in the IOC. A throttled
write fails and leaves the previous status/payload unchanged. Wait at least one
second before manually retrying. Negative matching status means metadata is
unavailable; stale tokens must never be accepted as a successful request.

NELM=65536 is capacity, not transfer length. NORD is the response byte length,
with no trailing NUL/padding. Configure Channel Access client/server array size
limits to accommodate 65536 bytes where needed. The source length in the payload
is a byte length, so decode UTF-8 only after splitting the source bytes.

Source and variable names describe the last successful compilation, not live
variable values. Use existing EPICS PVs for live monitors/trends. No cyclic PLC
sampling or callbacks are added. IOC integration and hardware timing remain to
be validated; record and protocol documentation changes do not establish RT safety.
