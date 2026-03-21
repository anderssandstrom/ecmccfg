+++
title = "Drive modes CSV, CSP, CSP-PC"
weight = 18
chapter = false
+++

## Scope

Three main motion modes are commonly used with ecmc and supported drives:

- `CSV`: Cyclic Synchronous Velocity, velocity setpoint sent to the drive
- `CSP`: Cyclic Synchronous Position, position setpoint sent to the drive
- `CSP-PC`: Cyclic Synchronous Position with centralized position control

Other modes also exist, for example cyclic synchronous torque. These can still
be used from PLC logic or EPICS logic, but they are not supported by the ecmc
axis object.

## Which mode to choose

- Use `CSV` when ecmc should run the position loop and the feedback does not
  need to be directly connected to the drive.
- Use `CSP` when the drive should run the position loop.
- Use `CSP-PC` when the drive runs one position loop and ecmc runs an
  additional centralized position loop, typically with a second encoder.

### Control loops

The control loops are executed at different locations depending on which mode:

|          | Current loop | Velocity loop | Position loop  |Comment|
| -------- | ------------ | ------------- |--------------- |-------|
| CSV      | drive        | drive         | ecmc           |       |
| CSP      | drive        | drive         | drive          | ecmc generates trajectory |
| CSP-PC   | drive        | drive         | drive and ecmc | dual position loop |

#### CSV
This is the most common mode for smaller drives such as stepper terminals.
In CSV the position loop is centralized in ecmc. That means that any EtherCAT
feedback can be used, not only a source connected directly to the drive. This
flexibility is the main reason why CSV is so common in smaller motion systems.

Common CSV use case:
- motion stage driven by an open-loop stepper motor connected to EL7041
- linear feedback from an absolute encoder connected to EL5042

ecmccfg configurations normally default to CSV, with one important exception:
- SmarAct MCS2 EC does not support CSV

In CSV the centralized position controller is normally a simple P controller, so
often only `Kp` needs tuning. Depending on the hardware, drive tuning may still
also be needed.

#### CSP
In pure CSP, the position loop is executed in the drive. That means that the
encoder used by the drive loop must be connected directly to the drive. The
trajectory is still generated centrally in ecmc.

CSP is therefore more common for larger servo drives where the motor already
has an encoder or where the drive supports multiple encoders. CSP normally
performs better than CSV because the position loop is closer to the hardware.
The tradeoff is reduced flexibility. EL7041 does not support CSP, while EL7062
does.

To configure a drive in CSP or CSP-PC, the slave is normally selected with the
`_CSP` suffix:
```
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,      "SLAVE_ID=3,HW_DESC=EL7062_CSP"
```
In CSP, the ecmc position control parameters are not active. Depending on the
hardware, drive tuning may still be needed.

#### CSP-PC
CSP-PC is basically CSP with the ecmc position loop also enabled. That gives
two position loops, one in the drive and one in ecmc. The normal idea is that
the loops work with different encoders. A meaningful CSP-PC configuration
therefore normally contains at least two encoders.

See "Hardware support below" to understand which drives support the different modes.

To run in CSP-PC the drive must still be configured in CSP mode:

```
axis:
  id: ${AXIS_ID=1}                                    # Axis id
  mode: CSP
```
Additionally, the system must know which encoder is connected to the drive.
That is configured with `useAsCSPDrvEnc`. This encoder is used for the
position loop in the drive.

Typical choices:
- open-loop counter
- absolute rotary encoder from an EL72xx or AM81xx encoder
- incremental encoder connected to EL7062
```
encoder:
  desc: CSP drive encoder
  ...
  useAsCSPDrvEnc: 1    # use this encoder as CSP drive encoder
  ...
```
Finally, the encoder for the centralized loop must be defined. This is normally
done by adding another encoder with `primary: 1`:
```
encoder:
  desc: Linear encoder
  type: 1
  ...
  primary: 1
  ...
```
In CSP-PC, the ecmc position control loop is active, so the ecmc position
controller parameters need tuning. Since a position setpoint is sent to the
drive, a PI controller is normally needed, so both `Kp` and `Ki` often need
tuning.

#### Hardware support

Current support for some common drives used with ecmc:
|          | CSV        | CSP         | CSP-PC      |Comment|
| -------- | ---------- | ------------|------------ |-------|
| Ex704x   | yes        | no          | no          | |
| Ex703x   | yes        | no          | no          | |
| EL7062   | yes        | yes         | yes         | Firmware bug fix needed for CSV |
| Ex72xx   | yes        | yes         | yes         | |
| EL7411   | yes        | yes         | yes         | Not used yet |
| MCS2 EC  | no         | yes         | yes         | |
| iPOS4808 | yes        | no          | no          | |
