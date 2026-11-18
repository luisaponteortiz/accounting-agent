Evidence for Fable's independent verification of RF-01 to RF-03 and PRV-16 (bundle SHA-256 c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd).

commands/                 stdout, stderr and a small json (argv, start, seconds, exit code) for every command; exit-codes.txt lists them.
                          consecutive-make-test-N also has the class setup log of the observation hook and the uptime before and after.
search/                   extended order search, one process per family or shard: stdout, compact results with the trail of every order.
                          rf-*          delivered source (2,640 orders)
                          baseline-re-* the same script on the RE checkpoint source (six families, 720 orders)
search-first-pass/        superseded first pass of six families (stricter repeat criterion that counted UC-21 as a failure).
re-step-search-*          the unmodified 480-order search of the last review on the delivered source, one family per process.
uc20-from-trails*.txt     UC-20 counted from the kept trails (delivered source; RE checkpoint source).
search-analysis.txt       ad hoc cross-checks over the trails. Reading notes:
                          - "left the hold listing" in the withdrawal family is the held row being withdrawn by the feed; it is
                            never admitted to a period and is held again when it is re-sent.
                          - the 36 steps "approved although Q>P is declared and P is on file" are all in the family
                            retained-claim-on-replacement, at steps where Z has not yet declared any claim: Z is then an
                            unrelated December row. Once Z's claim on Q is delivered, Z is held and its approval stops (0 doubles).
equivalence.txt           RF-03: delivered computation compared with the full computation at every call.
http-setup-timing.txt     RF-03: seconds until the HTTP background worker finished, RD and RF back to back. The first block is
                          headed "idle" but the machine was still settling (load average 16); the last block is the quiet one.
fable-rf-register-faults.txt   62 fault cases on the register checker (fourth authority).
fable-rf-gate-faults.txt       56 fault cases on the RF gate validators, fed real outputs.
fable-re-gate-faults-unchanged-script.txt   the last review's 33 gate fault cases, unchanged, with this checkpoint's outputs.
baseline-re-source-rf-probes.txt   my 15 new probes on the RE checkpoint source (9 WEAK: they discriminate).
cross-version-fingerprint.txt      observation UC-24.
integrity.txt, tree-compare.txt, diff-vs-re-archive.json, change-inventory-check.txt, preservation.txt, protected-inputs-check.txt
                          archive, manifest, tree, inventory, test-method, register and protected-input comparisons.
scripts/                  every script used, as run. Paths beginning /private/tmp/claude-501/rf are the disposable work area:
                          rf_x, re_x, rd_x = extracted RF, RE and RD bundles; base_re = RF tree with the RE accounting_agent/;
                          run1..run8, run_mt, run_mt2 = clean copies of rf_x used for the runs.
hook/sitecustomize.py     observation-only timing of unittest class setup (active only when FABLE_HTTP_SETUP_LOG is set).
versions.txt              machine and tool versions.
