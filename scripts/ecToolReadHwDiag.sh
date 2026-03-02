#!/bin/bash
echo "EtherCAT tool: Diagnosing: Prefix=$3, Master=$1, Slave=$2"
MID=$1
SID=$2
PREFIX=$3

# Busy
caput "${PREFIX}m${MID}-EcTool-Stat" "BUSY" > /dev/null 2>&1
caput "${PREFIX}m${MID}-EcTool-Prgs" 0 > /dev/null 2>&1

# Command to read diagnostics
text="$(python3 /ioc/NeedfulThings/ecmc_ec_scripts/ec_diagnostic_messages.py -m $MID -s $SID | tr -d '\0')"
caput -S ${PREFIX}m${MID}-EcTool-Msg "$text" > /dev/null 2>&1

echo "Read done"
caput "${PREFIX}m${MID}-EcTool-Prgs" 100 > /dev/null 2>&1

#echo "Progress: Done"
caput "${PREFIX}m${MID}-EcTool-Stat" "IDLE" > /dev/null 2>&1
