#!/bin/bash
echo "EtherCAT tool: ethecat master: Prefix=$2, Master=$1"

MID=$1
PREFIX=$2

# Busy
caput "${PREFIX}m${MID}-EcTool-Stat" "BUSY" > /dev/null 2>&1
caput "${PREFIX}m${MID}-EcTool-Prgs" 0 > /dev/null 2>&1

text="$(/opt/etherlab/bin/ethercat master | tr -d '\0')"

# Command to read EtherCAT master
caput -S ${PREFIX}m${MID}-EcTool-Msg "$text" > /dev/null 2>&1

echo "Read done"
caput "${PREFIX}m${MID}-EcTool-Prgs" 100 > /dev/null 2>&1

#echo "Progress: Done"
caput "${PREFIX}m${MID}-EcTool-Stat" "IDLE" > /dev/null 2>&1
