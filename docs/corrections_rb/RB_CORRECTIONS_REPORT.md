# RB/accounting-register correction response

16 November 2026. Local fictional preparation only. Independent RA/G0 acceptance failed at the returned checkpoint; the user authorized this correction pass, not Batch 3. No real systems, paid services/models, posting, payments, sending or deployment were activated. All submitted bundles/sidecars and independent inputs remain unchanged.

## Reproduction before source changes

The response ZIP matched its supplied SHA-256 d38e0e27b30e46d2e4690b5366aa3fa237d5733e23783c64082c39ca4ff30f84, all 39 extracted files matched its bytes, and the frozen combined ZIP matched b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea. Before correction all 344 frozen working hashes matched. Original source was not modified until after running the independent probes.

The unchanged latest script reproduced **8 OK / 5 WEAK / 1 NOTE**, exit 1: R01b/R01c, R03b/R04b and R02b failed; R04c was NOTE. Additional RB-01 unit regressions failed before the fix, including already approved destination work. PR-15's shared notice named the first client for a separately configured second fictional client. Raw baseline output, exit and notice are preserved here.

## Corrections in prescribed order

| Ticket | Correction | New verification |
| --- | --- | --- |
| RB-01 | Check live locked/quarantined ancestors before own admission, then retain nearest-owner fallback for released chains. Quarantine late/later-resolved links and support, stop destination governing approval and emit an approved-source event. Prevent new same-period move rows. | R01a–d; unit cases for destination eligible/approved, quarantine/history/events, reopen terminal and unresolved arrival order. |
| RB-02 | Historical matching support is replaced when its current key is removed **or re-pointed away**. A still-active same-item extra document stays a multiple-document question. | R03a/b, R04a/b; receipt/statement supplier refusal, independent item acceptance, separate final review and later-change invalidation. |
| RB-03 | Find prior approved semantic coverage across general/item scope and new rule keys. Preserve explicit link evidence; unrelated aliases/categories/scopes/policy values do not contribute. | R02a/b; additional vendor and receipt-policy scope/key variants with independent-review positives. |
| RB-04 | Disclose lookback statement revisions and own-period acceptances. Continuity is unverified until every relying item has active revision acceptance. Include acceptance evidence/actors in dependent manifest and lineage; revocation re-blocks and invalidates affected approval. | R04c; unit partial/all acceptance, supplier/acceptor independence, final review and revocation; locked prior lookback remains in retained A13 tests. |
| PR-15 | Shared state notice is client-neutral; a second client's whole state is checked and shared Python client-name literals are rejected by make check. | New second-client regression and static check. |

No historical artifact, accounting decision, source snapshot, package or audit record is rewritten. No schema migration or technology-stack rewrite was needed. The new 14-probe script is exercised unmodified by normal tests and make rb-gate; every result must be OK, including R04c.

## Requirements and enforcement

See PR_DISPOSITION.md for every PR-01–PR-17 response and unresolved owner/client choices. The register retains 76 original IDs and adds 12 explicit records: ONB-01/02, INT-07, GL-06, BNK-07, RPT-03, BB-08 and EXC-01–05. No proposed feature is implemented. Independent failures remain recorded, rather than being promoted by developer tests. The checker has fault regressions for duplicate/lost IDs, missing fields, invalid/mixed states/evidence, unknown/cyclic dependencies, missing backlog mappings and first-client conditions in shared records. All 27 original tickets remain mapped and Batch 3 order/closure is unchanged.

## Validation and limits

Final command results, exact counts and raw evidence are recorded in execution-results.json and final-*.txt. The complete loopback-enabled suite passed **174 tests**, including all 154 prior methods in 16 byte-identical original files and 20 new methods, with no skips or expected failures. The earlier sandbox-only run's HTTP bind PermissionError and separate reproduction are preserved; no source change was needed to resolve it. All five retained/new gate targets exit 0. The latest unchanged independent probes report **14 OK**, exit 0, and the 60 cases remain **29 PASS / 10 FIXED / 21 DEFERRED-OK**. Both older literal full commands remain nonzero at the same disclosed incompatible setups; compatible originals and reviewed setups pass their maintained gates. These are developer executions, not independent re-acceptance.

Residual matters: U4 non-restoration remains the accepted visible limitation; UC-5 grant lifecycle is required before actual G1; UC-6 duplicate payment vocabulary is still an unexecuted observation; UC-7 receipt move had_approval metadata can still be zero though the root charge had approval (historical rows are retained); UC-8/UC-9 keep the independent review's execution limits. A revised zero-activity prior statement with no item acceptance path stays unverified/manual rather than receiving invented authority. Per-item invalidation, aggregate receipts, non-calendar cycles, full reconciliation, AP/AR/reporting, identity/secrets, atomic exports/audit anchoring and production reliability remain deferred. Actual client policies, facts, hosting/support terms, parameter values and proposed product scope need their designated owners. No human G0 or later gate is opened by this response.
