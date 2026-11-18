#!/bin/bash
# Assemble the review folder in the scratch area (deliver/). Copies only; nothing in the project is touched.
set -e
R=/private/tmp/claude-501/rf; D=$R/deliver; O=$R/out; E=$D/evidence; P="/Users/luis/Documents/ChatGPT/Accounting Agent OS"
rm -rf "$E"; mkdir -p "$E/commands" "$E/scripts" "$E/search" "$E/search-first-pass" "$E/hook"
cp $R/scripts/fable_rf_acceptance_probes.py $R/scripts/fable_rf_step_search.py "$D/"
cp "$O/rf-probes-own.stdout.txt" "$D/fable_rf_acceptance_output.txt"
echo "exit=$(python3 -I -c "import json;print(json.load(open('$O/rf-probes-own.json'))['exit_code'])")" > "$D/fable_rf_acceptance_exit.txt"
for j in "$O"/*.json; do b=$(basename "$j" .json); case "$b" in *.results|_*) continue;; esac
  cp "$j" "$E/commands/"; cp "$O/$b.stdout.txt" "$O/$b.stderr.txt" "$E/commands/" 2>/dev/null || true
  for x in class-setup.jsonl uptime-before.txt uptime-after.txt; do [ -f "$O/$b.$x" ] && cp "$O/$b.$x" "$E/commands/"; done; done
python3 -I - <<'PY'
import json,glob
D='/private/tmp/claude-501/rf/deliver/evidence/commands/'
rows=[]
for f in sorted(glob.glob(D+'*.json')):
    d=json.load(open(f)); rows.append('%-48s exit=%d  elapsed=%ds  %s'%(d['label'],d['exit_code'],d['elapsed_seconds'],d['argv']))
open(D+'exit-codes.txt','w').write('\n'.join(rows)+'\n')
# compact copies of the search results (same content, no indentation)
import os
S='/private/tmp/claude-501/rf/out/'
for src,dst in [(S+'search/','search/'),(S,'')]:
    for f in sorted(glob.glob(src+'*.results.json')):
        open('/private/tmp/claude-501/rf/deliver/evidence/'+dst+os.path.basename(f),'w').write(json.dumps(json.load(open(f)),separators=(',',':')))
PY
cp "$O"/search/*.stdout.txt "$O"/search/*.json "$E/search/" 2>/dev/null || true
python3 -I - <<'PY'
import json,glob,os
E='/private/tmp/claude-501/rf/deliver/evidence/search/'
for f in glob.glob('/private/tmp/claude-501/rf/out/search/*.results.json'):
    open(E+os.path.basename(f),'w').write(json.dumps(json.load(open(f)),separators=(',',':')))
PY
cp "$O"/search_first_pass/*.stdout.txt "$E/search-first-pass/" 2>/dev/null || true
for f in re-step-search-older-claim+newer-claim re-step-search-older-resent-with-claim re-step-search-two-claims+revision re-step-search-late-row-target; do cp "$O/$f.stdout.txt" "$E/"; done
cp "$O/rf-register-faults-K.stdout.txt" "$E/fable-rf-register-faults.txt"; cp "$O/rf-gate-faults-M.stdout.txt" "$E/fable-rf-gate-faults.txt"; cp "$O/re-gate-faults-K-unchanged.stdout.txt" "$E/fable-re-gate-faults-unchanged-script.txt"
cp "$O/http-setup-timing.txt" "$O/cross-version-fingerprint.txt" "$O/search-analysis.txt" "$O/uc20-from-trails.txt" "$O/uc20-from-trails-baseline-re.txt" "$E/"
cp "$O/baseline-re-source-rf-probes.stdout.txt" "$E/baseline-re-source-rf-probes.txt"
grep -h "RF-03 EQUIVALENCE" "$O"/eq-*.stdout.txt | awk '{print}' > /dev/null
( for f in "$O"/eq-*.stdout.txt; do echo "$(basename $f .stdout.txt): $(grep 'RF-03 EQUIVALENCE' $f)"; done; echo; echo "--- demo data, single-threaded (eq-demo)"; grep -v "RF-03" "$O/eq-demo.stdout.txt" ) > "$E/equivalence.txt"
cp $R/ev/integrity.txt $R/ev/change-inventory-check.txt $R/ev/preservation.txt $R/ev/protected-inputs-check.txt $R/ev/diff-vs-re-archive.json $R/ev/tree-compare.txt "$E/"
cp $R/scripts/*.py $R/scripts/report_template.md $R/scripts/timing_reading.md $R/scripts/assemble.sh $R/tools/*.sh $R/tools/burn.py $R/tools/jobs*.txt $R/tools/eq_jobs.txt "$E/scripts/"
cp $R/hook/sitecustomize.py "$E/hook/"
cp $R/scripts/evidence_README.txt "$E/README.txt"
( echo "macOS $(sw_vers -productVersion) $(uname -m)"; python3 --version; echo "SQLite $(sqlite3 --version | cut -d' ' -f1)"; make --version | head -1; echo "CPUs $(sysctl -n hw.ncpu)"; sysctl -n machdep.cpu.brand_string ) > "$E/versions.txt" 2>&1
echo assembled; du -sh "$D"; find "$D" -type f | wc -l
