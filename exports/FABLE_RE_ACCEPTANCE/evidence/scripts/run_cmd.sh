#!/bin/bash
# usage: run_cmd.sh LABEL CWD cmd...
L="$1"; C="$2"; shift 2
O=/tmp/fre/out
cd "$C" || exit 99
S=$(date -u +%Y-%m-%dT%H:%M:%SZ); T0=$(date +%s)
"$@" >"$O/$L.stdout.txt" 2>"$O/$L.stderr.txt"; E=$?
T1=$(date +%s)
printf '{"label":"%s","cwd":"%s","argv":"%s","started_utc":"%s","elapsed_seconds":%d,"exit_code":%d}\n' "$L" "$C" "$*" "$S" $((T1-T0)) $E > "$O/$L.json"
echo "$L exit=$E elapsed=$((T1-T0))s" >> "$O/_progress.txt"
