#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <ioc-name> <panel-pv> [caqtdm-macros]" >&2
  exit 1
fi

ioc_name="$1"
panel_pv="$2"
macro_string="${3:-}"

panel_path="$(caget -St "$panel_pv" 2>/dev/null || true)"
panel_path="${panel_path//$'\r'/}"
panel_path="${panel_path//$'\n'/}"

if [[ -z "$panel_path" ]]; then
  echo "cpp_logic panel path PV '$panel_pv' is empty" >&2
  exit 1
fi

if [[ "$panel_path" == /* ]]; then
  resolved_path="$panel_path"
elif [[ "$panel_path" == */* ]]; then
  resolved_path="/ioc/${ioc_name}/${panel_path}"
else
  resolved_path="/ioc/${ioc_name}/qt/${panel_path}"
fi

if [[ ! -f "$resolved_path" ]]; then
  echo "cpp_logic panel '$resolved_path' does not exist" >&2
  exit 1
fi

if [[ -n "$macro_string" ]]; then
  exec caqtdm "$resolved_path" -macro "$macro_string" &
else
  exec caqtdm "$resolved_path" &
fi
