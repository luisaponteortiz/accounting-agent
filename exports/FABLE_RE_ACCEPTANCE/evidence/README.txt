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
