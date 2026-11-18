# Developer command results

These are developer executions, not independent acceptance. The owner resolved the frozen-period question in D-029: preserve frozen approval and block the incoming version until reopen. Independent acceptance remains pending. Each label has raw stdout/stderr and exact argv, environment, UTC start, duration and exit metadata beside this file. Verified labels use the final source in `verified-source-sha256.json`; earlier candidate/current/final labels remain as intermediate evidence and are not substituted for that run.

| Command / evidence label | Exit | Result |
| --- | --- | --- |
| Unmodified baseline RD probes / `baseline-rd-probes` | 1 | 10 OK / E02 NOTE / E03+E06 WEAK |
| Unmodified baseline extended search / `baseline-extended-orders` | 1 | 336 runs / 24 double; 12 in each affected family |
| Combined feed + unchanged HTTP methods / `feed-and-http-after-unclaimed-shortcut` | 0 | 27 tests OK, including all 11 HTTP methods |
| make test / `verified-full-make-test` | 0 | 227 tests OK; all 205 baseline methods retained with the sole authorized rewrite; no skips/expected failures |
| make check / `delivery-make-check` | 0 | 88 records / 27 tickets; states unchanged and conflict disclosed |
| make batch2-gate / `verified-batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK; synthetic month passes |
| make reverification-gate / `verified-reverification-gate` | 0 | Required original/maintained/checkpoint commands pass; supplementary N08/N09 remain disclosed |
| make acceptance-gate / `verified-acceptance-gate` | 0 | Required original/maintained assertions pass; U4 sole permitted gate NOTE |
| make rb-gate / `verified-rb-gate` | 0 | 14 original RA probes OK; strict-gate tests pass |
| make rc-gate / `verified-rc-gate` | 0 | 18 original RB IDs: 16 OK / N02c,N04e NOTE |
| make rd-gate / `verified-rd-gate` | 0 | 16 original RC IDs: 15 OK / X08 NOTE; all 120 orders / 0 double |
| make re-gate / `verified-re-gate` | 0 | 12 original RD probes OK; adapted Y05 OK; all 336 exact orders / 0 double |
| Unmodified F faults / `candidate-rb-register-faults` | 0 | 37/37 agree; exact-final archive repeats this adjacent to the envelope |
| Unmodified G faults on disposable copy / `candidate-rc-register-faults` | 0 | 44/44 agree / zero make-check gaps; exact-final archive repeats this adjacent to the envelope |
| Unmodified H diagnostic / `candidate-rd-register-faults` | 1 | 34/37 agree: H13/H14 reject; H22/H23/H24 expect obsolete RC precedence |
| Historical literal clause-7 diagnostic before D-029 / `verified-locked-home-boundary` | 1 | Exit 1 surfaced the question; D-029 subsequently confirmed frozen approval preservation |
| D-029 owner-clarification check / `owner-clarification-probe` | 0 | PASS: frozen approval preserved; incoming version held; after reopen conflict remains and no approval is created |
| Product-register tests after D-029 / `register-tests-after-owner-clarification` | 0 | 26 tests OK on the clarified register |
| Preservation and exact allowed method boundary / `delivery-preservation-check` | 0 | 719 inputs / 205 baseline methods / 227 current methods; schema/history/owner wording unchanged |
| Patch dry-run + apply + byte comparison / `delivery-source-patch-check` | 0 | 18 changed runtime/test/gate/adapter files reproduced exactly |

The first candidate full suite ran 225 tests and failed N01e. The first current full suite ran 216 methods and had one HTTP setup error, so its eleven HTTP methods did not run in that attempt. The next `final-full-make-test` attempt also hit that setup deadline and was interrupted after the known failure while the corrected full run continued. Their raw logs and nonzero exits remain in the index. The final 227-method result does not waive any of those methods.

The pre-clarification literal diagnostic exits 1 because it modeled suspension of a frozen approval. The owner subsequently chose preservation in D-029; the current owner-clarification probe exits 0. Both sources and raw results are retained. No policy choice remains pending. UC-9 behavioral reproduction is NOT_RUN because journals are explicitly excluded. No other required command is waived. The unmodified H diagnostic exits 1 for the three stated stale-authority expectations.

Exact-final archive verification runs make check, the unchanged F/G fault scripts and the gate fault/adaptation/input tests on a clean extraction. Those outputs are adjacent `_FINAL_VERIFICATION` artifacts, excluded from the payload so validation does not rebuild the ZIP with its own results.
