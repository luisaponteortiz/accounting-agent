#!/bin/bash
# Runs the delivered gates in a disposable working copy and records exit codes. No project files are edited by this script.
W="$1"; OUT="$2"
cd "$W" || exit 2
run() { name="$1"; shift; echo "=== $name: $* ===" > "$OUT/$name.txt"; ( "$@" ) >> "$OUT/$name.txt" 2>&1; code=$?; echo "=== exit code: $code ===" >> "$OUT/$name.txt"; echo "$name exit=$code" >> "$OUT/exit_codes.txt"; }
: > "$OUT/exit_codes.txt"
run 01_make_test make test
run 02_make_check make check
run 03_make_batch2_gate make batch2-gate
run 04_make_reverification_gate make reverification-gate
run 05_synthetic_month python3 scripts/synthetic_month.py
run 06_corrective_checkpoint python3 scripts/verify_corrective_checkpoint.py
run 07_original_supplied_probes python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .
run 08_cases python3 review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate
echo done >> "$OUT/exit_codes.txt"
