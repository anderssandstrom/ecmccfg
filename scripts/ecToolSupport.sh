#!/bin/bash
# Shared validation for the installed EcTool helpers. No eval or shell command
# strings: values remain data even when helpers are called directly.
set -o pipefail

ecToolStatusOnExit() {
    local result=$?
    if (( result != 0 )); then
        caput "${PREFIX}m${MID}-EcTool-Stat" "ERROR" > /dev/null 2>&1
    fi
    return "$result"
}

ecToolInteger() {
    local value=$1 maximum=$2
    [[ $value =~ ^[0-9]+$ && ${#value} -le 10 ]] || return 1
    (( 10#$value <= maximum ))
}

ecToolValidate() {
    ecToolInteger "$MID" 2147483647 || return 1
    [[ $PREFIX != -* ]] || return 1
    if [[ ${SID+x} ]]; then ecToolInteger "$SID" 65535 || return 1; fi
    if [[ ${CID+x} ]]; then [[ $CID == 1 || $CID == 2 ]] || return 1; fi
}

ecToolReadUnsigned() {
    local output value
    output=$("$@") || return 1
    value=$(awk '{print $2}' <<< "$output")
    # All values consumed here are uint8/uint16/uint32, never expressions.
    ecToolInteger "$value" 4294967295 || return 1
    printf '%s\n' "$((10#$value))"
}
