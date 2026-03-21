+++
title = "data storage buffer"
weight = 13
chapter = false
+++

## Scope

Data storage buffers are used when values should be collected over time and then
pushed to EPICS as waveform data.

Use data storage when:

- values should be buffered in the realtime context
- waveform updates should happen only on a trigger
- a PLC should decide when buffered data is published to EPICS

The corresponding public best-practice example is:

- `examples/PSI/best_practice/general/data_storage/`

The active waveform data can be read from:

- `<IOC>:ds0-Data-Act`

## Two common patterns

1. append continuously and push to EPICS on a hardware event
2. append continuously and push to EPICS on an EPICS trigger PV

Custom scale and offset can be applied directly in the PLC expression by using
macros in the startup file.

## 1. Push to EPICS by hardware trigger

One common pattern is to push the waveform on a hardware event, for example a
falling edge of a limit switch.

PLC code:

```text
##################################################################################
# PLC to add encoder data to dataStorage and push data on falling edge of high limit
#
# MACROS:
#   DS_ID    = ID of ds to use as a filter id
#   PLC_ID   = ID of this PLC
#   ENC_S_ID = Slave id of encoder terminal
#   DBG      = Set to empty string to get printouts, set to "#" to avoid printouts
#   SCALE    = Encoder scale value, defaults to 1
#   OFFSET   = Encoder offset value, defaults to 0
#

# Append data to storage
ds_append_data(${DS_ID},ec0.s${ENC_S_ID}.positionActual01*${SCALE=1}+${OFFSET=0});

# Trigger push of data on falling edge of limit switch
if(static.highlimOld and not(ax1.mon.highlim)) {
  ${DBG=#}println('Pushing data to EPICS....');
  ds_push_asyn(${DS_ID});
};

static.highlimOld:=ax1.mon.highlim;
```

## 2. Push to EPICS by EPICS trigger PV

In the best-practice example, the data stored in data storage `0` is pushed to
EPICS on a rising edge of the `<IOC>:Set-PushDataTrigger-RB` PV.

Start the example with:

```bash
iocsh.bash startup.cmd
```

Trigger writes to EPICS with:

```text
dbpf <IOC>:Set-PushDataTrigger-RB 1
dbpf <IOC>:Set-PushDataTrigger-RB 0
dbpf <IOC>:Set-PushDataTrigger-RB 1
```

PLC code:

```text
##################################################################################
# PLC to generate a signal, append it to dataStorage, and push it on trigger
#
# MACROS:
#   DS_ID    = ID of ds to use as a filter id
#   DBG      = Set to empty string to get printouts, set to "#" to avoid printouts
#

static.signal += 1;
ds_append_data(${DS_ID}, static.signal);

# Trigger push of data on rising edge of trigger
if(static.trigg and not(static.triggOld)) {
  ${DBG=#}println('Pushing data to EPICS....');
  ds_push_asyn(${DS_ID});
};

static.triggOld:=static.trigg;
```

## Related pages

- [general best practice]({{< relref "/manual/general_cfg/best_practice.md" >}})
- [script reference]({{< relref "/manual/general_cfg/script_reference.md" >}})
- [PLC best practice]({{< relref "/manual/PLC_cfg/best_practice.md" >}})
