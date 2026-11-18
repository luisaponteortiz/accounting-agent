#!/bin/bash
# Runs the six prescribed commands from a disposable copy of the RA checkpoint.
# usage: run_gates.sh <project-root-copy> <evidence-dir>
ROOT="$1"; OUT="$2"; cd "$ROOT" || exit 2
{ echo "date: $(date -u +%FT%TZ)"; uname -a; python3 --version; make --version | head -1; sqlite3 --version 2>/dev/null; python3 -c "import sqlite3;print('python sqlite',sqlite3.sqlite_version)"; } > "$OUT/versions.txt" 2>&1
: > "$OUT/exit-codes.txt"
run() { name="$1"; shift; "$@" > "$OUT/$name.stdout.txt" 2> "$OUT/$name.stderr.txt"; code=$?; echo "$name exit=$code cmd=$*" >> "$OUT/exit-codes.txt"; }
run make-test make test
run make-check make check
run make-batch2-gate make batch2-gate
run make-reverification-gate make reverification-gate
run make-acceptance-gate make acceptance-gate
run original-full-acceptance python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .
run original-full-reverification python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .
cat "$OUT/exit-codes.txt"
