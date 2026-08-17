#!/usr/bin/env bash

set -euo pipefail

# Usage: mxEnableDownstreamBaseplates.sh [MASTER_ID] [RESCAN_DELAY] [ETHERCAT_TOOL] [PORT]
# Note: Run this utility before addMaster.cmd claims the EtherCAT master.
MASTER_ID="${1:-0}"
RESCAN_DELAY="${2:-3}"
ETHERCAT_TOOL="${3:-/opt/etherlab/bin/ethercat}"
PORT="${4:-3}"
MAX_BASEPLATES="${MX_MAX_BASEPLATES:-32}"

if [[ ! "$MASTER_ID" =~ ^[0-9]+$ ]]; then
  echo "Error: master ID must be a non-negative integer." >&2
  exit 2
fi

if [[ ! "$RESCAN_DELAY" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "Error: rescan delay must be a non-negative number." >&2
  exit 2
fi

if [[ ! "$MAX_BASEPLATES" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: MX_MAX_BASEPLATES must be a positive integer." >&2
  exit 2
fi

if [[ ! "$PORT" =~ ^[0-3]$ ]]; then
  echo "Error: port must be an integer from 0 through 3." >&2
  exit 2
fi

if [[ ! -x "$ETHERCAT_TOOL" ]]; then
  echo "Error: EtherCAT tool is not executable: $ETHERCAT_TOOL" >&2
  exit 2
fi

declare -A opened=()
opened_count=0
printf -v dl_control_value '0x%08x' \
  "$((0x0007c001 & ~(3 << (8 + 2 * PORT))))"

while (( opened_count < MAX_BASEPLATES )); do
  slave_list="$("$ETHERCAT_TOOL" slaves -m "$MASTER_ID")"
  mb1120_sid=""

  while read -r sid; do
    if [[ "$sid" =~ ^[0-9]+$ && ! ${opened[$sid]+_} ]]; then
      mb1120_sid="$sid"
    fi
  done < <(awk 'toupper($0) ~ /MB1120/ {print $1}' <<< "$slave_list")

  if [[ -z "$mb1120_sid" ]]; then
    echo "No new MB1120 found. Discovered $opened_count junction(s)."
    printf '%s\n' "$slave_list"
    exit 0
  fi

  echo "Setting MB1120 port $PORT to Auto at master $MASTER_ID, slave position $mb1120_sid..."
  "$ETHERCAT_TOOL" reg_write -m "$MASTER_ID" -p "$mb1120_sid" \
    -e -t uint32 0x0100 "$dl_control_value"

  opened["$mb1120_sid"]=1
  ((opened_count += 1))

  sleep "$RESCAN_DELAY"
  "$ETHERCAT_TOOL" rescan -m "$MASTER_ID"
done

echo "Error: stopped after MX_MAX_BASEPLATES=$MAX_BASEPLATES; another MB1120 may remain." >&2
exit 1
