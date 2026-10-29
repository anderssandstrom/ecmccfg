# EcTool execution and compatibility

EcTool keeps its existing database records, fields, GUI interfaces, command
numbers and helper positional arguments. No startup or GUI changes are required
for the supplied `ecmcEc.db` configuration. Rebuild the module and install all
`ecTool*.sh` scripts together, including the new `ecToolSupport.sh`.

| Command | Operation | Arguments after helper name |
| --- | --- | --- |
| 5 | Master information | master, prefix |
| 10 | Change slave state | direct EtherCAT `states -mN -pN STATE` |
| 11 | List slaves | master, prefix |
| 20 | Diagnostic SDO messages | master, slave, prefix |
| 70621 | EL7062 autotune | master, slave, channel, prefix |
| 70622 | EL7062 tuning readback | master, slave, channel, prefix |

State values remain 1=INIT, 2=PREOP, 3=BOOT, 4=SAFEOP, 8=OP. Channels are
1 or 2. Master/slave selection remains available through the existing numeric
fields. A zero trigger is still a no-op; a nonzero finite trigger submits work.
Busy records reject another request promptly. Each EcTool record owns a separate
worker and immutable configuration, so multiple instances cannot overwrite each
other's pending command.

## Security changes

The C++ worker uses `posix_spawn()` with a fixed executable and separate argv
entries. It never constructs a shell command. Bash runs a fixed helper file,
not a `-c` command string. The existing installation layout is preserved:
`/ioc/modules/ecmccfg/<version>/R<EPICS-version>/<helper>`.

Prefix and version values are captured from local database links (or constant
inputs) during record initialization. Their existing PVs remain present, but
changing those PVs or the input links after initialization cannot redirect the
worker. Versions must be single path components containing letters, digits,
periods, underscores, plus signs or hyphens; `.` and `..` are rejected. Remote
CA-only metadata links fail closed. Custom databases must supply metadata
locally before `iocInit`. Restart the IOC to change the captured configuration.

The worker snapshots the startup environment, excluding Bash startup hooks and
exported functions. PATH and EPICS environment settings are retained so deployed
`caput` and Python installations continue to work. These executable paths, the
helper installation directory and its ancestors must be administrator-controlled.

Numeric arguments are validated before conversion or execution. NaN, infinity,
fractions, out-of-range values and unknown commands are rejected. Unused numeric
fields do not affect a command. Prefixes beginning with `-` are rejected to
prevent caput option injection. Other prefix characters are passed literally.
Helpers also validate direct invocations, quote arguments and reject malformed
numeric device responses before using Bash arithmetic. Failed helpers return
errors rather than silently treating failed hardware commands as successful.

Two existing helper mistakes are corrected: master information now uses the
requested master, and autotune invokes the shipped
`ecToolEL7062_readBackParams.sh` rather than an absent differently named file.

## Deployment boundary

This prevents EcTool data from becoming arbitrary shell commands; it does not
authorize users to operate equipment. State changes and autotuning intentionally
remain powerful. Apply site EPICS access security to maintenance controls,
underlying aSub/link fields and any sequence/GUI trigger records that invoke
them. Run the IOC without root and grant only necessary EtherCAT device access.
Access-security defaults are unchanged to preserve existing operation.

The separate `MCU-Cmd` / `Cfg.IocshCmd` exposure in the ecmc repository is not
changed by this EcTool patch. Restrict that command record independently; a
client with IOC-shell access can bypass protections elsewhere in the IOC.

The worker waits for each helper to finish; no new execution timeout is imposed
because that could interrupt existing diagnostics or tuning. A hung helper keeps
its record busy but no longer holds the database processing path waiting for a
worker mutex. Helpers continue using the existing caput status/message PVs.

## Verification

Run `python3 -m unittest discover -s tests -p test_ectool.py -v`.
The tests compile the production argument builder/process launcher, exercise
the production record callbacks with EPICS boundary stubs, and run temporary
helper copies with fake EtherCAT/caput/Python executables. They cover all command
layouts and states, startup metadata snapshots, multiple records, busy/invalid
requests, literal shell metacharacters, option/path rejection, malformed device
output and child failures. They perform no real hardware operations.

A build against the target EPICS installation and an authorized equipment smoke
test remain necessary before deployment. The stub tests do not emulate EPICS
initialization, Channel Access or actual drive behavior.
