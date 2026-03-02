#!/bin/bash
echo "EtherCAT tool: ethecat slaves: Prefix=$2, Master=$1"

MID=$1
PREFIX=$2

# Busy
caput "${PREFIX}m${MID}-EcTool-Stat" "BUSY" > /dev/null 2>&1
caput "${PREFIX}m${MID}-EcTool-Prgs" 0 > /dev/null 2>&1

if [ $MID -lt 0 ]
then
text="$(/opt/etherlab/bin/ethercat slaves | tr -d '\0')"
else
text="$(/opt/etherlab/bin/ethercat slaves -m $MID | tr -d '\0')"
fi

# Command to read EtherCAT slaves
caput -S ${PREFIX}m${MID}-EcTool-Msg "$text" > /dev/null 2>&1

echo "Read done"
caput "${PREFIX}m${MID}-EcTool-Prgs" 100 > /dev/null 2>&1

#echo "Progress: Done"
caput "${PREFIX}m${MID}-EcTool-Stat" "IDLE" > /dev/null 2>&1
