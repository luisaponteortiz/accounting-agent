#!/bin/bash
# usage: run_cmds.sh <root> <outdir>  ; runs the required commands unmodified, capturing raw output and exit codes
ROOT="$1"; OUT="$2"; mkdir -p "$OUT"; cd "$ROOT" || exit 9
: > "$OUT/exit-codes.txt"
i=0
runc() { i=$((i+1)); n=$(printf '%02d' $i)-$1; shift; s=$(date +%s)
  "$@" > "$OUT/$n.stdout.txt" 2> "$OUT/$n.stderr.txt"; rc=$?
  echo "$n exit=$rc secs=$(( $(date +%s)-s )) :: $*" >> "$OUT/exit-codes.txt"; }
runc rc-probes python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .
runc order-search python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py .
runc rb-probes python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
runc ra-probes python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
runc make-test make test
runc make-check make check
runc batch2-gate make batch2-gate
runc reverification-gate make reverification-gate
runc acceptance-gate make acceptance-gate
runc rb-gate make rb-gate
runc rc-gate make rc-gate
runc rd-gate make rd-gate
runc register-json python3 scripts/check_product_requirements.py --json
runc rb-register-faults python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
echo DONE >> "$OUT/exit-codes.txt"
