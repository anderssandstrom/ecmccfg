#!/usr/bin/env bash
# Monitor motor record fields using the normal EPICS camonitor output.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bash utils/camonitor_motor.sh AXIS_PREFIX [camonitor options ...]
       bash utils/camonitor_motor.sh AXIS_PREFIX --list

AXIS_PREFIX is the complete motor record name without a field suffix,
for example IOC:m1. Monitors IOC:m1.VAL, IOC:m1.RBV, IOC:m1.MSTA, etc.

Examples:
  bash utils/camonitor_motor.sh IOC:m1
  bash utils/camonitor_motor.sh IOC:m1 -n -t cI
  bash utils/camonitor_motor.sh IOC:m1 --list

Uses camonitor from PATH and the normal EPICS_CA_* environment settings.
Prints value/alarm monitor events; Ctrl+C stops monitoring. No PV writes.
--list prints the PV names without connecting. Other options go to camonitor.
Older motor versions may not provide every field in the list.
EOF
}

if [[ $# -eq 0 ]]; then
    usage >&2
    exit 2
fi
if [[ $1 == -h || $1 == --help ]]; then
    usage
    exit 0
fi
axis_prefix=$1
shift
if [[ -z $axis_prefix || $axis_prefix == -* || $axis_prefix == *[[:space:]]* ]]; then
    echo "Error: provide a motor record prefix, for example IOC:m1." >&2
    exit 2
fi

# Public fields from motorRecord.dbd (motorECMC 7.2.8.1), plus commonly
# monitored dbCommon fields. Internal DBF_NOACCESS fields are excluded.
fields=(
    DESC DTYP SCAN PINI PHAS EVNT TSE TSEL DISV DISA SDIS DISS DISP
    PROC PACT UDF STAT SEVR NSTA NSEV ACKS ACKT ASG FLNK
    VERS OFF FOFF FOF VOF DIR SET SSET SUSE VELO VBAS VMAX S SBAS SMAX
    ACCL ACCS ACCU BDST BVEL SBAK BACC FRAC OUT CARD RDBL DOL OMSL RLNK
    SREV UREV MRES ERES RRES UEIP URIP PREC EGU RHLM RLLM HLM LLM DHLM
    DLLM HOPR LOPR HLS LLS RHLS RLLS HIHI LOLO HIGH LOW HHSV LLSV HSV
    LSV HLSV MISV RDBD SPDB RCNT RTRY MISS SPMG LSPG STOP HOMF HOMR JOGF
    JOGR TWF TWR TWV VAL DVAL RVAL RLV RBV DRBV DIFF RDIF CDIR RRBV RMP
    REP RVEL DMOV MOVN MSTA MFLG LVIO TDIR ATHM PP MIP MMAP NMAP DLY
    PCOF ICOF DCOF CNEN INIT PREM POST STOO DINP MINP RINP JVEL JAR LOCK
    NTM NTMF HVEL STUP RMOD ADEL MDEL SYNC IGSET SPAM RSTM
)
pvs=()
for field in "${fields[@]}"; do
    pvs+=("${axis_prefix}.${field}")
done

if [[ ${1:-} == --list ]]; then
    if [[ $# -ne 1 ]]; then
        echo "Error: --list cannot be combined with camonitor options." >&2
        exit 2
    fi
    printf '%s\n' "${pvs[@]}"
    exit 0
fi
if ! command -v camonitor >/dev/null 2>&1; then
    echo "Error: camonitor is not on PATH. Load your EPICS Base environment first." >&2
    exit 1
fi

exec camonitor "$@" "${pvs[@]}"
