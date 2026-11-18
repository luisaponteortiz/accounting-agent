# Accounting Agent OS RF review handoff

Prepared 17 November 2026 for continuation in the same project or a new chat.

Fable has returned the independent RF review. **RF-01, RF-02, RF-03, PRV-16 and RE-01/RB-01 are accepted at the delivered RF checkpoint. There are no corrective tickets.** This acceptance covers the synthetic local preparation controls exercised by the review. Human G0 is still the accounting owner's decision; no later operating gate is open.

The working register has not yet incorporated this returned review. AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 still read **Verification failed**, and the checker still derives results from four authorities ending with the RE review. Fable now permits these three records to be recorded **Independently verified for the reviewed checkpoint and scope**. Reconciliation is a separate owner-assigned change; this handoff does not authorize it.

## Project and preserved checkpoint

- Workspace: `/Users/luis/Documents/ChatGPT/Accounting Agent OS`.
- Branch: `review/fable-rc-acceptance`.
- HEAD: `5af9a6194bc39e2f303cc6b43b0b59094118b8e4`; **10 commits**, unchanged. Do not commit, reset, clean, rewrite history or discard the existing modified/untracked project files.
- Scope: a universal accounting platform spanning GL, AP, AR, banking/reconciliation, close and reporting. Bird Bowl is the first isolated client implementation. The executable build remains local and fictional; reusable architecture does not establish full accounting or production readiness.

Delivered RF bundle:

`exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`

```text
SHA-256 c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd
Manifest 07bac9cac34acd069c5e509d8fe832a397f768e8e640a9324903f3fe3ee715f0
```

Returned independent response:

`exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip`

```text
SHA-256 343da96a13daecdbc5f8bd7c8d9c9ac265c7b1a9ebca97c478ac1be1a2583232
```

Both ZIP hashes were rechecked while preparing this handoff. All 298 files in the response ZIP match their working review-folder copies. The delivered archive, response, sidecars, manifests, review evidence and earlier archives are immutable. Do not rebuild the delivered label or rewrite the older handoffs to make them appear current. This note is outside that delivery.

## Read these sources first

1. Current [AGENTS.md](AGENTS.md), then the [latest independent RF report](exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md).
2. [RF machine-readable results](exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_RESULTS.json) and [tickets and owner observations](exports/FABLE_RF_ACCEPTANCE/FABLE_RF_CORRECTIONS.json). The tickets array is empty.
3. [Product register](docs/PRODUCT_REQUIREMENTS.md), [decision log](DECISIONS.md), [progress](PROGRESS.md) and [connection readiness](docs/CONNECTION_READINESS.md). Their RF-pending wording predates the returned RF review; the registration step has not been assigned.
4. [Developer RF report](docs/corrections_rf/RF_CORRECTIONS_REPORT.md), [raw command index](docs/corrections_rf/COMMAND_RESULTS.md), [completion record](docs/corrections_rf/completion.json), [change inventory](docs/corrections_rf/changed-files.json) and [source and tests patch](docs/corrections_rf/source-and-tests.patch).
5. [Package check](exports/FABLE_RF_AND_PRV_CORRECTIONS_PACKAGE_CHECK.json), [final archive verification](exports/FABLE_RF_AND_PRV_CORRECTIONS_FINAL_VERIFICATION.json), [checksum sidecar](exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip.sha256) and [external manifest](exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.REVIEW_MANIFEST.json).

[FABLE_RF_REVIEW_PROMPT.md](FABLE_RF_REVIEW_PROMPT.md) and [FABLE_RF_CORRECTIONS_HANDOFF.md](FABLE_RF_CORRECTIONS_HANDOFF.md) are the already-delivered review instructions and developer handoff. That independent review has now been completed.

## What was implemented and accepted

| Item | Delivered behavior |
| --- | --- |
| RF-01 | A first claim added to an already retained older/conflicting message is applied through the existing first-claim path. Known targets link immediately; unknown targets wait and link on arrival. Governing row data remains unchanged; locked chains and receipts are held. |
| RF-02 | Every recorded target selector remains a contributor through confirmations, replacements, revisions and historical ancestry. Ordinary dispositions retain their prior rules. |
| RF-03 | Repeated currentness checks are reused only within one transaction and one report calculation. Autocommit observations still recompute. The HTTP file and five-second deadline are unchanged. |
| PRV-16 | Four reviewer authorities are pinned, latest verdict wins per record, and the original seven-result order is enforced. This shipped configuration ends with RE; RF is not yet incorporated. |

D-026 and D-029 remain unchanged. D-031 quotes the owner's sole retained-test exception: only `test_PRV14_third_authority_is_pinned_and_latest_verdict_controls` was rewritten. Its first half uses the real four-authority pins; its second omits the fourth pinned inputs as fixture data, with unchanged assertions and validation. The other 226 earlier methods remain unchanged. Complete before/after text and diff are in the developer report. D-032 records developer validation, not a new owner policy.

## Evidence and its limits

Developer validation passed five consecutive complete `make test` runs of **241 methods each**, including all eleven HTTP methods each time. Worker wait was **2.12–2.44 seconds**. All nine required check/gate targets passed; the original 480-order search had zero doubles, unauthorized releases or audit failures.

Fable independently reproduced the reported results and passed five further consecutive complete 241-method runs. Its extended search added 2,640 orders: **3,120 stepwise orders in total**, with zero double approvals, unauthorized releases or audit failures. Its new 15 probes produced 12 OK and three NOTE, with 439 assertions and zero failed assertions. The original 21 RE probes remain 19 OK with C9c/C9g NOTE. This is evidence for the tried scenarios, not a proof of every possible provider or client workflow.

Fable verified all 227 earlier methods are present, 226 unchanged, with the D-031 rewrite only; schema, Y05, HTTP deadline, 1,198 protected inputs, the patch and all 1,790 delivered payload files are intact. Original register faults remain 37/37 and 44/44. The older RD/RE fault scripts remain 34/37 and 29/35 because they assume an earlier latest authority; exact case IDs and reasons are recorded. Fable's new fourth-authority faults pass 62/62 and RF gate faults 56/56. Do not weaken latest-wins or edit original fault cases to erase obsolete expectations.

Independent testing stayed within fictional local preparation, principally two periods and one card account. Journals were excluded; the target-selection HTTP route was not independently probed beyond the developer tests. No real provider or human operating readiness was verified.

## Owner observations remain open

These are observations, not corrective tickets or implementation assignments.

| Observation | Meaning and owner action |
| --- | --- |
| UC-21 | Repeating a retired open-period row can add row/receipt versions before retiring it again. No double approval or release. Decide whether clause 5 should cover this repeat. |
| UC-22 | An unordered message against an ordered governing row may add evidence on every identical repeat. Decide whether mixed ordering is permitted and how unordered repeats should be identified. |
| UC-23 | A selector also contributes to the card run's period-level workpaper, inventory and package manifest. This is stricter in the safe direction. Decide whether to accept that scope or narrow it. |
| UC-24 | Opening an RE-prepared database with RF makes open-period approvals stale until re-preparation/review; frozen approvals remain intact. No decision now; carry this into upgrade notes before retaining databases across versions. |
| UC-25 | Failed-record citation text is not checked against the latest review; the D-031 fixture derives expected rows from the checker and is less independent. Fable accepted it within the owner's conditions; no required action. |

U4, UC-14, UC-17, UC-18 and UC-20 remain open. Expected NOTE behavior, including X08, N02c, N04e, C9c and C9g, stays unchanged. UC-9 remains reading only; journals remain excluded.

## Next work needs a specific assignment

No new implementation is authorized. A separately assigned reconciliation pass would need to incorporate the RF results/report as the next pinned authority, derive the same seven rows in order, and record the three independently accepted scopes with their exact RF checkpoint and evidence. It must preserve product decisions and acceptance criteria, all owner wording, original inputs and archives. Adding a fifth authority may conflict with retained tests that assume four; identify and report those conflicts before adapting any method. D-031 is not a general test-edit exception.

After recording independent verification, human G0 remains a separate accounting-owner decision. No G1 sample processing, Batch 3, Proposed/deferred capability, real integration, paid/model service, sending, posting, payment, hosting or deployment follows automatically.

D-016/D-017 and every BB-01/BB-02 field remain unchanged. Existing permission to document November procedures outside the application using existing client access is distinct from loading client records. Application processing still requires human G0 and explicit G1 authorization. December 2026 remains the held-out validation month, separate from November teaching cases; both client requirements still read Not started.

For a new chat: read this handoff and the latest RF report first, preserve the checkpoint and all current files, and obtain the owner's specific next assignment before changing code, tests, authority pins, register states or readiness gates. A request to prepare this handoff authorizes this note only.
