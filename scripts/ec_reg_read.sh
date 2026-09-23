#!/bin/sh

MASTER="$1"
SLAVE="$2"
TYPE="$3"
ADDR="$4"
VAR="$5"
OUT="$6"
FORMAT="${7:-DEC}"

case "$FORMAT" in
    HEX|hex) FIELD=1 ;;
    DEC|dec) FIELD=2 ;;
    *)
        printf 'Invalid register output format: %s (expected HEX or DEC)\n' "$FORMAT" >&2
        exit 1
        ;;
esac

VALUE=$(/opt/etherlab/bin/ethercat reg_read -m"$MASTER" -p"$SLAVE" -t "$TYPE" "$ADDR" | awk -v field="$FIELD" '{print $field}')

printf 'epicsEnvSet("%s", "%s")\n' "$VAR" "$VALUE" > "$OUT"
