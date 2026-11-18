# Raw command index for the RF result registration

17 November 2026. Every command ran unmodified on disposable clones of the registered project, one after another, with no other job of this pass running. `validate.py` is the orchestrator; `results.json` holds exit codes, start times and load averages. macOS, Python 3.9.6.

| Label | Command | Exit | Seconds | Result | Output |
| --- | --- | --- | --- | --- | --- |
| make-test | `make test` | 0 | 1017.714 | 250 of 250 methods OK; 11 HTTP methods OK; no skips or expected failures | [stdout](make-test.stdout.txt) / [stderr](make-test.stderr.txt) |
| make-check | `make check` | 0 | 1.600 | all four PASS lines; 88 records, 27 tickets | [stdout](make-check.stdout.txt) / [stderr](make-check.stderr.txt) |
| make-batch2-gate | `make batch2-gate` | 0 | 54.934 | synthetic month passes; corrective gate C-01 to C-06 PASS | [stdout](make-batch2-gate.stdout.txt) / [stderr](make-batch2-gate.stderr.txt) |
| make-reverification-gate | `make reverification-gate` | 0 | 47.128 | passes | [stdout](make-reverification-gate.stdout.txt) / [stderr](make-reverification-gate.stderr.txt) |
| make-acceptance-gate | `make acceptance-gate` | 0 | 46.688 | {'NOTE': 1, 'OK': 19} and {'NOTE': 1, 'OK': 23}; U4 the only NOTE | [stdout](make-acceptance-gate.stdout.txt) / [stderr](make-acceptance-gate.stderr.txt) |
| make-rb-gate | `make rb-gate` | 0 | 28.570 | {'OK': 14}; 3 gate tests OK | [stdout](make-rb-gate.stdout.txt) / [stderr](make-rb-gate.stderr.txt) |
| make-rc-gate | `make rc-gate` | 0 | 24.738 | 16 OK, N02c and N04e NOTE | [stdout](make-rc-gate.stdout.txt) / [stderr](make-rc-gate.stderr.txt) |
| make-rd-gate | `make rd-gate` | 0 | 121.050 | 15 OK, X08 NOTE; 120 orders, 0 double | [stdout](make-rd-gate.stdout.txt) / [stderr](make-rd-gate.stderr.txt) |
| make-re-gate | `make re-gate` | 0 | 303.636 | 336 orders, 0 double, 0 finalized silently | [stdout](make-re-gate.stdout.txt) / [stderr](make-re-gate.stderr.txt) |
| make-rf-gate | `make rf-gate` | 0 | 2877.781 | 21 probes: 19 OK, C9c and C9g NOTE; 480 orders, 0 double, 0 released, 0 audit failures | [stdout](make-rf-gate.stdout.txt) / [stderr](make-rf-gate.stderr.txt) |
| register-faults-F-rb | `python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .` | 0 | 94.073 | 36 of 37 agree; F26 obsolete (exit code stays 0) | [stdout](register-faults-F-rb.stdout.txt) / [stderr](register-faults-F-rb.stderr.txt) |
| register-faults-G-rc | `python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py .` | 1 | 46.482 | 43 of 44 agree; G09 obsolete; make check gaps 0 | [stdout](register-faults-G-rc.stdout.txt) / [stderr](register-faults-G-rc.stderr.txt) |
| register-faults-H-rd | `python3 exports/FABLE_RD_ACCEPTANCE/evidence/scripts/fable_rd_register_faults.py .` | 1 | 23.643 | 35 of 37 agree; H22, H23 obsolete | [stdout](register-faults-H-rd.stdout.txt) / [stderr](register-faults-H-rd.stderr.txt) |
| register-faults-J-re | `python3 exports/FABLE_RE_ACCEPTANCE/evidence/scripts/fable_re_register_faults.py .` | 1 | 25.711 | 20 of 35 agree; 15 obsolete | [stdout](register-faults-J-re.stdout.txt) / [stderr](register-faults-J-re.stderr.txt) |
| register-faults-K-rf | `python3 exports/FABLE_RF_ACCEPTANCE/evidence/scripts/fable_rf_register_faults.py .` | 1 | 44.487 | 41 of 62 agree; 21 obsolete | [stdout](register-faults-K-rf.stdout.txt) / [stderr](register-faults-K-rf.stderr.txt) |
| conflict-unadapted-retained-register-tests | `python3 -m unittest tests.test_product_requirements tests.test_product_requirements_rf -v` | 1 | 61.398 | expected failure: the six unadapted retained methods fail (8 failures in 31 tests) | [stdout](conflict-unadapted-retained-register-tests.stdout.txt) / [stderr](conflict-unadapted-retained-register-tests.stderr.txt) |

The four fault scripts that exit 1 and the conflict reproduction that exits 1 are expected and explained in [the registration report](../RF_REGISTRATION_REPORT.md). The 94 tested source, test, script, review, Makefile, register, results and decision-log files had the same hashes before and after the run (`tested-source-sha256.json`, `source-unchanged-after-run.json`).
