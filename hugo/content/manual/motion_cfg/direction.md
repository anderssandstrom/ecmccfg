+++
title = "direction of motion"
weight = 20
chapter = false
+++

The direction of motion can be affected in several ways:
on the [slave level](#ethercat-slave), in [axis scaling](#ecmc-scaling), or in the [EPICS motor record](#epics-motor-record).

{{% notice tip %}}
The best option is to change direction at the slave level. The alternatives can lead to unintuitive scaling factors or mismatches between ECMC and EPICS.
{{% /notice %}}

## EtherCAT slave

ecmccfg allows SDOs to be set in the IOC startup script or in dedicated slave configuration files.
As most slaves have an SDO to invert the direction of motion or counting, it's only natural to make use of this feature.
The benefit of changing the direction on the slave is obvious.
All axes move in their natural direction, as given by the machine coordinate system.
Limit switches - consequently - are always where they belong, even non-experts can diagnose the device or system.
Examples for encoder and drive are given below.

{{% notice info %}}
Consult the respective slave manual for the correct SDO.
{{% /notice %}}

### Encoder direction

In many cases, inversion of the encoder value is possible in the EtherCAT slave.
By using the `INV_DIR` macro with `applyComponent.cmd`, the direction can be changed.

{{% notice info %}}
For EL5042 (example below), inversion can lead to a very high number since the data size is 64-bit. Therefore, it is advisable to invert the sign in the axis configuration instead.
{{% /notice %}}

```shell
# slave 7 {ecmcEL5042}
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL5042"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=1, MACROS='INV_DIR=1'"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Encoder-RLS-LA11-26bit-BISS-C,CH_ID=2, MACROS='INV_DIR=1'"
```

### Drive direction
```shell
# slave 18 {ecmcEL7041}
${SCRIPTEXEC} ${ecmccfg_DIR}addSlave.cmd,       "HW_DESC=EL7041"
${SCRIPTEXEC} ${ecmccfg_DIR}applyComponent.cmd "COMP=Motor-Generic-2Phase-Stepper, MACROS='I_MAX_MA=1000, I_STDBY_MA=500, U_NOM_MV=48000, R_COIL_MOHM=1230,INV_DIR=1'"
```

## ecmc scaling

A negative numerator can be used to change the direction of motion.
Refer to the [scaling]({{< relref "/manual/motion_cfg/scaling.md" >}}) section for details.

{{% notice info %}}
This results in negative values for `MRES` in the motor record.
{{% /notice %}}

## EPICS motor record

The `epics` key in the [axis config]({{< relref "/manual/motion_cfg/axisYaml.md" >}}) allows motor record fields to be initialized.
By initializing the `DIR` field to `Neg`, the motor record starts inverted.

```yaml
epics:
  name: reversedAxis
  precision: 1
  unit: deg
  motorRecord:
    enable: yes
    description: "inverted"
    fieldInit: "DIR=Neg"
```

{{% notice warning %}}
This affects only the motor record; ECMC internally still moves in the _wrong_ direction.
{{% /notice %}}
