# Best practice for ecmc

## General

### Data storage
* Data-storage buffer without EtherCAT hardware
* PLC-generated signal buffered with `addDataStorage.cmd`
* Push to EPICS on demand through an exposed PLC trigger PV

## Motion

### stepper and BISS-C
* Stepper motor
* RLS BISS encoder
* Open loop encoder

### stepper and BISS-C using hw substitution file
* Stepper motor
* RLS BISS encoder
* Open loop encoder

### Servo
* EL72xx servo equipped with a AM8111 motor with absolute encoder (OCT-version)

### SmarAct MCS2
* CSP motion with SmarAct MCS2
* Auto mode switching for homing and motion
* Linear and rotary YAML axis examples

### PVT
* Profile-move / PVT motion
* One-axis EL7041-0052 example
* Explicit `pvtControllerConfig.cmd` startup sequence

## PLC
* Macros
* include, substitute
