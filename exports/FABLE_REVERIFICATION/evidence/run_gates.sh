#!/bin/bash
# Runs the delivered gates in a disposable working copy and records exit codes.
W="$1"; OUT="$2"
cd "$W" || exit 2
run() { name="$1"; shift; echo "=== $name: $* ===" > "$OUT/$name.txt"; ( "$@" ) >> "$OUT/$name.txt" 2>&1; code=$?; echo "=== exit code: $code ===" >> "$OUT/$name.txt"; echo "$name exit=$code" >> "$OUT/exit_codes.txt"; }
: > "$OUT/exit_codes.txt"
cp docs/batch2/final-validation.json "$OUT/delivered-final-validation.json"
run 01_corrective_checkpoint python3 scripts/verify_corrective_checkpoint.py
run 02_make_test make test
run 03_make_check make check
run 04_make_batch2_gate make batch2-gate
run 05_cases_batch2_gate python3 review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate
run 06_maintained_probes python3 review/batch2_verification_probes.py .
run 07_synthetic_month python3 scripts/synthetic_month.py
echo done >> "$OUT/exit_codes.txt"
