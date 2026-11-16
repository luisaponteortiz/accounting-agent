# Fable independent verification of RB-01 to RB-04

16 November 2026. Reviewed: `FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_BUNDLE.zip`, SHA-256 `00a13d93…be001d` (matches the supplied value).

All data is fictional. Every database was temporary. No file of the bundle was changed, and nothing was connected, posted, paid, sent or deployed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RB-01** | **Not accepted.** Both reproductions in the ticket are closed. Three further arrival orders still leave one charge approved in two periods (RC-01, RC-02, RC-03, all P1). |
| **RB-02** | **Accepted.** |
| **RB-03** | **Accepted.** |
| **RB-04** | **Accepted.** |
| **G0 technical criteria** | **Not met.** Three P1 defects are open, all in the locked-period control. |
| Retained C, RV, RA and Batch 2 controls | Retained. Every delivered gate passes in my run. The C-01 and RV-01 objective is still breached by RC-01 to RC-03. |
| Preservation | Confirmed. Both frozen archives, all 39 returned review files and the 14-probe script are byte-identical to their originals. |
| Seven earlier adaptations, strengthened RT14b, five statement setups | Retained unchanged. Nothing under `review/` differs from the frozen submission. |

The requirements-register verdict is in `../FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_REPORT.md`.

## Confirmed blockers

All three end the same way: A1 stays approved in locked November, its replacement is approved in open December, and (in RC-01 and RC-03) December finalizes without acknowledgement. Each needs only a particular delivery order, not intent.

### RC-01 (P1): the locked charge was withdrawn after the lock

Probe N01b.

1. Approve A1 (3 Nov, 40.00). Lock November.
2. Intake B1 (2 Dec, 40.00) with no supersession claim. It is admitted to December.
3. The feed withdraws A1 (`tombstone`, `voided`). November is locked, so the withdrawal is quarantined.
4. Re-send B1 with `supersedes = demo_card_001:A1`. Disposition the transition, approve B1, finalize December.

Result: B1 approved in December, A1 approved in November, no source exception, no move row. If the claim arrives with B1 (step 2 and 4 merged), B1 is quarantined correctly.

Cause: `source_control.py` `source_origin` lines 124–127 examine only ancestors whose head is not removed. A head removed by a withdrawal that was itself quarantined is skipped, and lines 128–130 fall back to B1's own December admission.

This is not a regression; the frozen submission behaves the same way. The condition "head is not removed" is the one I wrote in the RB-01 correction text. The delivered code implements it as specified. The gap is in my correction as much as in the code.

### RC-02 (P1): the link is declared on a middle source

Probe N01c.

1. A1 approved, November locked.
2. Intake B1 (2 Dec) with no claim. Intake C1 (3 Dec) superseding B1. C1 replaces B1 inside December.
3. Re-send B1 with `supersedes = demo_card_001:A1`.

Result: B1 is quarantined, correctly. C1, which replaces B1, stays governing in December and is approved. Where C1 had already been approved, an independent reviewer approves the new version directly.

Cause: after an intake, `bind_source` is called for the source taken in and for every receipt (`service.py` lines 380–382), but not for other live sources whose chain has just changed.

In outcome this is a regression against the frozen combined submission, which holds both December sources. It held them by a side effect (the re-sent B1 was revived beside C1 and both collided), not by design.

### RC-03 (P1): an unresolved claim is never linked

Probe N01d.

1. A1 approved, November locked.
2. Intake A1Y (3 Dec) superseding A1X, which has not arrived. A1Y is admitted to December and held as unresolved.
3. Intake A1X (2 Dec) superseding A1. It is quarantined.
4. Intake A1Z (4 Dec) superseding A1Y. A1Y is not re-sent.

Result: A1Z is admitted with a disclosed chain of A1Y only, is approved, and December finalizes without acknowledgement.

Cause: an unresolved claim records only an event (`source_control.py` lines 47–48). No link is written when the target later arrives, so the chain of any later replacement stops at the claimant. The control works only if the provider happens to re-send A1Y (probe R01c).

Not a regression; the frozen submission behaves the same way.

### Correction, tried in a temporary copy

I applied the three corrections together to a throwaway copy of the source: six edits in `source_control.py` and `service.py`, 24 lines added and 3 replaced. This is not a delivered fix, and the bundle is unchanged. The patch is `evidence/experimental-correction.patch`.

1. In `source_origin`, also treat an ancestor as held when its head was removed by a withdrawal that is quarantined under a period still locked. On reopen, admit such a withdrawal.
2. After every intake that changed anything, re-bind every live transaction that has a supersession chain, shortest chain first.
3. Before that step, link each recorded unresolved claim whose target has now arrived.

In the copy:

| Check | Result in the temporary copy |
| --- | --- |
| My 18 new probes | 16 OK, 2 NOTE, 0 WEAK |
| `make rb-gate` (14 unmodified probes) | exit 0, 14 OK |
| `make acceptance-gate`, `make reverification-gate`, `make batch2-gate` | exit 0 each |
| `make test` | exit 0, 174 methods OK |

No new unit tests were written for the copy. The exact tickets, with acceptance assertions, are in `FABLE_RB_CORRECTIONS.json`.

## Judgment per ticket

| Ticket | Verdict | My evidence |
| --- | --- | --- |
| RB-01 | **Not accepted** | R01a–R01d pass unmodified. N01a passes: a destination approved before the claim stops governing, with an approved-source event, `ITEM_LEFT_POPULATION`, a blocked move carrying `had_approval`, no same-period move row, root history kept, finalization refused, reopen admitting only the replacement, relock, replay and restart stable. N01e passes: a three-link chain delivered newest first. N01f and N01g pass (open-period controls). **N01b, N01c and N01d fail.** |
| RB-02 | Accepted | R03a, R03b, R04a, R04b pass unmodified. N02a passes for a receipt re-pointed to a void id or to another existing charge, in one packet or two, in either order, by a second supplier. N02b passes for a statement re-pointed before or after its replacement. In every variant: held and disclosed with both identities, versions, suppliers and changed fields; both suppliers refused with 403; acceptance by a granted non-supplier is item-bound; the acceptor is refused at final review; a later change lapses the acceptance. A genuine additional receipt stays a multiple-receipt question. |
| RB-03 | Accepted | R02a, R02b pass unmodified. N03a passes for vendor mappings and receipt policies, by item scope and by new key, and for a three-step chain: every earlier author and approver is refused, and an independent reviewer approves. N03b passes: another item scope, description, category, policy value or client does not bar a reviewer. N03c: an equal money value cannot be written differently. |
| RB-04 | Accepted | R04c passes unmodified. N04a passes: December discloses the revision and stays unverified with no and with partial acceptance; it verifies only when every November item is accepted; the acceptor and the supplier of the restated statement are refused at December review; revocation re-blocks December, and finalization is refused even before December is re-prepared. N04b: a further change lapses the acceptance. N04c: a re-pointed or withdrawn-and-replaced November statement is disclosed; a withdrawn one is reported missing. N04d: a late restatement of a locked November is quarantined and the frozen balance is kept; an unaccepted restatement is not authenticated by locking. |

## Observations that need a decision, not a fix

- **UC-10 (N02c).** A contradicting receipt supplied *after* the one relied on, then moved away or withdrawn, leaves no disclosure. This is outside RB-02, which concerns documents supplied before the one relied on. Whether withdrawing contradicting evidence must be shown to the reviewer is a document-policy decision.
- **UC-11 (N04e).** A restated prior statement whose period has no card activity has no item to accept it against, so the next period stays unverified. Safe direction; the developer disclosed it.
- **UC-12.** A withdrawal of an approved charge that arrives under a lock is not listed in `state.source_exceptions`; it appears only as an event. Included in the RC-01 correction.
- **UC-7.** Same-period move rows are gone. Receipt rows in a blocked chain still carry `had_approval` 0.

## Commands I ran

Python 3.9.6, SQLite 3.51.0, GNU Make 3.81, macOS 26.5.2 (Darwin 25.5.0, x86_64). Run from byte copies of the extracted bundle. Raw stdout, stderr and exit codes are in `evidence/`.

| Command | Exit | Result in my run |
| --- | --- | --- |
| `make test` | 0 | 174 methods OK in 456 s. No skip or expected-failure marker. Loopback was available. |
| `make check` | 0 | Syntax, JSON, profile, registry, DOM, register and client-name checks. |
| `make batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK, none unexpected. |
| `make reverification-gate` | 0 | 27 unmodified originals OK; 35 reviewed setups OK; corrective checkpoint PASS. |
| `make acceptance-gate` | 0 | 20 unmodified originals: 19 OK and U4 NOTE. 24 reviewed setups: 23 OK and U4 NOTE. |
| `make rb-gate` | 0 | 14 OK; 3 gate tests OK. |
| `python3 scripts/check_product_requirements.py --json` | 0 | 88 records, 27 tickets. |
| `python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .` | 0 | 14 OK, including R04c. No NOTE, WEAK or ERROR. |
| `python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .` | **1** | 19 OK; A03, A05, X09 WEAK; A17 ERROR; U4 NOTE. As disclosed. Not a pass. |
| `python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .` | **1** | 28 OK; 4 WEAK; 3 ERROR. As disclosed. Not a pass. |
| `python3 fable_rb_acceptance_probes.py <root>` | **1** | 13 OK, 2 NOTE, 3 WEAK (N01b, N01c, N01d). |

The 174 count is reproduced: all 154 methods of the frozen RA source are present, the 16 original files under `tests/` are byte-identical (15 test modules and `__init__.py`), and 20 methods are new (11 register, 6 RB corrections, 3 gate). The normal test run and `make rb-gate` both require exit 0, the exact 14 probe ids and OK for each.

The 60 older cases are listed one by one in `FABLE_RB_ACCEPTANCE_RESULTS.json`. The 21 deferred refusals are not implemented accounting functionality.

Integrity: the manifest matches (448 files), no unsafe archive paths, both frozen archives match their stated hashes, and the 10 source, test and script files that differ from the frozen combined submission are exactly those named in `changed-files.json`. One small gap: 19 added files, all archives or packaging, are outside the inventory (PRV-09).

## Teaching month and isolation

Re-driven through the unmodified probes M1 and M2 and `scripts/synthetic_month.py`.

- Referral route: supplies +311.00, repairs +200.00, card liability −211.00, cash −300.00; nets to zero.
- Acceptance route: supplies +391.00, repairs +200.00, card liability −291.00, cash −300.00; nets to zero.
- Second client: isolation PASS, audit chains verify. Package immutability and stale-package refusal pass (A17, RT18).

These are preparation demonstrations. They are not posting, reconciliation completion or a close.

## What was not run

- UC-6 (duplicated payment row vocabulary), UC-8 (RA-05 across a period boundary), UC-9 (RA-07 for journals): delivered tests or reading only.
- The restricted-sandbox run without loopback: I read the preserved failure and did not reproduce it.
- No external linter or type checker exists in the project.

## Files returned

1. `FABLE_RB_ACCEPTANCE_REPORT.md` (this file)
2. `FABLE_RB_ACCEPTANCE_RESULTS.json`: every command, probe, case and assertion
3. `FABLE_RB_CORRECTIONS.json`: RC-01 to RC-03, open concerns, decisions for client authority
4. `fable_rb_acceptance_probes.py`: 18 service-only probes; exit 1 on a verified failure. Helpers are loaded unchanged from the earlier independent script in the project.
5. `fable_rb_acceptance_output.txt` and `evidence/`: raw logs, the scripts I used, the frozen-baseline comparison, register checks and the experimental patch with its results
6. `../FABLE_PR_REVERIFICATION/`: the PR report and corrections
