# Seven probe adaptations: exact changes and preserved controls

The original full command on current source exits **1**, with **29 OK, 3 ERROR and 3 WEAK**. Seven positive setups are adapted because RT14b can print OK despite never reaching its intended eligible starting state. The other six affected IDs are actual original-command failures. All 22 supplied independent files remain unchanged; the original script checksum is `14dc161e7cebd7624b824a5e4765b66e26a5f6a82fbe9da734928ab846fa328d`.

Three corrections specifically required by Fable change the positive setup contracts:

| Required correction | Input the original positive setup uses | Current requirement |
| --- | --- | --- |
| RV-11 | Mandate freshness `{}` | A valid nonempty freshness predicate, or explicit `{'none': '<reason>'}` demonstration authority, recorded at independent approval. |
| RV-12 | Replace a receipt and immediately expect eligibility | Expose the revision history, hold the item, then require acceptance by a granted non-supplier before separate final review. |
| RV-15 | Declare purchases distinct without supporting every candidate | Cite a supporting document for the item and each duplicate candidate. |

The separate `review/fable_reverification_probes.py` is generated from the untouched original by `scripts/build_reverification_adapter.py`. The complete delta is `reverification-probe-adaptations.patch`. It changes positive authority/evidence setup and adds assertions; original expected accounting outcomes and final verdict conditions remain. No new grant, actor or application bypass is introduced.

## RN02 — locked-period transaction movement

**Original failure:** The recurring-run setup calls `create_mandate(..., freshness={})` and raises `Nonempty freshness predicate required`. It stops before recurrence and reopen checks.

**Adaptation:** Replace only that empty predicate with an explicit fixed-evidence demonstration reason in `{'none': '<reason>'}`. The original separate human mandate approval remains.

**Preserved assertions:** Under lock, neither manual nor recurring December execution produces the moved item, November stays approved and the source-move quarantine is visible. After authorized reopen, the old approval is stale, there is at most one current governing artifact across periods, the destination item exists and its receipt follows it. The exact `held_while_locked`, `ok`, `follows` and return expressions remain unchanged.

**Observed outcome:** No December item under lock; November approval preserved. After reopen November has no governing A1, its historical approval is stale and December has the sole current A1 with its receipt. Other statement/revised-evidence holds remain; this probe does not require a clean destination approval.

## RN03 — artifact identity and rejection survive re-execution

**Original failure:** Its empty-freshness mandate aborts before final identity/review checks.

**Adaptation:** Supply the same explicit no-evidence demonstration form for this fixed-input scenario. Issuer, approver, schedule and execution attempts remain as written.

**Preserved assertions:** Exactly one A1 artifact; same ID/hash; A1 rejected and A2 approved; the additional preparer appears in contributors; that person is refused review with 403; contributors remain outside immutable payload identity. The entire final `ok` and return expressions remain unchanged.

**Observed outcome:** All identity/status conditions hold and the contributor's approval attempt returns 403.

## RN07 — explicit human identity is required

**Original failure:** The human preparer's mandate proposal uses `{}` and aborts before the service-approval test.

**Adaptation:** Make that human-created proposal valid with the explicit no-evidence reason. This mandate is deliberately not approved by a human in this probe: the next operation asks a service identity to approve it and must be refused.

**Preserved assertions:** Missing/invalid actor kinds are refused. Every service attempt at the listed human powers returns 403 despite human-looking names or grants. A granted human reviewer can still approve a clean item. The service-create negative input, original actors/grants, final `ok` and return remain unchanged.

**Observed outcome:** All service attempts return 403, including mandate creation/approval, while the human approval succeeds.

The explicit no-evidence form for these three tests is expressly allowed by RV-11. It authorizes unchanged fixture evidence; it does not demonstrate real evidence freshness. RT10a exercises freshness and recovery. RT10b's negative empty predicate remains unchanged and must be refused. A separate regression checks malformed predicates and the approval audit's stated no-evidence reason.

## RT12a — ordered source delivery with legitimately revised support

**Original failure:** Older/conflicting-delivery checks pass, but the legitimate sequence-7 update changes the transaction and receipt from 50.00 to 55.00. The new revised-evidence hold makes immediate eligibility false.

**Adaptation:** Before checking the new amount/eligibility, assert `EVIDENCE_REVISED_REQUIRES_REVIEW` and revision history; obtain `revised_evidence_accepted` from the original granted dispositioner, who supplied neither version; re-prepare through the service.

**Preserved assertions:** The four old/conflicting deliveries leave the accepted amount 50.00; four retention events exist; replay is recognized; genuinely newer sequence 7 produces 55.00 and becomes eligible. The original final `ok` and return expressions remain unchanged.

**Observed outcome:** All conditions pass. Final review is still pending in this probe. Separate regressions assert revision fields/history, refusal of suppliers and independent final approval.

## RT14a — dispositions, independent review and revocation

**Original failure:** Its two intended positive distinct-purchase decisions omit peer receipts and are refused. The later successful-review/revocation path is therefore unavailable.

**Adaptation:** The shared helper adds candidate receipt references only to default-evidence `distinct_purchases` calls. Explicit `evidence=[]` remains empty. The probe body and final conditions are unchanged.

**Preserved assertions:** Wrong currency-clearing choices, missing authority, incorrect split sums and empty evidence are refused. Supported decisions succeed. The exact 20.00 repairs / 15.00 supplies / 35.00 liability split remains. Referral does not clear currency. A proposed rule stays unapproved. The dispositioner cannot review their own item, another reviewer can, and revocation restores the duplicate hold.

**Observed outcome:** All conditions pass, including 403 for dispositioner review and successful independent review. No evidence is added to RT14d's explicitly insufficient own-row input.

## RT14b — new duplicate candidates invalidate prior decisions

**Original limitation:** After RV-15 the old initial decisions are refused. D1 starts blocked and stays blocked, so the original final expression prints OK without proving candidate invalidation.

**Adaptation:** Cite own and peer receipts, still without the statement. The strengthened adapted probe now explicitly asserts that **each D1/D2 disposition returns `ok`**, re-prepares, then asserts **D1 exists and is eligible before D3 is even constructed or intaken**. A failed setup raises AssertionError, which the unmodified runner records as ERROR and exit 1.

The added preconditions are:

```python
assert initial_result[0] == 'ok', ('Initial distinct-purchases disposition must succeed', k, initial_result)
# After both decisions and re-preparation, before D3 arrives:
assert initial_d1 is not None and initial_d1['eligible'], ('D1 must be eligible before D3 arrives', brief(initial_d1))
```

**Preserved assertion:** D3's arrival must prevent D1 from remaining eligible without `POSSIBLE_DUPLICATE`. The original final return expression is unchanged; the normal regression also explicitly requires the duplicate blocker and ineligibility.

**Observed outcome:** Initial D1 and D2 decisions succeed; D1 becomes eligible with no blockers; after D3, D1 is ineligible with `POSSIBLE_DUPLICATE` and both candidates listed.

Two new fault-injection regression methods verify that the strengthened probe raises the intended assertion when (a) either D1 or D2's initial decision is refused, and (b) D1 is initially ineligible. These test-only helper substitutions never edit accounting records. The existing service regression independently asserts the actual eligible-to-held transition without statement dependency. Logs: `rt14b-strengthened-probe.txt` and `rt14b-fault-regressions.txt`.

`rt14b-positive-preconditions.patch` isolates this user-requested strengthening against the prior adapted script retained in `before-rt14b-strengthening/`. The complete original-to-current adapter patch remains available separately. Final reruns passed all 136 tests, offline checks, the Batch 2 gate (29 PASS / 10 FIXED / 21 DEFERRED-OK), and the current re-verification gate (28 unchanged probes, all 35 adapted probes and the unmodified frozen corrective checkpoint).

## RG0 — teaching-month outcomes, impact and isolation

**Original failure:** Two distinct-purchase decisions lack peer support and revised TX-009 support lacks independent acceptance. Only eight items are approved, five are held and the original account-impact calculation fails.

**Adaptation:** Add peer receipts to the positive duplicate decisions and explicitly accept TX-009's revised support after first asserting its revision hold/history. The original probe already supplies the corrected receipt; the adapter adds the required independent control over that revision.

**Preserved assertions:** Eleven approvals; only TX-007 and TX-011 carried with dispositions; exact hand-calculated impact; acknowledgement required; two finalized packages; recorded lock; independent reviewer/finalizer; October quarantine disclosed; second-client isolation and audit integrity. `hand`, `independent`, `isolated`, `month` and the final return expressions are unchanged.

**Observed impact:** Office supplies +391.00, repairs +200.00, card liability −291.00 and cash −300.00, net zero. All original month/isolation conditions pass. No expected count is lowered.

The delivered `synthetic_month.py` instead keeps TX-009's original 79.99 receipt and refers the mismatch: ten approvals and three held dispositions, supplies +311.00 and liability −211.00. That is a separately documented allowed route, not the eleven-approval result claimed for adapted RG0. Neither path constitutes actual client authority or final close.

## Execution, preservation and independent judgment

```sh
make test
make check
make batch2-gate
make reverification-gate
```

The last target runs 28 unchanged-setup probes directly from the supplied script, all 35 original control assertions through the explicit current setup, and the unmodified historical corrective verifier on its frozen archive. Normal tests also run the positive-setup failure regressions and preservation checks.

The original full command remains:

```sh
python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .
```

Its current nonzero result is disclosed in `current-original-probes.txt`. The original 22 files and three historical archives remain unchanged. Previous developer-release logs are retained in `before-rt14b-strengthening/`; final rerun results use `final-*-release.txt` and `execution-results.json`.

The adapter generator checks original verdict/gate expressions; the retained diff and independent expression comparison include the RG0 hand calculation/month/isolation conditions. Expression identity alone does not prove the changed setup is valid. These document-presence fixtures also do not establish real receipt authenticity. Fable must judge the exact setup/helper changes under the API-change exception permitted by the corrections JSON. Independent acceptance and G0 remain pending.
