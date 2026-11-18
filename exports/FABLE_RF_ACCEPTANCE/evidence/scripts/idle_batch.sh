#!/bin/bash
# Runs after every search and gate has finished: HTTP setup timing (idle and under equal load), then five consecutive make test.
R=/private/tmp/claude-501/rf; O=$R/out; X=$R/tools/run_cmd.sh; T=$R/scripts/http_setup_timing.py
while pgrep -f "fable_rf_step_search|fable_re_step_search|fable_rf_equivalence|verify_re_acceptance_review|unittest discover|search_job|eq_job" >/dev/null; do sleep 20; done
sleep 45
{ echo "== idle, before the five runs"; date -u +%Y-%m-%dT%H:%M:%SZ; uptime; python3 $T $R/rd_x 5; python3 $T $R/rf_x 5; python3 $T $R/re_x 5
  for n in 8 16; do
    echo "== $n busy processes, RD then RF then RD then RF (same load for both)"; uptime
    for i in $(seq $n); do python3 $R/tools/burn.py 200 & done; sleep 3
    python3 $T $R/rd_x 4; python3 $T $R/rf_x 4; python3 $T $R/rd_x 4; python3 $T $R/rf_x 4; uptime
    pkill -f "$R/tools/burn.py"; sleep 20
  done; } > $O/http-setup-timing.txt 2>&1
sleep 30
for i in 1 2 3 4 5; do
  uptime > $O/consecutive-make-test-$i.uptime-before.txt
  FABLE_HTTP_SETUP_LOG=$O/consecutive-make-test-$i.class-setup.jsonl PYTHONPATH=$R/hook $X consecutive-make-test-$i $R/run_mt make test
  uptime > $O/consecutive-make-test-$i.uptime-after.txt
done
{ echo "== idle, after the five runs"; date -u +%Y-%m-%dT%H:%M:%SZ; uptime; python3 $T $R/rd_x 5; python3 $T $R/rf_x 5; } >> $O/http-setup-timing.txt 2>&1
$X make-test-idle-no-hook $R/run_mt2 make test
echo "idle batch finished" >> $O/_progress.txt
