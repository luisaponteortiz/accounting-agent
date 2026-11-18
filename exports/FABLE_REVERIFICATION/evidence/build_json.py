"""Builds FABLE_REVERIFICATION_CORRECTIONS.json and FABLE_REVERIFICATION_RESULTS.json from the
recorded evidence, so that probe verdicts and case statuses are copied, not retyped."""
import json, os, re, sys

out_dir, work_root = sys.argv[1], sys.argv[2]
ev = os.path.join(out_dir, 'evidence')
NOTICE = ('Review output only. Authorises no connection, posting, payment, model call, hosting, deployment or policy '
          'activation, and opens no readiness gate. All data fictional.')
PROBE_CMD = 'python3 fable_reverification_probes.py <project-root>'

# ---- probe verdicts, read from the recorded run ------------------------------------------------
probes = []
for line in open(os.path.join(ev, 'probe_stdout.txt')):
    m = re.match(r'^(R[A-Z0-9a-z]+)\s+(\S+)\s+(OK|WEAK|NOTE|ERROR)\s+(.*)$', line.rstrip())
    if m:
        probes.append({'id': m.group(1), 'requirement': m.group(2), 'raw_verdict': m.group(3),
                       'status': {'OK': 'PASS', 'WEAK': 'FAIL', 'NOTE': 'NOTE', 'ERROR': 'NOT_RUN'}[m.group(3)], 'checks': m.group(4)})
V = {p['id']: p['status'] for p in probes}
assert len(probes) == 35, len(probes)

# ---- defects ------------------------------------------------------------------------------------
D = []
def defect(i, prio, title, affects, source, repro, expected, actual, consequence, correction, assertions, tests, depends=(), client=None, probe=None):
    D.append({'id': i, 'priority': prio, 'classification': 'confirmed_defect', 'title': title, 'affected_requirements': affects, 'source': source,
              'probe': probe, 'minimal_reproduction': repro, 'expected': expected, 'actual': actual, 'accounting_or_control_consequence': consequence,
              'smallest_sufficient_correction': correction, 'depends_on': list(depends), 'acceptance_assertions': assertions,
              'regression_tests': tests, 'decision_requiring_client_authority': client})

defect('RV-01', 'P1', 'A charge approved in a locked period can be approved again in another period through supersession under a new source key',
       ['C-01', 'T-12', 'T-18 (cross-period invariant)'],
       ['accounting_agent/source_control.py source_revision lines 39-49 (supersedes handling; approved-source event only for the same key)',
        'accounting_agent/service.py bind_source lines 193-224 (move detection looks only at earlier versions of the same kind and key)',
        'accounting_agent/modules.py card_prepare line 164 (transition blocker only when supersedes_source_id is inside the data)'],
       ['Approve item A1 (3 Nov) and lock November; open December.',
        "Intake a new transaction key A1X dated 2 Dec, same amount, with envelope field supersedes='demo_card_001:A1', its receipt and a December statement.",
        'Run December card preparation and approve A1X with an independent reviewer.'],
       'The engine has been told A1X replaces A1. While November is locked, A1X is quarantined (SOURCE_MOVED_FROM_LOCKED_PERIOD) exactly as a re-dated A1 is, and an event is raised against the approval of A1.',
       'A1X is admitted to December with no blocker and is approved. A1 stays approved in locked November. No accounting event and no source exception is recorded; the head of A1 is marked removed inside the locked period.',
       'The same expense and liability are proposed in two periods under two approvals. This is the outcome C-01 was written to prevent, reached through the supersession link instead of a re-dated version.',
       ['In source_revision, when supersedes resolves to an existing head: look up the latest admitted binding of the superseded source. If it is in a locked period, bind the new source admitted=0 with reason SOURCE_MOVED_FROM_LOCKED_PERIOD, write a source_moves row (blocked=1) and do not change the superseded head until that period is reopened.',
        'If the superseded source has an approving decision on any artifact, record accounting event APPROVED_SOURCE_SUPERSEDED for its period and item key.',
        'Treat envelope-level supersedes the same as data.supersedes_source_id for the transition blocker: pass the resolved link to the handler (for example in ctx) so SOURCE_TRANSITION_REQUIRES_REVIEW is raised either way.',
        'On reopen of the origin, re-evaluate as for a moved version: the superseded source leaves the origin population and its approval becomes stale.'],
       ['Probe RN02b reports OK: December has no governing artifact for A1X while November is locked.',
        "state.source_exceptions lists A1X with SOURCE_MOVED_FROM_LOCKED_PERIOD; export.source_move_history has a row from 2026-11 with blocked=1.",
        'Probe RT12d: an event whose code starts with APPROVED_SOURCE is recorded for the superseded, approved A1.',
        'With envelope-level supersedes in an open period, the new item carries SOURCE_TRANSITION_REQUIRES_REVIEW.',
        'Probe RN02 and FV-C13 results are unchanged.'],
       ['probe RN02b', 'probe RT12d (supersession part)', 'new unit test: supersession into another period while origin locked, then reopen', 'FV-C13', 'existing lock/move/reopen invariant test'],
       depends=['RV-03'], probe='RN02b, RT12d')

defect('RV-02', 'P1', 'Double-recording hold disappears when the cited source receives any later version',
       ['T-15 criterion 2 (a journal citing a source that already has a card-derived entry is held)'],
       ['accounting_agent/service.py context lines 241-251 (ownership matched on snapshot id and hash of the current version only)',
        'accounting_agent/service.py intake lines 334-338 (origin reference validated against any stored snapshot)'],
       ['Card item A1 (40.00) is prepared. Intake journal J1 for 40.00 with origin_sources citing the A1 snapshot, with bound support.',
        'Both items carry SOURCE_ALREADY_HAS_ENTRY (correct).',
        "Intake a new version of A1 that differs only in spacing of the description ('Acme  Paper  Demo'). Re-run both workflows.",
        'Approve the card item and the journal with an independent reviewer.'],
       'Both items stay held until one of them is withdrawn or dispositioned; a superseded origin reference is itself flagged.',
       'Neither item has a blocker after the revision; both are approved. The 40.00 expense is proposed twice.',
       'One source produces two approved proposed entries in one book. Any routine feed revision of a card row silently releases the hold.',
       ['Resolve ownership by source identity, not by version: an origin reference claims (kind, source_key); compare it with the current head of that key in the period population.',
        "When a journal's cited snapshot is no longer the head of its key, add blocker ORIGIN_SOURCE_SUPERSEDED to the journal so it must be re-supplied against the current version.",
        'Keep the intake check that every origin reference resolves to a stored snapshot in scope.'],
       ['Probe RT15 reports OK: after the cosmetic revision both items still carry SOURCE_ALREADY_HAS_ENTRY and the journal also carries ORIGIN_SOURCE_SUPERSEDED.',
        'Re-supplying the journal against the current snapshot leaves SOURCE_ALREADY_HAS_ENTRY on both.',
        'FV-J01 to FV-J10 unchanged.'],
       ['probe RT15', 'new unit test: claim survives source revision', 'existing origin-collision test'], probe='RT15')

defect('RV-03', 'P1', 'An item whose source has left the period remains a stale governing item and blocks finalization permanently',
       ['T-12 criterion 2 (a tombstoned pending authorisation produces no artifact and no blockers)', 'T-18', 'T-19', 'C-01 (state after reopen)'],
       ['accounting_agent/service.py governing_id lines 600-602 (latest completed run that ever produced the item key)',
        'accounting_agent/packages.py period_outcomes lines 11-21 and finalize_package line 31',
        'accounting_agent/exceptions.py record_exceptions lines 73-79 (only items in the current output are updated)'],
       ['Intake A1, A2 (posted, with receipts), pending P1 and a tying statement, all with as_of=1. Run card preparation.',
        "Intake P1 again with identical data, as_of=2, tombstone=true, removal_reason='feed_removed'. Re-run. Approve A1 and A2.",
        'Finalize the card package with an acknowledgement.'],
       'P1 is no longer part of the period: no governing item, no open exception, and the package can be finalized with the removal recorded.',
       "P1's old artifact is still reported as governing with status 'stale' and blockers MISSING_RECEIPT and PENDING_TRANSACTION. finalize_package returns 409 'Stale/disputed items cannot be finalized'. There is no service operation that clears it. The same residue is left in the origin period after a locked-period move is released (probe RN02).",
       'Any month in which the feed removes, voids or supersedes a row, or in which a row moves to another period, can never be finalized; close readiness reports an open exception for a row that no longer exists. The failure is in the safe direction but stops the workflow.',
       ['Define the governing item set of a workflow and period as the item keys output by its latest completed run. An artifact for a key absent from that run is not governing.',
        "In commit, when the last step of a run completes, mark exceptions of absent item keys 'superseded' with history, and record accounting event ITEM_LEFT_POPULATION with the removal, supersession or move reference.",
        'period_outcomes and state then omit such items from items and list them under removed_items; finalize_package records removed_items in the package.'],
       ['Probe RT12d reports OK for the finalization part: finalize succeeds after the tombstone and the package lists P1 under removed_items.',
        'state shows no governing artifact for demo_card_001:P1; exceptions for it are superseded with history rows.',
        'Probe RN02: after reopen, November has no governing artifact for the moved A1.',
        'FV-C13 unchanged.'],
       ['probe RT12d', 'probe RN02', 'new unit tests: tombstone, supersession and move each followed by finalize', 'FV-C13'], probe='RT12d, RN02')

defect('RV-04', 'P1', 'Any later intake re-binds the receipts of a locked period, records them as late activity and raises a false change event against a finalized package',
       ['T-12', 'T-18 (post-finalization events)', 'C-01 (evidence follows its transaction)'],
       ['accounting_agent/service.py intake lines 344-346 (every receipt head is re-bound after any changed intake)',
        'accounting_agent/service.py bind_source line 221 (a binding into a locked period is always recorded as LATE_ACTIVITY_IN_LOCKED_PERIOD, even when the source and its period are unchanged)',
        'accounting_agent/packages.py package_changes lines 47-53'],
       ['Prepare, approve, finalize and lock November (two charges with receipts). Open December.',
        'Intake December-only sources (one charge, its receipt, a December statement).',
        'Read state.source_exceptions and state.accounting_events.'],
       'November is untouched: no new source exception and no event.',
       "Both unchanged November receipts are listed with LATE_ACTIVITY_IN_LOCKED_PERIOD, and POST_FINALIZATION_CHANGE is recorded against the November package. Approvals and package bytes are intact.",
       'After the first intake of the following month, the quarantine list and the change-event trail of every locked period are wrong. A reviewer cannot tell a real late receipt or a real post-finalization change from this noise, and reopen decisions would be taken on false signals.',
       ['In intake, re-bind a receipt only when the period selected for it differs from its latest admitted binding, or when it has no admitted binding.',
        'In bind_source, when the latest binding of this same snapshot is already admitted in the selected period, write nothing.',
        'package_changes for a locked period compares against the frozen membership, so that no event is raised when nothing in that period changed.'],
       ['Probe RT12b reports OK: after December-only intake, source_exceptions is empty and accounting_events is empty.',
        'Probe RN02 still lists exactly the moved transaction and its receipt, and no unrelated receipt.',
        'Probe RT12c (receipt follows its charge in either arrival order) still reports OK.',
        'A genuinely revised November receipt arriving after lock is still listed as LATE_ACTIVITY_IN_LOCKED_PERIOD.'],
       ['probe RT12b', 'probe RT12c', 'probe RN02', 'existing test_late_locked_evidence_preserves_approval_until_reopen'], probe='RT12b')

defect('RV-05', 'P1', 'A vendor mapping removed from the approved profile keeps producing clean, approvable matches',
       ['T-09 (supersession is a real control; handlers receive only approved rules in force)'],
       ['accounting_agent/service.py onboard lines 107-111 (rules are proposed only for vendors present in the new profile)',
        'accounting_agent/controls.py rules_at lines 102-106 and approve_profile_version lines 30-42'],
       ["Approve the demo profile (vendors demo_acme and demo_metro). Register version v2 without demo_metro, effective 2026-11-01, and approve it.",
        "Intake a 'METRO REPAIR DEMO' charge dated 4 Nov with receipt and statement; run card preparation."],
       'Under v2 the Metro alias is unknown: the item is held with UNKNOWN_VENDOR.',
       "The item is eligible with vendor demo_metro and category DEMO_REPAIRS, while state.profile.vendors shows only demo_acme.",
       'A mapping the client has withdrawn continues to code expenses with no blocker, and the approved profile shown to the reviewer does not contain it.',
       ['On approve_profile_version, for every approved profile-derived rule whose key is absent from the new profile (vendor mappings; and any other profile-derived kind), record a retirement that ends it the day before the new profile takes effect. Because policy_rules is immutable, add an append-only rule_retirements(rule_id, effective_to, actor, profile_id) table and have rules_at honour it.',
        'Retirement is part of the same independent approval and appears in the audit and export.'],
       ['Probe RT09c reports OK: the Metro item carries UNKNOWN_VENDOR under v2.',
        'An item dated before the effective date of v2 in an earlier period still matches the retired mapping (rule in force for that date).',
        'Probes RT09a and RT09b unchanged; FV-C01 and FV-C15 unchanged.'],
       ['probe RT09c', 'new unit test: retirement respects effective dates', 'probe RT09b'], probe='RT09c')

defect('RV-06', 'P1', 'Under the shipped checklist a document label alone satisfies the bank reconciliation and AP/AR tie-out requirements',
       ['T-19 (typed requirements; a label cannot complete deferred reconciliation or tie-out work)', 'F-11'],
       ['accounting_agent/modules.py close_readiness lines 283 and 293 (an untyped string is treated as a document requirement and is satisfied by any document of that type)',
        "accounting_agent/config/bird_bowl.demo.json required_close_evidence (five untyped strings); the validation base profile in review/FABLE_VALIDATION_CASES.json",
        'accounting_agent/controls.py validate_rule line 68 and service.py validate_profile lines 78-82 (untyped strings accepted)'],
       ["With the shipped demo profile, intake five documents whose only content is a label: types trial_balance, card_statement, bank_reconciliation, ap_tieout, ar_tieout, period_id 2026-11.",
        'Prepare and approve the card items, then run close_readiness.'],
       'bank_reconciliation, ap_tieout and ar_tieout stay unsatisfied until a verified workpaper from the (deferred) capability exists.',
       "All five requirements report satisfied=true and MISSING_CLOSE_EVIDENCE is absent. The typed form of the same requirements is correctly unsatisfied (same probe). The artifact still carries FINAL_CLOSE_SIGNOFF_REQUIRED and EXTERNAL_STEPS_UNVERIFIED.",
       'The checklist shown to the controller says the bank reconciliation and both tie-outs are in place when nothing was reconciled. This is finding F-11 surviving in the delivered configuration; the typed control exists but the shipped profile does not use it.',
       ['Refuse untyped checklist entries in validate_profile and validate_rule: every entry is an object with type workflow_outcome, reconciliation, tieout or document.',
        "Convert the demo profile and the validation base profile to typed entries (bank_reconciliation as reconciliation; ap_tieout and ar_tieout as tieout; card_statement as workflow_outcome of card_preparation or as a document, stated explicitly; trial_balance as document until trial-balance intake exists).",
        'Existing stored untyped rules are evaluated as unsatisfied with reason UNTYPED_REQUIREMENT.'],
       ['Probe RT19a reports OK: with label-only documents, bank_reconciliation, ap_tieout and ar_tieout report satisfied=false and MISSING_CLOSE_EVIDENCE is present.',
        'A profile or close_checklist rule containing a bare string is refused with 400.',
        'FV-CL01, FV-CL02 and FV-CL04 keep their expected blockers.'],
       ['probe RT19a', 'FV-CL01', 'FV-CL02', 'FV-CL04', 'existing typed-close test'],
       client='For a real client: the close checklist, and which named evidence each line requires (client question 13).', probe='RT19a')

defect('RV-07', 'P2', 'Disposition choices are not tied to the kind of activity or account: a card payment can be approved as a credit to an expense account',
       ['T-14 (closed vocabulary)', 'T-15 (signed settlement and credit effects)'],
       ['accounting_agent/exceptions.py VOCABULARY lines 6-14 and disposition lines 39-50 (activity checked only for settlement and transfer; account type never checked)',
        'accounting_agent/modules.py card_prepare lines 207-217 and 222-229'],
       ['Intake a payment of -300.00 (activity payment) with receipt and a tying statement.',
        "Disposition NON_EXPENSE_REQUIRES_REVIEW as standalone_credit, UNKNOWN_VENDOR as confirm_vendor and UNKNOWN_CATEGORY as code_category, each with account DEMO_OFFICE_SUPPLIES.",
        'Re-run and approve with an independent reviewer.'],
       "A payment can only be dispositioned as settlement_of_card_liability (or referred); credits and coding choices require the matching activity and an account of the right type.",
       'The item becomes eligible with entry Dr DEMO_CARD_LIABILITY 300.00 / Cr DEMO_OFFICE_SUPPLIES 300.00 and is approved.',
       'A liability settlement is recorded as a 300.00 reduction of expense. It takes two people making an explicit wrong choice, but the vocabulary is presented as closed and does not stop it.',
       ["standalone_credit and refund_of require activity credit, or purchase with a negative amount.",
        "Activity payment accepts only settlement_of_card_liability or refer_external; activity transfer only transfer or refer_external. Give fee, interest and unknown their own explicit choices (for example code_fee with an expense account; refer_external).",
        'code_category, confirm_vendor, standalone_credit, refund_of and allocate require an active expense account; settlement and transfer require an active asset account that is not the card liability.'],
       ['Probe RT14e reports OK: the standalone_credit disposition on a payment is refused.',
        'A code_category disposition naming DEMO_CARD_LIABILITY or DEMO_CASH is refused.',
        'Probe RT14a and the teaching-month probe RG0 are unchanged (TX-006 credit and TX-012 payment still resolve as before).'],
       ['probe RT14e', 'probe RT14a', 'probe RG0', 'existing transfer-direction test'],
       client='For a real client: how fees, interest and card payments are to be treated, and which accounts each disposition may use (client questions 3 and 4).', probe='RT14e')

defect('RV-08', 'P2', 'A distinct-purchases disposition stays in force when a new duplicate candidate arrives',
       ['T-14 (evidence-bound dispositions)'],
       ['accounting_agent/exceptions.py active_dispositions lines 17-25 (bound to the item hash and cited evidence only)', 'accounting_agent/modules.py card_prepare lines 183-187 and 210'],
       ['Two identical charges D1 and D2 with distinct receipts. Disposition each as distinct_purchases citing its own charge and receipt. Re-run: both eligible.',
        'Intake a third identical charge D3 with its own receipt and an updated statement. Re-run.'],
       'D1 and D2 return to POSSIBLE_DUPLICATE because the decision did not consider D3.',
       'D1 is eligible with no blocker; D3 is listed among its duplicate candidates. (If the disposition had cited the statement, it would have lapsed for an unrelated reason.)',
       'A human decision about two charges is silently extended to a third. The item is re-prepared and needs a new approval, so the reviewer can still see the candidate list, but the control that asked for a decision is gone.',
       ['Store the sorted duplicate-candidate set (source key and hash) in the disposition payload at decision time, taken from the governing artifact.',
        'active_dispositions treats a POSSIBLE_DUPLICATE disposition as inactive when the current candidate set differs.'],
       ['Probe RT14b reports OK: after D3 arrives, D1 carries POSSIBLE_DUPLICATE and is not eligible.', 'Probe RT14a unchanged.'],
       ['probe RT14b', 'probe RT14a'], probe='RT14b')

defect('RV-09', 'P2', 'After one charge is excluded as a duplicate, the surviving charge can only be cleared by a false distinct-purchases statement',
       ['T-14 (duplicate exclusion)'],
       ['accounting_agent/modules.py card_prepare lines 183-187 (the excluded charge still counts as a candidate)'],
       ['Two identical charges D1 and D2. Disposition D2 as duplicate_of D1. Re-run.'],
       'D2 is excluded with no entry (correct) and D1, the charge that remains, is no longer held as a possible duplicate of the row just excluded; it cites that disposition.',
       'D2 is held with DUPLICATE_EXCLUDED and has no entry (correct). D1 still carries POSSIBLE_DUPLICATE, and the only vocabulary for it is distinct_purchases, duplicate_of or source_replay.',
       'The real charge can never be approved truthfully. In practice someone will record distinct_purchases, which is the opposite of what was decided.',
       ['When computing duplicates for an item, leave out a candidate that carries an active duplicate_of or source_replay disposition naming this item, and add that disposition id to the item\'s disposition_ids so the result cites it and its author joins the item lineage.'],
       ['Probe RT14c reports OK: D1 has no POSSIBLE_DUPLICATE blocker, cites the disposition, and the dispositioner cannot approve D1.', 'Revoking the disposition restores POSSIBLE_DUPLICATE on both.'],
       ['probe RT14c', 'probe RT14a'], depends=['RV-08'], probe='RT14c')

defect('RV-10', 'P2', 'The author of a vendor mapping regains review rights when a colleague re-proposes the rule with a cosmetic change',
       ['C-04', 'T-09 addition (independence uses the proposer and approver of each applied rule)'],
       ['accounting_agent/service.py commit lines 518-523 (lineage takes only the applied version of the rule)'],
       ["Reviewer-to-be proposes mapping demo_acme version 1 (alias and category); a policy approver approves it.",
        "A colleague proposes version 2 superseding it, changing only the display name; a second approver approves it.",
        'Prepare an ACME charge and have the author of version 1 approve it.'],
       'Refused: the alias and category that coded the item were authored by this person.',
       'Accepted. The contributor list holds only the proposer and approver of version 2. (The equivalent case for chart and entity fields in the profile is handled correctly: probe RN05.)',
       'The person who wrote the coding rule approves the items it codes. It needs a colleague and an approver to pass a cosmetic revision, which is why this is P2 and not P1.',
       ['For an applied vendor_mapping or receipt_matching rule, include the proposer and approver of every earlier version in its supersession chain (same kind and key) unless that version\'s value fields used by the item (matched alias, category; matching parameters) differ from the applied version.'],
       ['Probe RN05b reports OK: the author of version 1 is refused with 403.', 'A reviewer who authored an earlier version with a different category is not barred.', 'Probes RN04, RN05 and RT09b unchanged.'],
       ['probe RN05b', 'probe RN05', 'probe RN04'], probe='RN05b')

defect('RV-11', 'P2', 'A mandate may be created and approved with an empty freshness predicate',
       ['T-10 (freshness predicate; no run without fresh required evidence)', 'F-07'],
       ['accounting_agent/service.py create_mandate line 666 (any dict accepted)', 'accounting_agent/controls.py mandate_fresh lines 138-145',
        'accounting_agent/demo.py create_fixture_mandate lines 43-50 (defaults to an empty predicate; used by every mandate probe in the maintained harness)'],
       ["create_mandate(..., period_rule={'kind':'fixed','period_id':'2026-11'}, freshness={}); approve it; tick on three consecutive days with no new evidence."],
       'Creation is refused, or the mandate records an explicit statement that no evidence is required which the approver must accept.',
       'The mandate is accepted and dispatches a run for every slot on unchanged evidence (three runs in the probe). Unknown source kinds and malformed cut-offs are also accepted at creation.',
       'The T-10 criterion is met only when the issuer chooses to declare a requirement. The original weakness (a schedule that re-runs regardless of evidence) remains available by default.',
       ['create_mandate requires at least one entry; each key must be a source kind read by one of the mandate workflows and each value occurrence_start or a valid timestamp.',
        "If a no-evidence mandate is wanted for demonstrations, require an explicit {'none': '<reason>'} form that is shown in the approval audit event.",
        'create_fixture_mandate states a real predicate.'],
       ['Probe RT10b reports OK: creation with {} is refused with 400.', 'Probe RT10a unchanged.', 'Existing dedup, cap, expiry and revocation tests pass with an explicit predicate.'],
       ['probe RT10b', 'probe RT10a', 'existing mandate tests', 'maintained probes P03 to P05, N11, N12'],
       client='For a real client: what evidence must be new before each recurring run.', probe='RT10b')

defect('RV-12', 'P2', 'A receipt mismatch can only be cleared by re-supplying the receipt, and the reviewer is not told the evidence was revised',
       ['T-17', 'T-14', 'Batch 2 gate (full month with no weakened blocker)'],
       ['accounting_agent/exceptions.py VOCABULARY (no entry for any RECEIPT_* code)', 'accounting_agent/modules.py card_prepare lines 195-206 and evidence refs line 238',
        'scripts/synthetic_month.py lines 27-32 (TX-009 receipt amount changed from 79.99 to 80.00 by the preparer)'],
       ['Teaching fixture: TX-009 is 80.00 and its receipt says 79.99, so the item carries RECEIPT_AMOUNT_POLICY_UNSET.',
        'There is no disposition for that code. The delivered walkthrough re-supplies the receipt with amount 80.00; the item becomes eligible and is approved.'],
       'An item with a receipt exception can be carried by an explicit referral, and when supporting evidence is replaced the artifact says so and asks for a decision by someone other than the supplier.',
       'The only route is to change the evidence. The approved artifact cites receipt version 2 with no flag, no disposition and no reference to version 1.',
       'A preparer can make third-party evidence agree with the charge and obtain a clean item. The independent reviewer sees a version number only. The teaching-month result for TX-009 rests on this.',
       ["Add refer_external for RECEIPT_AMOUNT_*, RECEIPT_DATE_*, RECEIPT_VENDOR_*, RECEIPT_MULTIPLE_* and RECEIPT_CURRENCY_MISMATCH so the item can be carried without touching evidence.",
        "When an item relies on a supporting document whose version is above 1, list evidence_revisions (earlier version reference, changed fields, supplier) in the artifact and add blocker EVIDENCE_REVISED_REQUIRES_REVIEW, cleared only by disposition revised_evidence_accepted from a granted human who supplied none of the versions.",
        'Update scripts/synthetic_month.py to take one of these routes for TX-009.'],
       ['With the teaching fixture, re-supplying receipt-TX-009 at 80.00 yields EVIDENCE_REVISED_REQUIRES_REVIEW and evidence_revisions naming version 1 and the amount change.',
        'refer_external on RECEIPT_AMOUNT_POLICY_UNSET is accepted and the item stays ineligible.',
        'Probe RG0 reports the month complete with TX-009 either referred or accepted through the new disposition.'],
       ['probe RG0', 'new unit tests for evidence_revisions and the new disposition', 'FV-C17', 'FV-C18'],
       client='For a real client: the document policy, including who may accept a corrected receipt (client question 5).', probe='RG0')

defect('RV-13', 'P2', 'The statement workpaper does not disclose when line identity, continuity or provenance could not be checked',
       ['T-13 (population identity; limits when authoritative evidence is absent)', 'F-12'],
       ['accounting_agent/modules.py statement_checks lines 100-130 (line ids optional; continuity checked only when a prior statement is on file; provenance validated but unused)'],
       ["Statement for November without line_ids, provenance manually_keyed, supplied by the preparer in the same packet as the transactions; October is open with no statement.",
        'Replace one statement line by a different charge of the same amount.'],
       'The substituted item is held, or the workpaper and each item state that line identity and opening-balance continuity were not verified and that the statement was keyed by a contributor.',
       'Both items are eligible with no blocker. The workpaper has only account_id, evidence, unreconciled_population, execution and external_reconciliation.',
       'Without line ids the control is again a count and totals supplied by the preparer. That limit is acceptable only if the reviewer is told.',
       ["Add to the workpaper and to each card item: line_identity (verified or not_supplied), opening_continuity (verified, no_prior_statement or prior_period_statement_missing) and statement_provenance with the supplying actor.",
        'When the prior period exists and has no statement, raise STATEMENT_PRIOR_PERIOD_MISSING on the account.',
        'Whether a statement without line ids may support approval is a client policy: until an approved rule says so, raise STATEMENT_LINE_IDENTITY_NOT_VERIFIED.'],
       ['Probe RT13n reports OK: the substituted item is not eligible, or the workpaper discloses line_identity=not_supplied.', 'Probe RT13 unchanged; FV-C08, FV-C09 and FV-C19 unchanged.'],
       ['probe RT13n', 'probe RT13', 'FV-C08', 'FV-C09', 'FV-C19'],
       client='For a real client: which document is the authoritative statement, whether it carries line identifiers, and how cycles map to periods (client questions 2 and 4).', probe='RT13n')

defect('RV-14', 'P3', 'The normalised alias is recorded only in the audit event, not where the approver reads the rule',
       ['T-09 addition (probe N18)'], ['accounting_agent/controls.py _propose_rule lines 76-83', 'accounting_agent/service.py state line 789'],
       ["Propose a vendor rule with alias 'ACME-PAPER/DEMO'. Read state.rules."],
       'The rule record shown for approval includes the normalised aliases and names any existing rule with the same normalised alias.',
       "The rule record holds the raw value only. The normalised form 'acme paper demo' is in the rule_proposed audit event. A collision is not reported at proposal; after approval the affected items are held as AMBIGUOUS_VENDOR, which is safe.",
       'The approver can approve a punctuation-only collision without seeing it; the consequence is held items, not wrong matches.',
       ['Add normalized_aliases and alias_collisions (rule ids) to each vendor_mapping row returned by state and export.'],
       ['Probe RT09d reports OK.'], ['probe RT09d'], probe='RT09d')

defect('RV-15', 'P3', 'A disposition may cite only the item\'s own source row as its evidence',
       ['T-14 (evidence-bound dispositions)'], ['accounting_agent/exceptions.py disposition line 38'],
       ['Two identical charges. Disposition D1 as distinct_purchases with evidence containing only the D1 transaction reference.'],
       'Refused: distinct purchases must cite supporting evidence for both charges.', 'Accepted.',
       'The evidence requirement can be met without any evidence. Receipt blockers still apply when receipts are required.',
       ['For distinct_purchases require at least one cited document that is not a transaction row for this item and one for each candidate; for other choices require at least one reference other than the item\'s own row.'],
       ['Probe RT14d reports OK.', 'Probe RT14a unchanged.'], ['probe RT14d', 'probe RT14a'], probe='RT14d')

defect('RV-16', 'P3', 'The change inventory and the patch omit two changed runtime files',
       ['Documentation accuracy (G0)'], ['scripts/build_change_report.py line 12 (only .py and .json files are inventoried)', 'docs/batch2/changed-files.json', 'docs/batch2/source-and-tests.patch'],
       ['Compare accounting_agent/web/app.js and index.html with exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip.'],
       'Every changed runtime file is in the inventory and the patch.', 'Both files differ from the baseline and appear in neither. All 46 listed hashes are correct.',
       'A reviewer working from the patch does not see the UI changes that expose dispositions, finalization and lock acknowledgement.',
       ['Include .js, .html and .css under accounting_agent/web in the inventory and the patch.'],
       ['evidence/static_checks.py reports no computed-but-unlisted file.'], ['evidence/static_checks.py'], probe='static check')

defect('RV-17', 'P3', 'Several packages can be finalized for one period and workflow with no link between them',
       ['T-18'], ['accounting_agent/packages.py finalize_package lines 23-45', 'accounting_agent/storage.py migration 12'],
       ['Finalize the card package; revise a source; re-prepare and review; finalize again.'],
       'The second package names the one it replaces, and state shows which package governs.', 'Two unrelated package rows exist for November card preparation.',
       'A handover reader cannot tell which package is current without comparing timestamps and events.',
       ['Add supersedes_package_id to the package payload when a package already exists for the period and workflow, and a governing flag in state.'],
       ['Probe RT18 prints no second-package observation, or the second package payload names package 1.'], ['probe RT18'], probe='RT18')

order = ['RV-04', 'RV-03', 'RV-01', 'RV-02', 'RV-05', 'RV-06', 'RV-07', 'RV-08', 'RV-09', 'RV-10', 'RV-11', 'RV-12', 'RV-13', 'RV-14', 'RV-15', 'RV-16', 'RV-17']
assert sorted(order) == sorted(d['id'] for d in D)

corrections = {
    'title': 'Fable corrective tickets after re-verification of C-01 to C-06 and Batch 2 (Accounting Agent OS, bundle FABLE_CORRECTIONS_AND_BATCH_2)',
    'authored': '2026-11-15', 'notice': NOTICE,
    'companion_files': ['FABLE_REVERIFICATION_REPORT.md', 'FABLE_REVERIFICATION_RESULTS.json', 'fable_reverification_probes.py', 'fable_reverification_output.txt'],
    'recommendation': 'Do not start Batch 3 and do not record gate G0 yet. Implement RV-01 to RV-06 (P1) first, then RV-07 to RV-13 (P2), in the order given, and return the source for re-verification.',
    'priority_counts': {p: sum(1 for d in D if d['priority'] == p) for p in ('P0', 'P1', 'P2', 'P3')},
    'implementation_order': order,
    'order_note': 'RV-04 first because it disturbs every multi-period test. RV-03 before RV-01 because the supersession fix relies on a defined state for items that leave a period. RV-08 before RV-09 because both change how duplicate candidates are bound.',
    'completion_gate': [
        PROBE_CMD + ' exits 0: no WEAK and no ERROR verdict. NOTE verdicts RT09d, RT13n and RT14d become OK when RV-14, RV-13 and RV-15 are done.',
        'make test, make check and make batch2-gate still pass; reviewer cases stay at 29 PASS, 10 FIXED, 21 DEFERRED-OK with no other status.',
        'The original unmodified script still passes on the frozen corrective archive (scripts/verify_corrective_checkpoint.py).',
        'fable_reverification_probes.py is run by make test, unmodified. If an API change makes a probe unrunnable, the change and the adapted probe are returned for review; expectations are not edited to pass.',
        'Each contract change is recorded in DECISIONS.md.'],
    'confirmed_defects': D,
    'unverified_concerns': [
        {'id': 'UC-1', 'concern': 'The mandate policy signature is built from the rules applicable to the sources currently in the target period, so evidence dated after a mid-period rule could change the signature and suspend the mandate although no policy changed.', 'source': 'accounting_agent/controls.py policy_signature line 148; service.py context lines 259-266', 'basis': 'code reading; not executed', 'direction': 'fails safe (false suspension)'},
        {'id': 'UC-2', 'concern': 'The prior-statement lookback for continuity uses the latest accepted head of the prior statement even when that version is quarantined as late activity for a locked prior period.', 'source': 'accounting_agent/service.py context lines 270-274', 'basis': 'code reading; not executed'},
        {'id': 'UC-3', 'concern': 'Revising a receipt that supports an approved item raises no APPROVED_SOURCE_REVISED event, because the event is matched on the item key of the changed source. The item does go stale.', 'source': 'accounting_agent/source_control.py lines 39-42', 'basis': 'code reading; not executed'},
        {'id': 'UC-4', 'concern': 'If a superseding source is later removed, the superseded head is not restored.', 'source': 'accounting_agent/source_control.py lines 43-49', 'basis': 'code reading; not executed'},
        {'id': 'UC-5', 'concern': 'Synthetic authority grants have no revocation and no rule that the administrator differs from the subject. Acceptable for fictional grants; must be designed before gate G1 (finding F-23).', 'source': 'accounting_agent/controls.py grant_authority lines 7-17', 'basis': 'code reading'}],
    'deferred_enhancements': [
        {'id': 'DE-1', 'note': 'Each item envelope carries the run-wide input fingerprint and the run-wide applied-rule list, so a same-period rule or source that affects one item sends every item of that workflow back for review (seen in probe RT09b). Conservative; narrowing it is an efficiency improvement, not a control fix.'},
        {'id': 'DE-2', 'note': 'With multiple receipts allowed, each receipt is still compared with the whole charge. Needs a client document policy.'},
        {'id': 'DE-3', 'note': 'Double-recording detection works within one period population; a journal in a later period citing an earlier period source is not detected. Belongs with settlement pairing and reconciliation in Batch 3.'},
        {'id': 'DE-4', 'note': 'Statement cycles must equal the accounting period. Non-calendar cycles remain deferred, as the developer states.'}],
    'decisions_requiring_client_authority': [
        'Whether the person who approves policy (profile or rule) may also review items prepared under it. The code bars them, which follows the earlier review; a small client may not have a third person.',
        'Document policy: date window, amount tolerance, multiple receipts, and who may accept a corrected or replaced receipt (client question 5).',
        'Which document is the authoritative card statement, whether it has line identifiers, and how statement cycles map to periods (client questions 2 and 4).',
        'Treatment of fees, interest, card payments and transfers, and the accounts each disposition may use (client questions 3 and 4).',
        'The close checklist and the named evidence each line requires; who gives final sign-off (client question 13).',
        'Who may disposition each exception type, finalize, and lock; and what evidence must be new before a recurring run.'],
}
json.dump(corrections, open(os.path.join(out_dir, 'FABLE_REVERIFICATION_CORRECTIONS.json'), 'w'), indent=1, ensure_ascii=False)

# ---- results ------------------------------------------------------------------------------------
cases = json.load(open(os.path.join(work_root, 'docs/batch2/final-validation.json')))
exit_codes = dict(l.strip().split(' exit=') for l in open(os.path.join(ev, 'exit_codes.txt')) if ' exit=' in l)
frozen = {}
for line in open(os.path.join(ev, '01_corrective_checkpoint.txt')):
    m = re.match(r'^([PN]\d+)\s+(OK|WEAK|NOTE|DEFERRED|ERROR)\s', line)
    if m: frozen[m.group(1)] = m.group(2)
maint = {}
for line in open(os.path.join(ev, '06_maintained_probes.txt')):
    m = re.match(r'^([PN]\d+)\s+(OK|WEAK|NOTE|DEFERRED|ERROR)\s', line)
    if m: maint[m.group(1)] = m.group(2)
carried = {'N01': ['RN01'], 'N02': ['RN02', 'RN02b'], 'N03': ['RN03'], 'N04': ['RN04'], 'N05': ['RN05', 'RN05b'], 'N06': ['RN06'], 'N07': ['RN07']}

def crit(text, status, evidence, note=None, defects=()):
    c = {'criterion': text, 'status': status, 'evidence': evidence}
    if note: c['note'] = note
    if defects: c['defects'] = list(defects)
    return c
P, F = 'PASS', 'FAIL'
tickets = {
 'T-09': ('FAIL', [
    crit('A proposed version or rule is never applied by a run.', P, ['RT09a', 'RT09b', 'RT17']),
    crit('The proposer cannot approve; a service actor cannot approve.', P, ['RT09a', 'RT09b', 'RN07']),
    crit('A rule effective on the first day of the next period is not applied to an item dated in the current period.', P, ['RT09b']),
    crit('After supersession, re-preparing an earlier period applies the rule that was in force for that date.', P, ['RT09b']),
    crit('Export shows, for every artifact, the rule ids and versions applied.', P, ['RT09b', 'inspection: service.py commit line 539'], 'The list is the run-wide set, not the rules used by that item (DE-1).'),
    crit('Added: independence uses the proposer and approver of each rule applied to the item; probe N05 stays refused.', P, ['RN05', 'maintained N05'], 'Earlier versions of a superseded rule are not included.', ['RV-10']),
    crit('Added: a rule effective in a later period leaves approvals in earlier periods intact; probe N17 reports OK.', P, ['RT09b', 'maintained N17']),
    crit('Added: alias approval shows the normalised form (probe N18).', F, ['RT09d'], 'Recorded in the audit event only.', ['RV-14']),
    crit('Adversarial: a mapping withdrawn by a newly approved profile stops applying.', F, ['RT09c'], None, ['RV-05']),
    crit('Adversarial: fixture approval and grant helpers are not reachable through HTTP.', P, ['inspection: accounting_agent/http.py routes; demo.py', 'delivered tests/test_http.py (11 tests, executed)'])]),
 'T-11': ('PASS', [
    crit('A client_sample profile with a null accounting basis yields no eligible journal artifact.', P, ['RT11']),
    crit('The demo profile yields the same results as before and its waivers appear in the export.', P, ['RT11', 'validation cases'])]),
 'T-12': ('FAIL', [
    crit('Probe P07: the newer amount stays current after the late older batch.', P, ['RT12a', 'maintained P07']),
    crit('A tombstoned pending authorisation produces no artifact and no blockers.', F, ['RT12d'], 'The old artifact stays governing with status stale and blocks finalization.', ['RV-03']),
    crit('FV-C13 holds the settled row and no longer reports the superseded pending row as an open item.', P, ['case FV-C13']),
    crit('Required behaviour: revision or removal of a source with an approved governing artifact raises an exception against that approval.', F, ['RT12d', 'RT18'], 'Raised for revision and removal; not for supersession.', ['RV-01']),
    crit('Added: supporting evidence is assigned to the period of the item it references and is listed even when it does not match; probe N09.', P, ['RT12c', 'maintained N09']),
    crit('Added: opening a period adopts every quarantined source that belongs to it; probe N08.', P, ['RT12c', 'maintained N08']),
    crit('Added: quarantined sources are included in the period status passed to close readiness.', P, ['RT19a', 'case FV-CL04']),
    crit('Adversarial: later intake for another period leaves a locked period untouched.', F, ['RT12b'], None, ['RV-04'])]),
 'T-10': ('PASS', [
    crit('Issuer cannot approve own mandate.', P, ['RT10a']),
    crit('No run is created for an occurrence without fresh required evidence.', P, ['RT10a'], 'Holds when a requirement is declared; an empty predicate is accepted.', ['RV-11']),
    crit('Changing a bound rule halts dispatch and is visible.', P, ['RT10a']),
    crit('Existing dedup, cap, expiry and revocation tests pass.', P, ['make test']),
    crit('Added: each occurrence prepares the period named by the period rule, not the calendar date of the slot.', P, ['RT10a']),
    crit('Adversarial: concurrent ticks and restart.', P, ['maintained N11, N12', 'delivered concurrency tests in make test'], 'Executed through the delivered harness and tests; not re-probed independently.')]),
 'T-13': ('PASS', [
    crit('A foreign-currency row appears as an unreconciled population item.', P, ['RT13']),
    crit('An opening-balance break blocks every item on that account.', P, ['RT13']),
    crit('Purchases, credits and payments tie separately.', P, ['RT13']),
    crit('FV-C08 and FV-C09 pass with statement inputs.', P, ['cases FV-C08, FV-C09'], 'Through the test-only adapter, which keeps the declared count and total defects.'),
    crit('Substitution detected when line ids are present.', P, ['RT13']),
    crit('Limits disclosed when line ids or the prior statement are absent.', 'NOTE', ['RT13n'], None, ['RV-13'])]),
 'T-14': ('PASS', [
    crit('Two duplicate candidates with a distinct_purchases disposition and distinct receipts become eligible and cite the disposition.', P, ['RT14a', 'RG0']),
    crit('A split disposition whose lines sum exactly becomes eligible; lines that do not sum are refused.', P, ['RT14a']),
    crit('A service actor cannot disposition; a disposition creates no active rule; revoking it re-blocks the item.', P, ['RN07', 'RT14a']),
    crit('An inventory step with NO_SOURCE_EVIDENCE blocks its dependants.', P, ['RT14f']),
    crit('Added: contributors are computed per item lineage (N14 flips, N04 stays refused).', P, ['RN04', 'maintained N14, N04']),
    crit('Adversarial: external referral or duplicate exclusion never produces a clean approval or a silent loss of ledger effect.', P, ['RT14a', 'RT14c', 'RG0']),
    crit('Adversarial: a disposition is bound to the facts it decided.', F, ['RT14b', 'RT14c', 'RT14d'], 'P2 and P3 residuals.', ['RV-08', 'RV-09', 'RV-15'])]),
 'T-15': ('FAIL', [
    crit('Each approved card item has exactly one proposed entry traceable to its source snapshot.', P, ['RT15', 'RG0']),
    crit('A journal citing a source that already has a card-derived entry is held.', F, ['RT15'], 'Held at first; released by any later version of the cited source.', ['RV-02']),
    crit('The sum of proposed entries by account for a period is reproducible from the export.', P, ['RG0']),
    crit('FV-J01 to FV-J07 still pass through the shared validator.', P, ['cases FV-J01 to FV-J07', 'inspection: core.py validate_entry used by both handlers']),
    crit('Adversarial: signed expense, credit, settlement and transfer effects.', F, ['RT14e', 'RG0'], 'Correct for the intended paths; a payment can be dispositioned as a credit to expense.', ['RV-07'])]),
 'T-16': ('PASS', [
    crit('FV-J08, FV-J09 and FV-J10 report FIXED.', P, ['cases']),
    crit('FV-J01 to FV-J07 still pass.', P, ['cases']),
    crit('Added: separate unit tests for unbound support, duplicate journal and no-effect journal.', P, ['tests/test_reviewer_probes.py test_P08_* (three tests, executed)', 'RT16'])]),
 'T-17': ('PASS', [
    crit('With no rule, FV-C17 and FV-C18 are still held, with policy-unset codes.', P, ['cases FV-C17, FV-C18', 'RT17']),
    crit('With an approved one-day window a receipt dated the day before posting matches; two days does not.', P, ['RT17']),
    crit('A proposed rule has no effect.', P, ['RT17']),
    crit('Added: test_P15 asserts behaviour.', P, ['inspection and execution of tests/test_reviewer_probes.py test_P15_receipt_tolerance_is_explicit_client_policy']),
    crit('Adversarial: an item with a receipt exception can be carried or resolved without altering evidence.', F, ['RG0'], None, ['RV-12'])]),
 'T-18': ('FAIL', [
    crit('Finalized package hash is identical before and after unrelated later intake.', P, ['RT18', 'RT12b']),
    crit('A source revision after finalization leaves the package unchanged and opens a visible exception.', P, ['RT18']),
    crit('A preparer cannot finalize.', P, ['RT18']),
    crit('Added: locking or finalizing is refused, or requires a recorded acknowledgement, while any governing item is stale, disputed or unreviewed (probe N10).', P, ['RN01', 'RT18', 'maintained N10']),
    crit('Added: no source key has a current governing artifact in more than one period.', P, ['RN02'], 'Holds for one key; the same charge under a superseding key is not covered.', ['RV-01']),
    crit('T-07 follow-up: a defined recovery path for a mistaken revoke; a bound on re-opening a resolved dispute.', P, ['RT18', 'maintained N15']),
    crit('Adversarial: change events against a finalized package are raised only for real changes.', F, ['RT12b'], None, ['RV-04']),
    crit('Adversarial: a period in which a source was removed can still be finalized.', F, ['RT12d'], None, ['RV-03'])]),
 'T-19': ('FAIL', [
    crit('FV-CL02 reports FIXED.', P, ['case FV-CL02']),
    crit('FV-CL04 passes as an executable case.', P, ['case FV-CL04']),
    crit('FV-CL01 still passes.', P, ['case FV-CL01']),
    crit('Adversarial: a label-only document cannot complete reconciliation or tie-out requirements.', F, ['RT19a'], 'Holds for typed requirements; the shipped checklist is untyped.', ['RV-06']),
    crit('Adversarial: in-flight preparation race; waiting does not adopt changed sources or policy.', P, ['RT19b']),
    crit('External and final-close holds remain.', P, ['RT19a'])]),
}
corr = {
 'C-01': ('FAIL', 'The re-dating scenario (N02) is fixed, including replay, a recurring run and release on reopen. The same result is reachable through supersession under a new key.', ['RN02', 'RN02b'], ['RV-01', 'RV-03', 'RV-04']),
 'C-02': ('PASS', 'All five decision types, dispositions and finalization refuse with 409 PERIOD_LOCKED; an audited reopen by a granted human is required; decisions are accepted afterwards.', ['RN01'], []),
 'C-03': ('PASS', 'Identical work by another enqueuer or mandate issuer reuses the artifact and keeps the rejection and the approval; contributors append outside the hash; a newly linked contributor loses review rights.', ['RN03'], []),
 'C-04': ('PASS', 'Every version supplier and every author and approver of chart, entity and book configuration stays barred; another item\'s receipt does not bar. One P2 residual for superseded rule versions.', ['RN04', 'RN05', 'RN05b'], ['RV-10']),
 'C-05': ('PASS', 'Marks are kept; unknown and colliding aliases are held; empty aliases refused.', ['RN06'], []),
 'C-06': ('PASS', 'Kind is mandatory; a service identity is refused for every human authority, including when grants are issued to it.', ['RN07'], []),
}
results = {
 'title': 'Fable re-verification results: C-01 to C-06 and Batch 2', 'authored': '2026-11-15', 'notice': NOTICE,
 'status_vocabulary': {'PASS': 'verified by execution unless the evidence says inspection', 'FAIL': 'a confirmed gap, with a defect id', 'NOTE': 'limitation needing a decision', 'NOT_RUN': 'not executed', 'DEFERRED': 'capability correctly unavailable'},
 'environment': {'python': '3.9.6', 'sqlite': '3.51.0', 'platform': 'macOS (Darwin, arm64 or x86_64 as reported in the output file)', 'network': 'not used', 'loopback': 'available',
                 'bundle_sha256': '312232b6a235115b6c163a3a222672b7d21847e8d5a77d19577bf286138f9ebc', 'manifest': '152 of 152 files match; none unlisted'},
 'decisions': {
   'historical_corrective_checkpoint': {'status': 'PASS', 'basis': 'Unmodified original script on the frozen archive: N01 to N07 OK and all other required probes OK; exit 0. Chronology is consistent with the archive contents and file times but cannot be proved from an archive.'},
   'current_C01_to_C06': {'status': 'FAIL', 'basis': 'C-02 to C-06 pass on current source. C-01 passes its stated scenario and fails its objective through supersession (RV-01).'},
   'batch_2': {'status': 'FAIL', 'basis': 'T-11, T-10, T-13, T-14, T-16 and T-17 meet their criteria. T-09, T-12, T-15, T-18 and T-19 each have a P1 defect.'},
   'G0_technical_criteria': {'status': 'FAIL', 'basis': 'Six P1 defects are open, so two of the six G0 criteria are not met. The month, isolation and reviewer-case criteria are met. Human G0 acceptance is a separate decision and should wait.'},
   'gates_G1_to_G4': 'closed; nothing in this review opens them'},
 'commands': [
   {'command': 'python3 scripts/verify_corrective_checkpoint.py', 'exit_code': int(exit_codes['01_corrective_checkpoint']), 'evidence': 'evidence/01_corrective_checkpoint.txt'},
   {'command': 'make test', 'exit_code': int(exit_codes['02_make_test']), 'result': '111 tests, 0 failures, 0 errors, 0 expected failures', 'evidence': 'evidence/02_make_test.txt'},
   {'command': 'make check', 'exit_code': int(exit_codes['03_make_check']), 'evidence': 'evidence/03_make_check.txt'},
   {'command': 'make batch2-gate', 'exit_code': int(exit_codes['04_make_batch2_gate']), 'evidence': 'evidence/04_make_batch2_gate.txt'},
   {'command': 'python3 review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate', 'exit_code': int(exit_codes['05_cases_batch2_gate']), 'evidence': 'evidence/05_cases_batch2_gate.txt'},
   {'command': 'python3 review/batch2_verification_probes.py .', 'exit_code': int(exit_codes['06_maintained_probes']), 'evidence': 'evidence/06_maintained_probes.txt'},
   {'command': 'python3 scripts/synthetic_month.py', 'exit_code': int(exit_codes['07_synthetic_month']), 'evidence': 'evidence/07_synthetic_month.txt'},
   {'command': 'PYTHONDONTWRITEBYTECODE=1 ' + PROBE_CMD, 'exit_code': int(open(os.path.join(ev, 'probe_exit.txt')).read().strip()), 'result': '35 probes: 21 OK, 11 WEAK, 3 NOTE', 'evidence': 'fable_reverification_output.txt section B; evidence/probe_stdout.txt'},
   {'command': 'python3 -I evidence/static_checks.py <root> <reviewer-originals> <original-bundle>', 'exit_code': 0, 'evidence': 'evidence/static_checks.txt'}],
 'developer_claims': [
   {'claim': '111 passing tests', 'status': 'PASS', 'reproduced': '111 run, all ok'},
   {'claim': 'all 41 original platform/HTTP methods retained', 'status': 'PASS', 'reproduced': '41 of 41 platform and HTTP names of the Batch 1 baseline present (32 and 9). Against the first 0.1.0 bundle: 40 of 40 platform and HTTP methods present, 14 bodies changed, none with fewer assertions'},
   {'claim': '60 cases: 29 PASS, 10 FIXED, 21 DEFERRED-OK', 'status': 'PASS', 'reproduced': cases['summary']},
   {'claim': 'changed-files.json and the patch represent the actual source', 'status': 'FAIL', 'reproduced': 'all 46 listed hashes correct; accounting_agent/web/app.js and index.html changed and are in neither (RV-16)'},
   {'claim': 'four verification inputs unchanged', 'status': 'PASS', 'reproduced': 'identical in the outer bundle, the frozen archive and the reviewer originals'},
   {'claim': 'teaching month: nine card and two journal approvals, two held with external referral, two packages, November locked, second client unaffected', 'status': 'PASS', 'reproduced': 'independently re-driven with explicit authority (probe RG0); entry impact equals hand calculation', 'caveat': 'TX-009 and J-002 are cleared by re-supplied inputs (RV-12)'}],
 'corrective_tickets': {k: {'status': v[0], 'summary': v[1], 'probes': v[2], 'open_defects': v[3]} for k, v in corr.items()},
 'original_probes_N01_to_N07': {n: {'frozen_checkpoint_unmodified_script': frozen.get(n), 'maintained_harness_current_source': maint.get(n),
                                  'carried_into_current_api': {p: V[p] for p in carried[n]}} for n in carried},
 'frozen_checkpoint_all_probes_raw': frozen,
 'maintained_harness_all_probes_raw': maint,
 'maintained_harness_judgment': {
   'status': 'accepted as an adaptation, not as sufficient evidence',
   'points': ['Setup changes (proposed-then-approved profile, explicit grants, structured statements, lock acknowledgement) keep the original assertions for N01 to N07; my independent versions with explicit setup agree.',
              'Every mandate probe uses create_fixture_mandate, which supplies an empty freshness predicate and the occurrence-calendar rule, so the harness never exercises the freshness control (RV-11).',
              'prepare_profile approves through a fixed second actor inside the helper. That is explicit but it means no maintained probe tests a withdrawn mapping, a superseded rule author or an untyped checklist.',
              'N16 and N18 remain NOTE. N18 is not evidence that alias normalisation is visible to an approver (RV-14).']},
 'validation_case_adaptations': [
   {'case': 'FV-C13', 'judgment': 'justified', 'reason': 'T-12 asked for the superseded pending row to leave the open population.'},
   {'case': 'FV-C17, FV-C18', 'judgment': 'justified', 'reason': 'T-17 asked for policy-unset codes; the items are still held.'},
   {'case': 'FV-J05, FV-J07', 'judgment': 'justified', 'reason': 'Period contracts stated in the case text; outcome remains no eligible entry.'},
   {'case': 'FV-CL04', 'judgment': 'justified', 'reason': 'Now executable; expects the missing-evidence blocker plus disclosure of the quarantined document.'},
   {'case': 'statement adapter (accounting_agent/fixtures/spec_adapter.py)', 'judgment': 'acceptable with a limit', 'reason': 'Used only by the runner and the fixture builder, never by intake. It preserves a wrong declared count or total as a wrong statement. It takes line ids from the intake population, so the 60 cases cannot detect a line-identity defect; probes RT13 and RT13n cover that.'}],
 'independent_probes': probes,
 'batch_2_tickets': {k: {'status': v[0], 'criteria': v[1]} for k, v in tickets.items()},
 'validation_cases': [{'id': c['id'], 'stage': c['stage'], 'raw_runner_status': c['status'],
                       'status': {'PASS': 'PASS', 'FIXED': 'PASS', 'DEFERRED-OK': 'DEFERRED'}.get(c['status'], 'FAIL'), 'detail': c.get('detail', '')} for c in cases['cases']],
 'validation_case_summary': cases['summary'],
 'full_month_and_isolation': [
   crit('Every teaching item approved or dispositioned, with service operations only and no database edit.', P, ['RG0', 'scripts/synthetic_month.py'], 'Eleven approved; TX-007 and TX-011 referred and still held; TX-008 quarantined in unconfigured October and named in the package.'),
   crit('No weakened blocker.', P, ['RG0'], 'No blocker was weakened. TX-009 was cleared by replacing its receipt and J-002 by correcting the journal; the first is defect RV-12.'),
   crit('Packages finalized by an independent granted human with acknowledgement; period locked.', P, ['RG0']),
   crit('Proposed-entry impact recomputed independently.', P, ['RG0'], 'Office supplies +391.00, repairs +200.00, card liability -291.00, cash -300.00; net zero.'),
   crit('Second client in December on the same engine with no effect on the first.', P, ['RG0'], 'Artifacts, package bytes and evidence history unchanged; cross-client review and intake refused; both audit chains verify.')],
 'G0_criteria': [
   crit('Batch 1 and Batch 2 complete.', F, ['batch_2_tickets'], 'Five Batch 2 tickets have a P1 defect.'),
   crit('All P0 and P1 current defects fixed with tests.', F, ['FABLE_REVERIFICATION_CORRECTIONS.json'], 'RV-01 to RV-06 open.'),
   crit('Reviewer cases: zero unexpected, all fail-until-fix cases fixed.', P, ['validation_cases']),
   crit('A full synthetic month reaches approved-or-dispositioned, finalized and locked with no database edits and no weakened blocker.', P, ['RG0'], 'With the RV-12 caveat.'),
   crit('Two synthetic clients in different periods on one engine with no cross-effects.', P, ['RG0']),
   crit('Documentation matches code.', F, ['static checks', 'RT19a'], 'Change inventory omits two files (RV-16); close-readiness documents describe typed requirements while the shipped checklist is untyped (RV-06).')],
 'not_run': [{'item': 'Browser walkthrough of the demo UI', 'reason': 'No accounting control depends on it. HTTP boundaries were executed through the delivered tests and inspected.'},
             {'item': 'Unverified concerns UC-1 to UC-5', 'reason': 'Found by reading; listed separately and not counted as defects.'}],
}
assert len(results['validation_cases']) == 60
json.dump(results, open(os.path.join(out_dir, 'FABLE_REVERIFICATION_RESULTS.json'), 'w'), indent=1, ensure_ascii=False)
print('defects', corrections['priority_counts'], '| probes', len(probes), '| cases', len(results['validation_cases']), cases['summary'])
print('probe fails:', [p['id'] for p in probes if p['status'] == 'FAIL'], '| notes:', [p['id'] for p in probes if p['status'] == 'NOTE'])
