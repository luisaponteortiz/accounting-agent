#!/bin/bash
# usage: run_cmd.sh <cwd> <evidence_dir> <label> <command...>
cwd="$1"; ev="$2"; label="$3"; shift 3
cd "$cwd" || exit 97
start=$(date +%s)
"$@" >"$ev/$label.stdout.txt" 2>"$ev/$label.stderr.txt"
code=$?
end=$(date +%s)
echo "$label|exit=$code|seconds=$((end-start))|cmd=$*" >> "$ev/exit-codes.txt"
