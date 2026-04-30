#!/usr/bin/env bash
# Randomly spam EPICS PVs with values in +/-10 range.
set -euo pipefail

PVS=(
  "c6025a-08:TR_HI"
  "c6025a-08:TR_LO"
  "c6025a-08:CENTERY"
  "c6025a-08:GAPY"
)

command -v caput >/dev/null 2>&1 || {
  echo "caput command not found. Ensure EPICS base is in PATH." >&2
  exit 1
}

delay="${1:-0.2}"

if [[ ! "$delay" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "Usage: $0 [delay_seconds]" >&2
  exit 1
fi

rand_value() {
  python3 - "$@" <<'PY'
import random
import sys
low, high = (float(arg) for arg in sys.argv[1:3])
print(f"{random.uniform(low, high):.4f}")
PY
}

while true; do
  for pv in "${PVS[@]}"; do
    value="$(rand_value -10 10)"
    echo "caput ${pv} ${value}"
    caputq "${pv}" "${value}"
  done
  sleep_time="$(rand_value 0 "$delay")"
  echo "sleep ${sleep_time}s"
  sleep "$sleep_time"
done
