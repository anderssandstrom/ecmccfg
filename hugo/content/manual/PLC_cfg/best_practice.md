+++
title = "PLC best practice"
weight = 14
chapter = false
+++

## best practice
Here you can find some best practice configurations for common use cases.
* Macros
* MSI include, substitute
* Printouts
* Description
* Common PLC code in ecmccfg/plc_lib
* Variable declaration
* Link PLC variables to EPICS PVs

The corresponding startup files are located in `examples/PSI/best_practice/`.

Public PLC best-practice examples include:

- `examples/PSI/best_practice/plcs/basic/`
- `examples/PSI/best_practice/plcs/masterless/`
- `examples/PSI/best_practice/plcs/motion/stepper_bissc_forw_back_seq/`

### macros
Use of macros makes the code more generic. When loading a PLC file with "loadPLCFile.cmd", custom macros can be defined in "PLC\_MACROS":
```shell
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd,    "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Test', SAMPLE_RATE_MS=1000, PLC_MACROS='BO_S_ID=${ECMC_EC_SLAVE_NUM}'"
```
NOTE: ECMC\_EC\_SLAVE\_NUM expands to the ID of the last added slave.

In addition to the custom macros, a few macros, that are often needed, are predefined:
1. SELF\_ID : Id of current PLC
2. SELF     : plc<SELF\_ID>
3. M\_ID    : EtherCAT master ID
4. M        : ec<M\_ID>

#### SELF_ID and SELF example
A common use case is that some initiation is needed, could be triggering of a custom homing sequence:

```C
if(${SELF}.firstscan) {
  var plc:=${SELF_ID};
  ${DBG=#}println('PLC ',plc,' is starting up');
};

```
After macro expansion the code would look like this (for PLC id=0,DBG=''):
```C
if(plc0.firstscan) {
 var plc:=0;
 println('PLC ',plc,' is starting up');
};

```
#### M_ID and M example
All EtherCAT related information/data is accessible through the pattern "ec<master_id>.s<slave_id>.<name>".
To allow the same code to be loaded on different masters it's a good idea to use the predefined macros,"M" and "M_ID".

Toggle an output:
```shell
${M}.s${BO_S_ID}.binaryOutput${BO_CH=01}:=not(${M}.s${BO_S_ID}.binaryOutput${BO_CH=01});
${DBG=#}println('State: ', ${M}.s${BO_S_ID}.binaryOutput${BO_CH});
```
After macro expansion with the following macros the code would look like this:
* BO\_S\_ID = 10
* BO\_CH    = Not defined (defaults to "01")
* DBG       = Not defined (defaults to "#")
```c
ec0.s10.binaryOutput01:=not(ec0.s10.binaryOutput01);
#println('State: ', ec0.s10.binaryOutput01);
```

### include and substitute
Since all PLC files and PLC libs are parsed through MSI the "include" and "substitute" commands can be used.

When using the include command, the file location dir of the file must be added in the INC parameter when loading the PLC:
```shell
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd,    "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Test', SAMPLE_RATE_MS=1000, PLC_MACROS='BO_S_ID=${ECMC_EC_SLAVE_NUM}'"
```
The "INC" parameter can contain several directories separated with a ":", making it possible to include PLC files from several locations/modules.

#### example: Toggle a few outputs
As a demo use case let's consider that a few outputs needs to be toggled.
NOTE: There are simpler ways to write this specific code but it's used to demo how code can be divided.

Lets first define some code that toggles a bit (toggle\_output.plc\_inc):
```shell
# Example of simple include file that toggles an binary output
${M}.s${BO_S_ID}.binaryOutput${BO_CH}:=not(${M}.s${BO_S_ID}.binaryOutput${BO_CH});
${DBG=#}println('State: ', ${M}.s${BO_S_ID}.binaryOutput${BO_CH});

```
This code snippet then can be included in a main plc-file by using the "include" keyword.
Each include can then be included with different macros by using the "substitute" keyword:
```C
substitute "BO_CH=01"
include "toggle_output.plc_inc"

substitute "BO_CH=02, DBG="
include "toggle_output.plc_inc"
```
The above code would expand to:
```C
ec0.s10.binaryOutput01:=not(ec0.s10.binaryOutput01);
#println('State:', ec0.s10.binaryOutput01);

ec0.s10.binaryOutput02:=not(ec0.s10.binaryOutput02);
println('State: ', ec0.s10.binaryOutput02);
```
The resulting code will toggle two different outputs, the state of the last output will be printed.

NOTE: Macros cannot be used in the filename when including a file. Instead the dir should be defined in the INC param when loading the PLC, see above.

### printouts

There are two good ways to handle printouts:
1. `plc<id>.dbg` or `${SELF}.dbg` flag: Accessible bit from generic plc panel. Printouts can be switched on/off in runtime.
2. MACROS: Mask priontouts with dbeug macros. IOC needs to be restated with a different MACRO value in order to change state of printouts.

#### `plc<id>.dbg` or `${SELF}.dbg`

The variable `plc<id>.dbg` or `${SELF}.dbg` can be used to turn on and of debug printouts for an PLC:
```C
if(${SELF}.dbg) {
  println('Time:            ',ec_get_time());
  println('Time MONO:       ',ec_get_time_frm_src(1));
  println('Time REAL:       ',ec_get_time_frm_src(0));
};
```
This allows turning on/off printouts in runtime by writing to the `<prefix>PLC<id>-DbgCmd` PV which is accessible in the generic plc panel (can be started from ecmcMain.ui).

{{% notice warning %}}
Only use the `plc<id>.dbg` variable for dbg purpose. It should always be safe to write to this variable.
{{% /notice %}}

#### MACROS
Adding a DBG macro can be useful to be able to turn on/off printouts. Typically during commissioning it can be useful to have many printouts, but later when system goes into production, it could be a good idea to turn (some) printouts off.

Example of a printout that can be turned on/off (default off)
```C
${DBG=#}println('Value: ', ${M}.s${BO_S_ID}.binaryOutput${BO_CH});
```
Will result in the below if setting the DBG='' (and some other macros, see above):
```C
println('Value: ', ec0.s10.binaryOutput01);
```

### Description
Always add a description when creating a PLC by setting the DESC macro when calling loadPLCFile.cmd.

Example:
```shell
${SCRIPTEXEC} ${ecmccfg_DIR}loadPLCFile.cmd,    "FILE=./cfg/main.plc, INC=.:./cfg/, DESC='Toggle some bits', SAMPLE_RATE_MS=1000, PLC_MACROS='BO_S_ID=${ECMC_EC_SLAVE_NUM}'"
```

{{% notice info %}}
The description can maximum be 40 chars long.
{{% /notice %}}

### Common PLC lib
In ecmccfg/plc_lib some code snippets are accessible. These are installed in ecmccfg module and can be accesses in ${ecmccfg_DIR}.

Sofar, the following code is accessible:
* Homing of abs encoder with overflow
* Synchronization kinematics and state machine (master-slave)

### Variable declaration

By declaring variables the ecmc plc code will be simpler to read. A declaration block needs to be added starting with "VAR" and ending with "END_VAR":
```
VAR
  <declarations>
END_VAR
<plc code>
```

The declaration needs to comply with the following syntax:
```
VAR
  <var_name> : <address>;
END_VAR
```

The following "addresses" are supported:
* global:
  - `global.<name>`
* static
  - `static.<name>`
* ethercat
  - `ec<mid>`
  - `ec<mid>.s<sid>`
  - `ec<mid>.s<sid>.<name>`
* motion:
  - `ax<id>`
  - `ax<id>.traj`
  - `ax<id>.enc`
  - `ax<id>.drv`
  - `ax<id>.mon`
  - `ax<id>.traj.<name>`
  - `ax<id>.enc.<name>`
  - `ax<id>.drv.<name>`
  - `ax<id>.mon.<name>`
* data storage:
  - `ds<id>`
  - `ds<id>.<name>`
* plc:
  - `plc<id>`
* constants
  - `<name>`

The variables will then be replaced/substituted with the addresses during load time.

Example of plc file with declaration section and code section:
```
VAR
  // Globals
  gTest          : global.test;

  // Statics
  sTest          : static.test;

  // EtherCAT I/0
  actPos         : ${M}.s${DRV_SID}.positionActual01;
  mySlave        : ${M}.s${DRV_SID};
  coolingValveBO : ${M}.s${BO_SID=2}.binaryOutput02;

  // Axis data
  targetPos      : ax${AX_ID=1}.traj.targetpos;
  myAxis         : ax1;
  myTraj         : ax${AX_ID=1}.traj;

  // Data storage
  buffer         : ds${DS_ID=0};

  // Constants
  pi             : 3.1415;

  // PLC
  myPLC          : ${SELF}

END_VAR

coolingValveBO:=not(coolingValveBO);

println('mySlave.controlWord: ', mySlave.driveControl${CH=01});

if(myTraj.targetpos<>static.oldTarget) {
  println('new target: ',myTraj.targetpos );
};

static.oldTarget := myTraj.targetpos;

if(gTest+ 1 > 10+sTest+mySlave.positionActual01) {
  println('actPos:', actPos);
};

if(gTest+ 1> 10+mySlave.positionActual01) {
  println('actPos:', actPos);
};
static.pini:=1;

println('actPos:', actPos, ' myAxis enc: ', myAxis.enc.actpos+pi);
gTest += 1;

println('buffer index: ', buffer.index);
if(myTraj.setpos>0) {
    myTraj.setpos+=1;
}
```

As an example, the first row of the code section:
```
coolingValveBO:=not(coolingValveBO);
```
will be converted to:
```
${M}.s${BO_SID=2}.binaryOutput02:=not(${M}.s${BO_SID=2}.binaryOutput02);
```
and:

```
if(gTest+ 1 > 10+sTest+mySlave.positionActual01) {
```
will be converted to:
```
if(global.test+ 1 > 10+static.test+${M}.s${DRV_SID}.positionActual01) {
```

### Link static and global variables to EPICS PVs

PLC variables are exposed on the ecmc asyn port and can then be wrapped by normal
EPICS records.

The asyn naming convention is:

- PLC-local static variable: `plcs.plc<id>.static.<name>`
- Global variable: `plcs.global.<name>`

Examples:

- `plcs.plc0.static.seqStep`
- `plcs.plc0.static.doMotion`
- `plcs.global.mode`

#### Preferred way: use the wrapper scripts

For numeric values:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd \
  "NAME=M1-State,PLC_VAR=seqStep,EGU=step,PREC=0"
```

For boolean values:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd \
  "NAME=M1-DoMtn,PLC_VAR=doMotion,ONAM=Run,ZNAM=Stop"
```

For a global variable:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd \
  "NAME=Mode,PLC_VAR=mode,SCOPE=global,ONAM=Remote,ZNAM=Local"
```

These scripts load the new templates:

- `ecmcPlcVarAnalog.db` creates `$(DEV):$(NAME)` as an `ao`
- `ecmcPlcVarBinary.db` creates `$(DEV):$(NAME)` as a `bo`

So the examples above create PVs such as:

- `$(IOC):M1-State`
- `$(IOC):M1-DoMtn`
- `$(IOC):Mode`

`DEV` defaults to `IOC`, but a different prefix can be provided:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd \
  "DEV=IOC_TEST,NAME=Counter,PLC_VAR=counter,EGU=counts,PREC=0"
```

Extra record macros can be passed directly through the script call, either as
named script parameters like `EGU`, `PREC`, `ESLO`, `EOFF`, `DESC`, `HOPR`,
`LOPR`, `DRVH`, and `DRVL`, or through `DB_MACROS` for less common fields.

Example with extra template macros:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarAnalog.cmd \
  "NAME=Counter,PLC_VAR=counter,EGU=counts,PREC=0,DB_MACROS='HHSV=MAJOR,HSV=MINOR'"
```

`PLC_VAR` supports these forms:

- `counter`: resolved as `plcs.plc${ECMC_PLC_ID}.static.counter`
- `static.counter`: resolved as `plcs.plc${ECMC_PLC_ID}.static.counter`
- `global.mode`: resolved as `plcs.global.mode`
- `plcs.plc3.static.counter`: used as-is

For bare names that should be global, set `SCOPE=global`:

```iocsh
${SCRIPTEXEC} ${ecmccfg_DIR}addPlcVarBinary.cmd \
  "NAME=Mode,PLC_VAR=mode,SCOPE=global,ONAM=Remote,ZNAM=Local"
```

`PLC_ID` can be provided explicitly, but after `loadPLCFile.cmd` it normally
does not need to be, because it defaults to the last loaded PLC id from
`ECMC_PLC_ID`.

#### Legacy way: load the older record templates directly

The older `Set...-RB` naming is still available:

```iocsh
dbLoadRecords("ecmcPlcAnalog.db",
              "P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc${ECMC_PLC_ID}.static.seqStep,REC_NAME=-M1-State")
dbLoadRecords("ecmcPlcBinary.db",
              "P=$(IOC):,PORT=MC_CPU1,ASYN_NAME=plcs.plc${ECMC_PLC_ID}.static.doMotion,REC_NAME=-M1-DoMtn")
```

These records are also useful when EPICS should both write the PLC variable and read
back its current value, but the new wrapper scripts provide the cleaner `DEV:NAME`
PV naming.

#### When to use `static` and when to use `global`

- Use `static` for values owned by one PLC, for example a state machine step,
  command bit, or internal setpoint.
- Use `global` for values that must be shared between several PLCs or between a
  PLC and a common EPICS control PV.

#### Custom records for one-way links

If a plain input or output record is needed instead of the standard readback
template, link directly to the same asyn name.

Read a PLC variable into EPICS:

```db
record(ai,"$(P)FromPLC"){
  field(DTYP, "asynFloat64")
  field(INP,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=0))T_SMP_MS=$(T_SMP_MS=1000)/TYPE=asynFloat64/plcs.plc0.static.toEpics?")
  field(SCAN, "I/O Intr")
}
```

Write an EPICS value into a PLC variable:

```db
record(ao,"$(P)ToPLC"){
  field(DTYP, "asynFloat64")
  field(OUT,  "@asyn($(PORT),$(ADDR=0),$(TIMEOUT=0))T_SMP_MS=$(T_SMP_MS=1000)/TYPE=asynFloat64/plcs.plc0.static.fromEpics=")
  field(SCAN, "Passive")
}
```

Notes:

- `?` at the end of the asyn path reads a value.
- `=` at the end of the asyn path writes a value.
- `PORT` is normally `MC_CPU1`.
- For boolean variables, use `addPlcVarBinary.cmd`, `ecmcPlcBinary.db`, or `asynInt32`.
