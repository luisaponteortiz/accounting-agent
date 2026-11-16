#!/bin/bash
# Assemble the review folder in the scratch area (deliver/). Copies only; nothing in the project is touched.
set -e
D=/tmp/fre/deliver; O=/tmp/fre/out; E=$D/evidence
rm -rf "$E"; mkdir -p "$E/commands" "$E/scripts" "$E/experiment" "$E/first-pass-step-search"
cp /tmp/fre/probes/fable_re_acceptance_probes.py /tmp/fre/probes/fable_re_step_search.py "$D/"
for j in "$O"/*.json; do b=$(basename "$j" .json); case "$b" in *.results|diff-vs-rd-archive) continue;; esac
  cp "$j" "$E/commands/"; cp "$O/$b.stdout.txt" "$O/$b.stderr.txt" "$E/commands/" 2>/dev/null || true; done
python3 -I - <<'PY'
import json,glob,os
rows=[]
for f in sorted(glob.glob('/tmp/fre/deliver/evidence/commands/*.json')):
    d=json.load(open(f)); rows.append('%-48s exit=%d  elapsed=%ds  %s'%(d['label'],d['exit_code'],d['elapsed_seconds'],d['argv']))
open('/tmp/fre/deliver/evidence/commands/exit-codes.txt','w').write('\n'.join(rows)+'\n')
PY
cp "$O"/step-search-*.results.json "$O"/rd-order-search-336.results.json "$O"/rc-order-search-120.results.json "$E/" 2>/dev/null || true
for f in step-search-older-claim+newer-claim step-search-older-resent-with-claim step-search-two-claims+revision step-search-late-row-target; do cp "$O/$f.stdout.txt" "$E/"; done
cp "$O"/experiment-step-search-*.results.json "$E/experiment/" 2>/dev/null || true
for f in "$O"/experiment-step-search-*.stdout.txt "$O"/experiment-rd-order-search-336.stdout.txt; do cp "$f" "$E/experiment/"; done
cp "$O"/experiment/* "$E/experiment/"
cp "$O"/http-isolated-*.txt "$O"/feed-plus-http-*.txt "$E/"; cp "$O"/experimental-correction-rf01.patch "$O"/fable-re-register-faults.txt "$O"/fable-re-gate-faults.txt "$O"/register-diff.txt "$O"/preservation.txt "$O"/archive-integrity-check.txt "$O"/patch-and-inputs-check.txt "$O"/change-inventory-check.txt "$O"/diff-vs-rd-archive.json "$O"/baseline-rd-source-re-probes.txt "$O"/uc20-replacement-of-waiting-claimant.txt "$O"/http-setup-timing.txt "$E/"
cp "$O"/first-pass-step-search/step-search-older-resent-with-claim.stdout.txt "$E/first-pass-step-search/" 2>/dev/null || true
cp /tmp/fre/probes/fable_re_register_faults.py /tmp/fre/probes/fable_re_gate_faults.py /tmp/fre/probes/uc20_explore.py /tmp/fre/tools/verify_manifest.py /tmp/fre/tools/compare_trees.py /tmp/fre/tools/preservation.py /tmp/fre/tools/run_cmd.sh /tmp/fre/tools/seq_probes.sh /tmp/fre/tools/seq_make.sh /tmp/fre/tools/seq_faults.sh /tmp/fre/tools/quiet_tail.sh /tmp/fre/tools/http_setup_timing.py /tmp/fre/tools/build_results.py /tmp/fre/tools/assemble.sh "$E/scripts/"
( echo "macOS $(sw_vers -productVersion) $(uname -m)"; python3 --version; echo "SQLite $(sqlite3 --version | cut -d' ' -f1)"; make --version | head -1; echo "CPUs $(sysctl -n hw.ncpu)" ) > "$E/versions.txt" 2>&1
( echo "bundle  sha256 $(shasum -a 256 '/Users/luis/Documents/ChatGPT/Accounting Agent OS/exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip' | cut -d' ' -f1)"; echo "sidecar        $(cut -d' ' -f1 '/Users/luis/Documents/ChatGPT/Accounting Agent OS/exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip.sha256')"; echo "internal REVIEW_MANIFEST.json sha256 $(shasum -a 256 /tmp/fre/extract/REVIEW_MANIFEST.json | cut -d' ' -f1)"; echo "external manifest             sha256 $(shasum -a 256 '/Users/luis/Documents/ChatGPT/Accounting Agent OS/exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.REVIEW_MANIFEST.json' | cut -d' ' -f1)"; echo "package check manifest_sha256        $(python3 -I -c "import json;print(json.load(open('/Users/luis/Documents/ChatGPT/Accounting Agent OS/exports/FABLE_RE_AND_PRV_CORRECTIONS_PACKAGE_CHECK.json'))['manifest_sha256'])")"; python3 -I /tmp/fre/tools/verify_manifest.py /tmp/fre/extract | tail -1 ) > "$E/integrity.txt" 2>&1
cat > "$E/README.txt" <<'TXT'
Evidence for Fable's independent verification of the RE/PRV bundle 4890b297...98ae (16 November 2026).

commands/                 one .json (argv, cwd, UTC start, seconds, exit), .stdout.txt and .stderr.txt per command; exit-codes.txt lists them.
                          make-test is the first full run, made while eleven other jobs were running; make-test-rerun-alone is the run on a quiet machine.
integrity.txt             bundle, sidecar, internal and external manifest hashes; payload hash check.
versions.txt              environment.
*-check.txt, preservation.txt, register-diff.txt, diff-vs-rd-archive.json
                          comparisons with the RD archive 0d188fa6...7ea9 and with the working project (read-only).
baseline-rd-source-re-probes.txt
                          my probes run against the RD checkpoint source (they must fail there).
fable-re-register-faults.txt, fable-re-gate-faults.txt
                          my fault injection for PRV-14/15 and for the RE gate; scripts under scripts/.
step-search-*.stdout.txt, *.results.json
                          my order search on the delivered source, one file per family.
first-pass-step-search/   the first run of the family that fails, made with a stricter criterion that also counted an approval
                          of the replacement row while the claimed target had not arrived yet. Kept for completeness; superseded.
experimental-correction-rf01.patch, experiment/
                          the one-line worked reference for RF-01 and everything run on a disposable copy with it. Not a delivered correction.
uc20-replacement-of-waiting-claimant.txt
                          observation UC-20 on this checkpoint and on the RD checkpoint.
http-setup-timing.txt     seconds the unchanged HTTP test setup needs on the RD and RE source, before and after the quiet make test.
scripts/                  every script used. Paths inside them point at the reviewer's disposable scratch copies.
TXT
echo assembled; du -sh "$D"; find "$D" -type f | wc -l
