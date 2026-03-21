+++
title = "data storage buffer"
weight = 13
chapter = false
+++

## data storage examples
The corresponding best-practice example is located in:

- `examples/PSI/best_practice/general/data_storage/`

1. Continuously add value to data storage. Push to epics by hw trigger.
2. Continuously add value to data storage. Push to epics by epics pv trigger.
Data buffered data can be accessed by the `<IOC>:ds0-Data-Act` waveform PV.

Custom scale and offset can be applied to the stored values by MACROS (to the plc) in the startup file.

### 1 push to epics by hw trigger

One common pattern is to push the waveform on a hardware event, for example a
falling edge of a limit switch.

PLC-code:
```
##################################################################################
# PLC to add encoder data to dataStorage and push data on falling edge of higlimit
#
# MACROS:
#   DS_ID    = ID of ds to use as a filter id
#   PLC_ID   = ID of this PLC
#   ENC_S_ID = Slave id of encoder terminal
#   DBG      = Set to empty string to get printouts, set to "#" to avoid printouts
# SCALE          = Encoder scale value, defaults to 1
# OFFSET         = Encoder offset value, defaults to 0
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

### 2 push to epics by epics pv trigger

In the best-practice example the data stored in dataStorage 0 is pushed to
EPICS at a rising edge of the `<IOC>:Set-PushDataTrigger-RB` PV.

The best-practice example uses a PLC-generated signal and is started with `startup.cmd`.
```
iocsh.bash startup.cmd
```

Trigger writes to EPICS by:
```
dbpf <IOC>:Set-PushDataTrigger-RB 1
dbpf <IOC>:Set-PushDataTrigger-RB 0
dbpf <IOC>:Set-PushDataTrigger-RB 1
```

PLC-code:
```
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
