#!/bin/bash
# usage: search_job.sh LABEL ROOT FAMILY SHARD
R=/private/tmp/claude-501/rf
L="$1"; ROOT="$2"; FAM="$3"; SH="$4"
S=$(date -u +%Y-%m-%dT%H:%M:%SZ); T0=$(date +%s)
cd "$ROOT" && python3 $R/scripts/fable_rf_step_search.py . --family "$FAM" --shard "$SH" --json "$R/out/search/$L.results.json" > "$R/out/search/$L.stdout.txt" 2> "$R/out/search/$L.stderr.txt"; E=$?
T1=$(date +%s)
printf '{"label":"%s","root":"%s","family":"%s","shard":"%s","started_utc":"%s","elapsed_seconds":%d,"exit_code":%d}\n' "$L" "$ROOT" "$FAM" "$SH" "$S" $((T1-T0)) $E > "$R/out/search/$L.json"
echo "search $L exit=$E elapsed=$((T1-T0))s" >> "$R/out/_progress.txt"
