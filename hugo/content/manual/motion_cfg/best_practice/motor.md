
+++
title = "Motor record"
weight = 30
chapter = false
+++

## Topics
1. [Auto-save restore](#auto-save-restore)
2. [Open loop stepper with retries](#open-loop-stepper-with-retries)
3. [No motor record](#no-motor-record)

## Auto-save restore
Test IOC for open loop stepper motor with auto-save-restore
The example is based on that PSI ioc install tool is used.

### Auto save restore configurations
Auto save/restore of motor position is made through motor record.
At PSI if the tool "ioc install" is used, its enough to add a file \<ioc_name\>_pos.req in the "./cfg/" sub dir listing the DVAL field of the motor record names that need to be auto saved restored.

In order for restore of motor position to succeed, both restore pass 1 and 2 needs to executed (see EPICS hooks).

**NOTE: Auto save restore will only work with incremental encoders (in axis definition YAML file, "encoder.type: 0").**

### Example of a _pos.req file in ./cfg/
ioc install automatically adds restore at both passes ("#ENABLE-PASS=2") if filename ends with  "_pos.req"
```
MTEST04-MTN-ASM:Axis1.DVAL
```
#### Example of a x.req file in ./cfg/

If the file is named something else (without ending with "_pos.req") then also "#ENABLE-PASS=2" needs to be added:
```
#ENABLE-PASS=2
MTEST04-MTN-ASM:Axis1.DVAL
```
## Open loop stepper with retries
The motion axis in this example is configured to move in open loop but executing retries based on an absolute encoder.

### General configuration
Two encoders are configured for the motion object:
* **01**: BISS-C absolute encoder
* **02**: Open loop counter

The system will startup with the open loop encoder as primary (used for control) and the motor record are configured to use retries to control on the absolute BISS-C encoder.

### Motor record
Important motor record fields are:
1. **RTRY** : Max retry count
2. **RMOD** : Retry Mode
3. **UEIP** : Use encoder if present
4. **RDBD** : Retry deadband
5. **URIP** : Use RDBL Link If Present
6. **RDBL** : Readback link (position from an EPICS variable)

#### RTRY : Max retry count
maximum retry count. Needs to be set to a number higher than 0

### RMOD : Retry Mode
Can be set to:
* 0: "Unity"
* 1: "Arithmetic"
* 2: "Geometric"
* 3: "In-Position"

Use setting 1 or 2 for this test, for more information read motor record doc.

#### UEIP : Use encoder if present
Not used in this test. Set to 0.

#### RDBD : Retry deadband

Set to 0.01mm in this test (motor record will execute new mode if outside this limit).

#### URIP : Use RDBL Link If Present
Set to 1

#### RDBL : Readback link (position from EPICS variable)
This should be a record holding the value for control, could any PV. In this example another configured encoder is used

In this example the axis encoder 01 `<prefix>:<axis_name>-Enc<enc_id>-PosAct`

#### Feed settings to motor record by `epics.motorRecord.fieldInit` var:

Any vars added to `epics.motorRecord.fieldInit` will be forwarded to motor record at init:

```
##### Pass extra parameters to motor record:
# RTRY : Max retry count
# RMOD : Retry Mode
# UEIP : Use encoder if present
# RDBD : Retry deadband
# URIP : Use RDBL Link If Present
# RDBL : Readback link (position from an EPICS variable)

epics:
  name: ${AX_NAME=M1}                                 # Axis name
  precision: 3                                        # Decimal count
  description: Test cfg                               # Axis description
  unit: mm                                            # Unit
  motorRecord:
    syncSoftLimits: False
    fieldInit: 'FOFF=Frozen,RRES=1.0,RTRY=2,RMOD=1,UEIP=0,RDBD=0.1,URIP=1,RDBL=$(IOC):${AX_NAME=M1}-Enc${RTRY_ENC_CH=01}-PosAct'
```
**NOTE: Do not use "CP" on the RDBL link...**

### Running the test

1. Start:
```
iocsh.bash startup.cmd
```
2. Run positioning commands:
```
dbpf IOC_TEST:Axis1 10
```
Now the motion should be going stepwise (depending on RTRY) and end up in:
1. ecmc act pos = 10/0.95
2. motor record act pos = 10

NOTE: JOGGING is not supported (motor record will stop any started JOGGING cmd)

### Stop on RDBL pv alarms
Motor record stops motion if the RDBL linked PV is in alarm state (MAJOR or INVALID) independent on if severity propagation is set (disregarding NMS,MS,MSS...)

The simulated position is configured like this:
```
  field(LOW,  "-50")
  field(LOLO, "-60")
  field(HIGH, "50")
  field(HIHI, "60")
```

**IMPORTANT:** If you use an incremental encoder linked to calc record, you can sometimes experience stops during homing sequence since then the motion axis might go outside of the alarm limits defined. Normally motor record driver will not update the position during homing but I will happen for instance when activating limit switch or homing switch. Then a stop could occur
This is of course no problem if the RDBL linked value is absolute like intended.

### How to move when RDBL alarm interlock

If motion is interlocked by the RDBL alarm then motion can be executed by setting the URIP to 0 (disabling RDBL).
```
dbpf IOC_TEST:Axis1.URIP 0
```
Motion can now be executed.
Note: The RDBL link are now not used (retries based on RDBL will not be executed)

## No motor record

In yaml configuration use `epics.motorRecord.enable = False`:
```
epics:
  name: ${AX_NAME=M1}                                 # Axis name
  precision: 3                                        # Decimal count
  description: Test cfg                               # Axis description
  unit: mm                                            # Unit
  motorRecord:
    enable: False
```
