#!/bin/bash
# usage: run_all.sh <run-copy> <evidence-dir>
# Runs the eleven commands of FABLE_RC_REVIEW_PROMPT.md, unmodified, in order.
cwd="$1"; ev="$2"
mkdir -p "$ev"
: > "$ev/exit-codes.txt"
run() {
  label="$1"; shift
  cd "$cwd" || exit 97
  start=$(date +%s)
  "$@" >"$ev/$label.stdout.txt" 2>"$ev/$label.stderr.txt"
  code=$?
  end=$(date +%s)
  echo "$label|exit=$code|seconds=$((end-start))|cmd=$*" >> "$ev/exit-codes.txt"
}
run 01-fable-rb-probes python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
run 02-fable-ra-probes python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
run 03-make-test make test
run 04-make-check make check
run 05-make-batch2-gate make batch2-gate
run 06-make-reverification-gate make reverification-gate
run 07-make-acceptance-gate make acceptance-gate
run 08-make-rb-gate make rb-gate
run 09-make-rc-gate make rc-gate
run 10-check-product-requirements-json python3 scripts/check_product_requirements.py --json
run 11-register-faults python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
echo DONE >> "$ev/exit-codes.txt"
