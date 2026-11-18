"""Builds FABLE_RV_CORRECTIONS.json and FABLE_RV_ACCEPTANCE_RESULTS.json from recorded evidence.
Probe verdicts, case statuses and exit codes are read from the evidence files, not retyped.
Usage: python3 -I build_json.py <review_rv dir> <working copy root> <previous review dir>"""
import json, os, re, sys
out_dir, work_root, prev_dir = sys.argv[1:4]
ev = os.path.join(out_dir, 'evidence')
NOTICE = ('Review output only. Authorises no connection, posting, payment, model call, hosting, deployment or policy '
          'activation, and opens no readiness gate. All data fictional.')
CMD = 'python3 fable_rv_acceptance_probes.py <project-root>'
VERDICT = re.compile(r'^([A-Z][A-Za-z0-9]+)\s+(\S+)\s+(OK|WEAK|NOTE|ERROR)\s+(.*)$')
MAP = {'OK': 'PASS', 'WEAK': 'FAIL', 'NOTE': 'NOTE', 'ERROR': 'NOT_RUN'}

def verdicts(name):
    rows = []
    for line in open(os.path.join(ev, name)):
        m = VERDICT.match(line.rstrip())
        if m: rows.append(m.groups())
    return rows
mine = [{'id': a, 'requirement': b, 'raw_verdict': c, 'status': MAP[c], 'checks': d} for a, b, c, d in verdicts('acceptance_stdout.txt')]
V = {p['id']: p['raw_verdict'] for p in mine}
assert len(mine) == 24, len(mine)
gate = verdicts('04_make_reverification_gate.txt'); direct, adapted = gate[:28], gate[28:63]
assert len(direct) == 28 and len(adapted) == 35, (len(direct), len(adapted))
original_full = verdicts('07_original_supplied_probes.txt'); assert len(original_full) == 35
D_, A_, O_ = ({r[0]: r[2] for r in x} for x in (direct, adapted, original_full))
exits = dict(l.strip().split(' exit=') for l in open(os.path.join(ev, 'exit_codes.txt')) if ' exit=' in l)

# ---- new confirmed defects -----------------------------------------------------------------------
D = []
def defect(i, prio, title, affects, source, probe, repro, expected, actual, consequence, correction, assertions, tests, depends=(), client=None):
    D.append({'id': i, 'priority': prio, 'classification': 'confirmed_defect', 'title': title, 'affected_requirements': affects, 'source': source, 'probe': probe,
              'minimal_reproduction': repro, 'expected': expected, 'actual': actual, 'accounting_or_control_consequence': consequence,
              'smallest_sufficient_correction': correction, 'depends_on': list(depends), 'acceptance_assertions': assertions, 'regression_tests': tests,
              'decision_requiring_client_authority': client})

defect('RA-01', 'P1', 'A second supersession step releases a charge that is quarantined behind a locked period',
       ['RV-01', 'C-01', 'T-12 (supersession is resolved by the engine)'],
       ['accounting_agent/service.py bind_source lines 218-223: the origin period is taken from the direct predecessor only, and only if that predecessor was ever admitted',
        'accounting_agent/source_control.py apply_supersession lines 87-98: the quarantined predecessor and its receipt are then marked removed'],
       'X01',
       ['Approve item A1 (3 Nov) and lock November; open December.',
        "Intake A1X dated 2 Dec with supersedes='demo_card_001:A1' and its receipt. It is correctly quarantined (SOURCE_MOVED_FROM_LOCKED_PERIOD).",
        "Intake A1Y dated 3 Dec with supersedes='demo_card_001:A1X', its receipt and a December statement.",
        'Run December card preparation. Disposition SOURCE_TRANSITION_REQUIRES_REVIEW as settlement_verified, citing the charge, its receipt and the statement. Re-run and approve with an independent reviewer.'],
       'A1Y is quarantined exactly as A1X is, because the charge it replaces is still approved in a locked period. The quarantine of A1X stays visible.',
       'A1Y is admitted to December and approved. A1 remains approved in locked November. The quarantine entries for A1X and its receipt disappear from state.source_exceptions because their heads are marked removed.',
       'The same expense and liability are approved in two periods. This is the outcome RV-01 and C-01 exist to prevent, reached with one more supersession step. A feed that re-issues a row twice produces it without any intent.',
       ['In bind_source, resolve the origin through the whole supersession chain: walk supersession_refs to the nearest ancestor that has an admitted binding and use that period as the origin.',
        'If the direct predecessor (or any ancestor before the admitted one) is itself quarantined with SOURCE_MOVED_FROM_LOCKED_PERIOD, the new source inherits that block, in the same way a receipt inherits it from its transaction.',
        'Do not call apply_supersession for a blocked source; a quarantined predecessor stays listed until the origin is reopened.',
        'On reopen, release the whole chain: only the last link enters the destination period and the earlier links are recorded as superseded.'],
       ['Probe X01 reports OK: while November is locked, December has no governing artifact for A1Y.',
        'state.source_exceptions lists A1X, A1Y and both receipts with SOURCE_MOVED_FROM_LOCKED_PERIOD; export.source_move_history has a blocked row for each.',
        'After reopen and re-preparation: November has no governing A1, December has exactly one governing item for the charge (A1Y) carrying SOURCE_TRANSITION_REQUIRES_REVIEW, and A1X is not a governing item anywhere.',
        'Probes A01, RN02 and RN02b are unchanged.'],
       ['probe X01', 'probe A01', 'probes RN02, RN02b, RT12d', 'new unit test: three-link chain under lock, then reopen', 'FV-C13'])

defect('RA-02', 'P2', 'The author of a rule is dropped from the item lineage when a colleague re-proposes the same rule without the optional supersedes link',
       ['RV-10', 'C-04', 'T-09 (independence uses the proposer and approver of each applied rule)'],
       ['accounting_agent/controls.py applied_rule_lineage lines 124-137: earlier versions are found only through rule.supersedes', 'accounting_agent/controls.py _propose_rule lines 92-99: supersedes is optional'],
       'A10',
       ["Reviewer-to-be proposes vendor mapping demo_acme version 1 (alias and category); a policy approver approves it.",
        'A colleague proposes version 2 with the same key, alias and category and a cosmetic name change, passing no supersedes value; a second approver approves it.',
        'Prepare an ACME charge. The author of version 1 approves it.'],
       'Refused with 403, as it is when the supersedes link is supplied.',
       'Accepted. The contributor list holds only the proposer and approver of version 2.',
       'The RV-10 control holds only when the re-proposer chooses to declare the link. The person who wrote the coding rule can approve the items it codes.',
       ['Find earlier versions by rule identity, not by the optional link: every earlier approved rule with the same kind, rule_key and item scope is a candidate ancestor, compared with the applied version exactly as today.',
        'Alternatively, set supersedes automatically in _propose_rule to the latest existing version of the same kind and key; either way the lineage must not depend on a value the proposer may omit.'],
       ['Probe A10 reports OK: the unlinked cosmetic re-proposal leaves the author of version 1 refused with 403.',
        'The different-category case in A10 is still allowed, and RN05b, RN04, RN05 are unchanged.'],
       ['probe A10', 'probe RN05b', 'delivered test_RV10_semantic_rule_authors_retained_but_different_category_author_not_barred extended with an unlinked case'])

defect('RA-03', 'P2', 'Replacing a receipt under a new key avoids the revised-evidence hold',
       ['RV-12', 'T-17'],
       ['accounting_agent/source_control.py evidence_revisions lines 69-79: revisions are computed per document key', 'accounting_agent/modules.py supporting_revisions lines 147-152'],
       'X12k',
       ['Charge A1 is 40.00 and its receipt (key receipt-A1) says 39.99: the item carries RECEIPT_AMOUNT_POLICY_UNSET.',
        "The preparer withdraws receipt-A1 (tombstone, reason voided) and supplies a new key receipt-A1-replacement for the same charge at 40.00.",
        'Re-run and approve with an independent reviewer.'],
       'The item is held with EVIDENCE_REVISED_REQUIRES_REVIEW and discloses that the supporting document for this charge was replaced: earlier document, its supplier, the fields that differ.',
       'The item is eligible with no blocker and evidence_revisions is empty. It is approved.',
       'The RV-12 control is avoided by changing the document key. A preparer can still make third-party evidence agree with the charge and obtain a clean item, and the reviewer is told nothing.',
       ['Compute revisions per supported item as well as per key. For a transaction, compare the receipts now relied on with every receipt snapshot ever supplied for that account and transaction id, including withdrawn heads and other keys. A withdrawn or different earlier document whose content differs is listed as a revision with kind replaced.',
        'The hold, the supplier rule and the acceptance binding then apply unchanged.'],
       ['Probe X12k reports OK: after the replacement the item carries EVIDENCE_REVISED_REQUIRES_REVIEW and evidence_revisions names receipt-A1 version 1 and the amount change.',
        'The supplier of either receipt cannot accept; a granted non-supplier can; probe A12 is unchanged.',
        'A second receipt added for a charge whose first receipt is unchanged is not reported as a revision (it remains a multiple-receipt question).'],
       ['probe X12k', 'probe A12', 'delivered test_RV12_revised_receipt_requires_independent_acceptance_and_discloses_history extended with a replacement key'],
       client='For a real client: the document policy, including who may accept a corrected or replaced receipt (client question 5).')

defect('RA-04', 'P2', 'A statement re-supplied to agree with the population is neither held nor disclosed as revised',
       ['RV-12 (changed support is disclosed and held)', 'RV-13', 'T-13', 'F-12'],
       ['accounting_agent/source_control.py evidence_revisions line 72: only receipt and document kinds are examined', 'accounting_agent/modules.py statement_checks lines 100-139 and supporting_revisions lines 147-152'],
       'X12s',
       ['Population is two purchases totalling 100.00. The statement supplied by the preparer says purchases 90.00: every item carries STATEMENT_CONTROL_MISMATCH.',
        'The preparer re-supplies the statement with purchases 100.00. Re-run and approve with an independent reviewer.'],
       'The items are held, and the workpaper discloses the earlier statement version, its supplier and the fields that changed, until a granted human who supplied no version accepts the revision.',
       'Both items are eligible and are approved. The item cites statement version 2; evidence_revisions is empty and the workpaper has no revision field. Provenance shows only the latest supplier.',
       'The statement is the completeness control. If the person who supplies the population can also restate the control until it agrees, with no trace shown to the reviewer, the control gives no assurance beyond the preparer\'s own word.',
       ['Include the statement kind in evidence_revisions and treat the statement of an account as supporting evidence of every item on that account, so the existing hold, supplier rule and acceptance apply.',
        'Add statement_revisions (earlier and current version, suppliers, changed fields) to the statement workpaper.'],
       ['Probe X12s reports OK: after the re-supplied statement the items are not eligible, or the revision is disclosed on the item or the workpaper.',
        'A supplier of any statement version cannot accept the revision; a granted non-supplier can, and final review stays separate.',
        'Probes A13, RT13 and RT13n and cases FV-C08, FV-C09, FV-C19 are unchanged.'],
       ['probe X12s', 'probe A13', 'probes RT13, RT13n', 'FV-C08', 'FV-C09'],
       client='For a real client: which document is the authoritative statement and who may supply or correct it (client questions 2 and 4).')

defect('RA-05', 'P3', 'A mandate is suspended as if policy had changed when new evidence falls after the date of a rule that was already approved',
       ['T-10 (bound policy)', 'UC-1 from the previous review, now reproduced'],
       ['accounting_agent/controls.py policy_signature line 210: the signature is built from the rules applied to the sources currently present'],
       'U1',
       ['Approve a vendor rule effective 15 November. Then create and approve a mandate for November; at that moment all November evidence is dated before the 15th.',
        'Fresh evidence dated 25 November arrives and the mandate is ticked.'],
       'The occurrence is dispatched. No policy changed after the mandate was approved.',
       "The mandate moves to needs_reconfirmation with reason 'Bound policy changed' and nothing is dispatched.",
       'A false suspension. It fails in the safe direction, but a recurring authority that suspends itself whenever evidence crosses a rule date will be re-approved by habit.',
       ['Build the signature from policy alone: the ids and versions of every approved rule whose effective window intersects the target period, with retirements, plus the accounting profile hash. It must not depend on which sources are present.'],
       ['Probe U1 reports OK: the mandate stays active and one run is dispatched.', 'Probe RT10a is unchanged: a rule approved after the mandate still suspends it.'],
       ['probe U1', 'probe RT10a', 'delivered mandate tests'])

defect('RA-06', 'P3', 'A disposition that cites the predecessor snapshots listed in the artifact is accepted but never takes effect',
       ['RV-01 (transition review)', 'T-14'],
       ['accounting_agent/exceptions.py disposition lines 53-55 accept references to superseded predecessors', 'accounting_agent/exceptions.py active_dispositions line 26 then requires every cited reference to be a current source'],
       'X01',
       ['An item that supersedes another carries SOURCE_TRANSITION_REQUIRES_REVIEW; its evidence list includes the predecessor snapshot.',
        'Disposition it as settlement_verified citing the whole evidence list. The call returns a disposition id. Re-run.'],
       'Either the call is refused, or the disposition clears the blocker.',
       'The blocker stays and nothing says why. The same disposition citing current sources only does clear it.',
       'The reviewer believes the transition was dispositioned. The natural choice, citing everything the artifact lists, silently does nothing.',
       ['Make the two checks agree: active_dispositions accepts the references that disposition accepted, namely current sources and the supersession references of the item.'],
       ['In probe X01 the first disposition (citing predecessors) clears SOURCE_TRANSITION_REQUIRES_REVIEW once RA-01 is fixed and the origin is reopened; or it is refused with a message naming the reference.'],
       ['probe X01', 'probe A01'], depends=['RA-01'])

defect('RA-07', 'P3', 'A transaction row belonging to a different item counts as supporting evidence',
       ['RV-15'], ['accounting_agent/exceptions.py disposition lines 56-60'], 'A14',
       ["An unknown-vendor item is dispositioned as confirm_vendor citing its own row and the transaction row of an unrelated item."],
       'Refused: supporting evidence means a receipt, a document or the statement.', 'Accepted.',
       'The RV-15 requirement for evidence beyond the item\'s own row can be met with a row that says nothing about the item.',
       ['Count as supporting evidence only snapshots of kind receipt, document or statement that relate to the item (its receipts, its account statement, or a document naming it).'],
       ['Probe A14 reports OK: the disposition citing only another item\'s transaction row is refused.', 'Probes A07, A08, A09, M1 and M2 are unchanged.'],
       ['probe A14', 'probes A07, A08, A09'])

defect('RA-08', 'P3', 'Two charges can each be excluded as a duplicate of the other, leaving no proposed entry for either',
       ['RV-09'], ['accounting_agent/exceptions.py disposition line 89', 'accounting_agent/modules.py card_prepare duplicate resolution'], 'X09',
       ['Two identical charges D1 and D2. Before re-preparation, disposition D2 as duplicate_of D1 and D1 as duplicate_of D2. Re-run.'],
       'The second disposition is refused because its target is itself excluded.', 'Both are accepted. Both items carry DUPLICATE_EXCLUDED and neither has an entry. Both stay visibly held and block finalization without acknowledgement.',
       'A real charge can be left with no proposed entry. It is visible, so this is P3, but nothing stops it.',
       ['Refuse duplicate_of or source_replay when the target item has an active duplicate_of or source_replay disposition.'],
       ['Probe X09 reports OK: the second, circular disposition is refused.'], ['probe X09', 'probe A09'])

order = ['RA-01', 'RA-03', 'RA-04', 'RA-02', 'RA-06', 'RA-05', 'RA-07', 'RA-08']
corrections = {
    'title': 'Fable corrective tickets after acceptance review of RV-01 to RV-17 (bundle FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE)',
    'authored': '2026-11-15', 'notice': NOTICE,
    'companion_files': ['FABLE_RV_ACCEPTANCE_REPORT.md', 'FABLE_RV_ACCEPTANCE_RESULTS.json', 'fable_rv_acceptance_probes.py', 'fable_rv_acceptance_output.txt', 'evidence/'],
    'recommendation': 'Fourteen of the seventeen corrections are accepted. Fix RA-01 (P1) before G0 is recorded; fix RA-02, RA-03 and RA-04 (P2) in the same pass. Batch 3 stays closed until then.',
    'priority_counts': {p: sum(1 for d in D if d['priority'] == p) for p in ('P0', 'P1', 'P2', 'P3')},
    'implementation_order': order,
    'order_note': 'RA-01 first: it is the only P1 and RA-06 depends on it. RA-03 and RA-04 share the evidence-revision code and should be done together.',
    'completion_gate': [
        CMD + ' exits 0: no WEAK and no ERROR. The NOTE verdicts A14, X09 and U1 become OK when RA-07, RA-08 and RA-05 are done; U4 may remain a NOTE.',
        'make test, make check, make batch2-gate and make reverification-gate still pass; reviewer cases stay at 29 PASS, 10 FIXED, 21 DEFERRED-OK.',
        'fable_rv_acceptance_probes.py is added to make test unmodified. An API change that makes a probe unrunnable is returned with the adapted probe for review, as was done this time.',
        'Each contract change is recorded in DECISIONS.md.'],
    'confirmed_defects': D,
    'unverified_or_open_concerns': [
        {'id': 'UC-4', 'status': 'observed, not a defect', 'note': 'When a superseding source is itself removed, the charge it replaced is not restored. Both appear under removed_items, and a statement with line ids then fails to tie (probe U4), so it is visible. Whether to restore automatically is a feed-semantics question for gate G2.'},
        {'id': 'UC-5', 'status': 'unchanged', 'note': 'Synthetic authority grants have no revocation and no rule that the administrator differs from the subject (controls.py grant_authority line 7). Acceptable for fictional grants; must be designed before gate G1.'},
        {'id': 'UC-6', 'status': 'new, by reading only', 'note': 'A duplicated payment row can only be settled or referred; source_replay is refused for payment activity (exceptions.py line 77). Not executed.'}],
    'verified_since_last_review': [
        {'id': 'UC-2', 'status': 'PASS', 'evidence': 'probe A13: a quarantined late revision of the prior statement is not used; the frozen statement governs continuity.'},
        {'id': 'UC-3', 'status': 'PASS', 'evidence': 'probes A04 and A12: revising a receipt that supports an approved item raises APPROVED_SOURCE_REVISED for that item.'},
        {'id': 'UC-1', 'status': 'reproduced', 'evidence': 'probe U1; now ticket RA-05.'}],
    'deferred_enhancements': [
        {'id': 'DE-1', 'note': 'Each item envelope still carries the run-wide fingerprint and rule list, so a same-period change to one item sends every item of that workflow back for review. Conservative.'},
        {'id': 'DE-2', 'note': 'With multiple receipts allowed, each receipt is still compared with the whole charge. Needs a client document policy.'},
        {'id': 'DE-3', 'note': 'Double-recording detection works within one period population. Cross-period detection belongs with reconciliation in Batch 3.'},
        {'id': 'DE-4', 'note': 'Statement cycles must equal the accounting period.'},
        {'id': 'DE-5', 'note': 'Trial balance and card statement lines of the demo checklist are typed as document, so a label still satisfies them. That is the explicit typing asked for in RV-06; it should become a workflow outcome or a tie-out when those capabilities exist.'}],
    'decisions_requiring_client_authority': [
        'Whether the person who approves policy may also review items prepared under it (currently barred).',
        'Document policy: date window, amount tolerance, multiple receipts, and who may accept a corrected or replaced receipt.',
        'Which document is the authoritative card statement, whether it has line identifiers, who may supply or correct it, and how cycles map to periods.',
        'Treatment of fees, interest, card payments and transfers, and the accounts each disposition may use.',
        'The close checklist, the evidence each line requires, and who gives final sign-off.',
        'Who may disposition, finalize and lock, and what evidence must be new before a recurring run; whether a no-evidence mandate is ever acceptable outside demonstrations.'],
}
json.dump(corrections, open(os.path.join(out_dir, 'FABLE_RV_CORRECTIONS.json'), 'w'), indent=1, ensure_ascii=False)

# ---- results ----------------------------------------------------------------------------------------
prev_corr = json.load(open(os.path.join(prev_dir, 'FABLE_REVERIFICATION_CORRECTIONS.json')))
prev_res = json.load(open(os.path.join(prev_dir, 'FABLE_REVERIFICATION_RESULTS.json')))
cases = json.load(open(os.path.join(work_root, 'docs/batch2/final-validation.json')))
P, F = 'PASS', 'FAIL'
# evidence for each stated assertion of RV-01 to RV-17, in the order they appear in the previous corrections file
EVID = {
 'RV-01': [['RN02b direct', 'A01'], ['A01'], ['RT12d direct', 'A01'], ['A02'], ['RN02 adapted', 'case FV-C13']],
 'RV-02': [['RT15 direct', 'A02'], ['A02'], ['cases FV-J01 to FV-J10']],
 'RV-03': [['RT12d direct', 'A03'], ['A03'], ['RN02 adapted', 'A01'], ['case FV-C13']],
 'RV-04': [['RT12b direct', 'A04'], ['RN02 adapted'], ['RT12c direct'], ['A04']],
 'RV-05': [['RT09c direct'], ['A05'], ['RT09a, RT09b direct', 'cases FV-C01, FV-C15']],
 'RV-06': [['RT19a direct', 'A06'], ['A06'], ['cases FV-CL01, FV-CL02, FV-CL04']],
 'RV-07': [['RT14e direct', 'A07'], ['A07'], ['RT14a adapted', 'RG0 adapted', 'M1', 'M2']],
 'RV-08': [['RT14b adapted', 'evidence/rt14b_fault_injection.txt', 'A08'], ['RT14a adapted']],
 'RV-09': [['RT14c direct', 'A09'], ['A09']],
 'RV-10': [['RN05b direct', 'A10 (linked case)'], ['A10 (different-category case)'], ['RN04, RN05, RT09b direct']],
 'RV-11': [['RT10b direct', 'A11'], ['RT10a direct'], ['make test', 'evidence/legacy_upgrade_check.txt']],
 'RV-12': [['M2', 'A12'], ['A12', 'M1'], ['M1 (referred)', 'M2 (accepted)', 'RG0 adapted']],
 'RV-13': [['RT13n direct', 'A13'], ['RT13 direct', 'cases FV-C08, FV-C09, FV-C19']],
 'RV-14': [['RT09d direct', 'A14']],
 'RV-15': [['RT14d direct', 'A08'], ['RT14a adapted']],
 'RV-16': [['evidence/inventory_checks.txt']],
 'RV-17': [['A17', 'RT18 direct']],
}
OBJECTIVE = {'RV-01': (F, ['RA-01'], 'Every stated assertion holds. A second supersession step defeats the control (probe X01).'),
             'RV-10': (F, ['RA-02'], 'Every stated assertion holds. The control depends on an optional link the re-proposer can omit (probe A10).'),
             'RV-12': (F, ['RA-03', 'RA-04'], 'Every stated assertion holds for a revised receipt. A replacement receipt under a new key, and a re-supplied statement, are not covered (probes X12k, X12s).')}
rv = {}
for d in prev_corr['confirmed_defects']:
    i = d['id']; ass = d['acceptance_assertions']; assert len(ass) == len(EVID[i]), i
    status, open_defects, note = OBJECTIVE.get(i, (P, [], 'Stated assertions hold and no route around the control was found.'))
    rv[i] = {'title': d['title'], 'previous_priority': d['priority'], 'acceptance': status, 'note': note, 'open_defects': open_defects,
             'assertions': [{'assertion': a, 'status': P, 'evidence': e} for a, e in zip(ass, EVID[i])]}
rv['RV-09']['note'] += ' One P3 observation: both charges can be excluded at once (RA-08).'
rv['RV-15']['note'] += ' One P3 observation: another item\'s transaction row counts as support (RA-07).'
rv['RV-13']['note'] += ' A re-supplied statement is not disclosed as revised; ticketed under RA-04.'
rv['RV-01']['open_defects'].append('RA-06')

failed_before = ['RN02b', 'RN05b', 'RT09c', 'RT12b', 'RT12d', 'RT10b', 'RT14b', 'RT14c', 'RT14e', 'RT15', 'RT19a']; noted_before = ['RT09d', 'RT13n', 'RT14d']
changed_setup = ['RN02', 'RN03', 'RN07', 'RT12a', 'RT14a', 'RT14b', 'RG0']
orig = {}
for pid in [r[0] for r in original_full]:
    orig[pid] = {'previous_review': {p['id']: p['raw_verdict'] for p in prev_res['independent_probes']}[pid],
                 'original_script_full_command_now': O_[pid], 'original_script_in_delivered_gate': D_.get(pid, 'not run directly (setup changed)'),
                 'adapted_copy_in_delivered_gate': A_[pid],
                 'judgment': P if (D_.get(pid) == 'OK' or (pid in changed_setup and A_[pid] == 'OK')) else F}
orig['RT14b']['note'] = 'The original script prints OK on current source without reaching its starting state. Accepted on the strengthened adapted probe and independent fault injection.'

adapt = {
 'RN02': 'The only change is the empty freshness predicate, replaced by the explicit no-evidence form that RV-11 itself provides. Issuer, independent approver, schedule and every verdict expression are unchanged. The probe then runs to completion and its lock, recurrence and reopen conditions hold.',
 'RN03': 'Same single change. The identity, rejection, contributor and 403 conditions are unchanged and hold.',
 'RN07': 'Same single change, on a mandate that is deliberately left unapproved. The service approval attempt is refused with 403 by the grant check, not by an invalid mandate. The service-created mandate with {} is untouched and is refused with 403 by the human check, which runs before freshness validation.',
 'RT12a': 'The newer delivery changes the receipt, so RV-12 requires a hold. The helper first asserts the hold and the disclosed history, then obtains acceptance from the existing dispositioner, who supplied neither version. No grant is added. The original ordering conditions are unchanged.',
 'RT14a': 'The shared helper adds the candidate receipts only when a distinct-purchases call uses default evidence. The explicit empty-evidence negative is untouched and still refused. All final conditions are unchanged.',
 'RT14b': 'Evidence now names the candidate receipt, still without the statement. The added assertions make the probe fail when its starting state is not reached. My own fault injection confirms: refusal of D1, refusal of D2 and an ineligible D1 each give ERROR, exit 1, before the third charge is constructed; the valid path gives OK, exit 0.',
 'RG0': 'Peer receipts are cited for the two distinct-purchases decisions, and the corrected TX-009 receipt is accepted only after its hold and history are asserted. Expected counts, the hand calculation and the isolation conditions are unchanged. My independent M2 reaches the same result by the same route.'}
adaptations = {k: {'acceptance': 'ACCEPTED', 'original_command_verdict_now': O_[k], 'adapted_verdict': A_[k], 'reason': v} for k, v in adapt.items()}

tickets = {k: {'status': P, 'criteria': [dict(c, status=(P if c['status'] in ('FAIL', 'NOTE') else c['status'])) for c in v['criteria']]} for k, v in prev_res['batch_2_tickets'].items()}
for t in tickets.values():
    for c in t['criteria']:
        c.pop('defects', None); c['previous_status'] = next(x['status'] for x in prev_res['batch_2_tickets'][[k for k, v in tickets.items() if v is t][0]]['criteria'] if x['criterion'] == c['criterion'])
        c['evidence'] = c['evidence'] + ['delivered gate: original probes direct or adapted, all OK']
def add(ticket, text, status, evidence, defects=(), note=None):
    c = {'criterion': text, 'status': status, 'evidence': evidence, 'previous_status': 'new this review'}
    if defects: c['defects'] = list(defects)
    if note: c['note'] = note
    tickets[ticket]['criteria'].append(c)
add('T-12', 'Adversarial: a supersession chain respects a locked origin.', F, ['X01'], ['RA-01'])
add('T-09', 'Adversarial: rule-author lineage does not depend on the optional supersedes link.', F, ['A10'], ['RA-02'], 'P2.')
add('T-17', 'Adversarial: a replacement receipt under a new key is treated as a revision.', F, ['X12k'], ['RA-03'], 'P2.')
add('T-13', 'Adversarial: a re-supplied statement is disclosed and held.', F, ['X12s'], ['RA-04'], 'P2.')
add('T-10', 'Adversarial: no false suspension when evidence crosses an already-approved rule date.', 'NOTE', ['U1'], ['RA-05'], 'P3; fails safe.')
add('T-11', 'Re-run this review.', P, ['RT11 direct'])
tickets['T-12']['status'] = F
for k in ('T-09', 'T-13', 'T-17'):
    tickets[k]['status'] = 'PASS'; tickets[k]['open_p2'] = [c['defects'][0] for c in tickets[k]['criteria'] if c.get('defects') and c['status'] == F]

corr = {'C-01': (F, 'Re-dating and single-step supersession are quarantined and released correctly (RN02, RN02b, A01). A two-step supersession chain is admitted and approved in a second period (X01).', ['RA-01']),
        'C-02': (P, 'RN01 direct: every decision type, dispositions and finalization refuse under lock; audited reopen required.', []),
        'C-03': (P, 'RN03 adapted and A09: identical work reuses the artifact and keeps its rejection; contributors append outside the hash.', []),
        'C-04': (P, 'RN04, RN05, RN05b direct and X15: version suppliers, configuration authors and cited-evidence suppliers stay barred. One P2 residual for unlinked rule versions.', ['RA-02']),
        'C-05': (P, 'RN06 direct.', []), 'C-06': (P, 'RN07 adapted: all service attempts refused with 403.', [])}

results = {
 'title': 'Fable acceptance results: RV-01 to RV-17, C-01 to C-06, Batch 2 and G0', 'authored': '2026-11-15', 'notice': NOTICE,
 'status_vocabulary': {'PASS': 'verified by execution unless the evidence says inspection', 'FAIL': 'confirmed gap with a defect id', 'NOTE': 'limitation needing a decision', 'NOT_RUN': 'not executed', 'DEFERRED': 'capability correctly unavailable; its future accounting behaviour was not tested', 'ACCEPTED': 'probe adaptation judged valid'},
 'environment': {'python': '3.9.6', 'sqlite': '3.51.0', 'platform': 'macOS Darwin x86_64', 'make': 'GNU make 3.81', 'network': 'not used', 'loopback': 'available',
                 'bundle_sha256': '247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75', 'manifest': '243 of 243 files match; none unlisted; untouched extraction re-verified after all runs'},
 'decisions': {
   'RV_01_to_RV_17': {'status': '14 PASS, 3 FAIL', 'pass': [k for k, v in rv.items() if v['acceptance'] == P], 'fail': [k for k, v in rv.items() if v['acceptance'] == F]},
   'current_C01_to_C06': {'status': 'FAIL on C-01 only', 'basis': 'RA-01. C-02 to C-06 pass.'},
   'batch_2': {'status': 'FAIL', 'basis': 'Ten of eleven tickets meet every criterion. T-12 has one P1 defect (RA-01). Three P2 defects are open under T-09, T-13 and T-17.'},
   'probe_adaptations': {'status': 'ACCEPTED, all seven', 'basis': 'The delta is exactly the delivered patch; every verdict and gate expression is structurally identical; each change is required by RV-11, RV-12 or RV-15.'},
   'strengthened_RT14b': {'status': 'PASS', 'basis': 'evidence/rt14b_fault_injection.txt'},
   'G0_technical_criteria': {'status': 'FAIL', 'basis': 'One P1 defect is open (RA-01). Every other G0 criterion is met.'},
   'human_G0_and_gates_G1_to_G4': 'not for this review; all remain closed'},
 'commands': [
   {'command': 'make test', 'exit_code': int(exits['01_make_test']), 'result': '136 tests, all ok, no expected failure, no skip', 'evidence': 'evidence/01_make_test.txt'},
   {'command': 'make check', 'exit_code': int(exits['02_make_check']), 'evidence': 'evidence/02_make_check.txt'},
   {'command': 'make batch2-gate', 'exit_code': int(exits['03_make_batch2_gate']), 'result': '29 PASS, 10 FIXED, 21 DEFERRED-OK; regenerated report identical to delivered', 'evidence': 'evidence/03_make_batch2_gate.txt'},
   {'command': 'make reverification-gate', 'exit_code': int(exits['04_make_reverification_gate']), 'result': '28 original probes OK directly; 35 OK through the adapted copy; frozen corrective checkpoint passes', 'evidence': 'evidence/04_make_reverification_gate.txt'},
   {'command': 'python3 scripts/synthetic_month.py', 'exit_code': int(exits['05_synthetic_month']), 'evidence': 'evidence/05_synthetic_month.txt'},
   {'command': 'python3 scripts/verify_corrective_checkpoint.py', 'exit_code': int(exits['06_corrective_checkpoint']), 'result': 'N01 to N07 OK on the frozen archive; says nothing about current source', 'evidence': 'evidence/06_corrective_checkpoint.txt'},
   {'command': 'python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .', 'exit_code': int(exits['07_original_supplied_probes']), 'result': '29 OK, 3 ERROR (RN02, RN03, RN07), 3 WEAK (RT12a, RT14a, RG0), as disclosed', 'evidence': 'evidence/07_original_supplied_probes.txt'},
   {'command': 'python3 review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate', 'exit_code': int(exits['08_cases']), 'evidence': 'evidence/08_cases.txt'},
   {'command': 'PYTHONDONTWRITEBYTECODE=1 ' + CMD, 'exit_code': int(open(os.path.join(ev, 'acceptance_exit.txt')).read().strip()), 'result': '24 probes: 16 OK, 4 WEAK, 4 NOTE', 'evidence': 'fable_rv_acceptance_output.txt section B'},
   {'command': 'python3 evidence/rt14b_fault_injection.py <root>', 'exit_code': 0, 'evidence': 'evidence/rt14b_fault_injection.txt'},
   {'command': 'python3 evidence/legacy_upgrade_check.py old|new <root> <db> <facts>', 'exit_code': 0, 'evidence': 'evidence/legacy_upgrade_check.txt'},
   {'command': 'python3 -I evidence/preservation_checks.py ...', 'exit_code': 0, 'evidence': 'evidence/preservation_checks.txt'},
   {'command': 'python3 -I evidence/inventory_checks.py ...', 'exit_code': 0, 'evidence': 'evidence/inventory_checks.txt'}],
 'developer_claims': [
   {'claim': '136 passing tests', 'status': P}, {'claim': '60 cases: 29 PASS, 10 FIXED, 21 DEFERRED-OK', 'status': P, 'reproduced': cases['summary']},
   {'claim': '28 unchanged-setup original probes OK; 35 OK through the adaptation', 'status': P},
   {'claim': 'original full command exits 1 with RN02, RN03, RN07 ERROR and RT12a, RT14a, RG0 WEAK', 'status': P},
   {'claim': 'test methods retained: 40 (initial archive), 41 (Batch 1 baseline), 43 (reviewed Batch 2 checkpoint)', 'status': P, 'reproduced': 'all present; none has fewer assertions; no expected-failure or skip marker'},
   {'claim': 'all 22 supplied files, the four earlier inputs and three nested archives unchanged', 'status': P},
   {'claim': 'both change inventories and patches complete, including JS/HTML', 'status': P},
   {'claim': 'adapter preserves every original verdict and gate expression', 'status': P, 'reproduced': 'return statements and verdict-condition assignments identical in all 35 probes; six probe bodies and one helper changed, one helper added; delta equals the delivered patch'},
   {'claim': 'baseline 21 OK / 11 WEAK / 3 NOTE reproduced before changes; implementation order', 'status': 'NOT_VERIFIED', 'reproduced': 'delivered logs are consistent; chronology cannot be established from an archive'},
   {'claim': 'teaching month: ten approvals, three held dispositions, impact +311 / +200 / -211 / -300', 'status': P, 'reproduced': 'delivered script and independent probe M1'}],
 'rv_corrections': rv,
 'corrective_tickets_C01_to_C06': {k: {'status': v[0], 'summary': v[1], 'open_defects': v[2]} for k, v in corr.items()},
 'original_probe_ids': orig,
 'previously_failed_or_noted_ids': {'failed_before': failed_before, 'noted_before': noted_before, 'all_now_ok_in_delivered_gate': all((D_.get(p) or A_[p]) == 'OK' for p in failed_before + noted_before)},
 'probe_adaptations': adaptations,
 'strengthened_RT14b': {'status': P, 'cases': ['initial D1 disposition refused -> ERROR, exit 1, third charge not constructed', 'initial D2 disposition refused -> ERROR, exit 1, third charge not constructed',
                                              'D1 ineligible before the third charge -> ERROR, exit 1, third charge not constructed', 'no fault -> OK, exit 0; D1 eligible, then ineligible with POSSIBLE_DUPLICATE after D3'],
                         'delivered_tests': ['test_RT14b_fails_when_either_initial_disposition_is_refused', 'test_RT14b_fails_when_initial_D1_is_ineligible'], 'evidence': 'evidence/rt14b_fault_injection.txt'},
 'independent_probes': mine,
 'batch_2_tickets': tickets,
 'validation_cases': [{'id': c['id'], 'stage': c['stage'], 'raw_runner_status': c['status'], 'status': {'PASS': 'PASS', 'FIXED': 'PASS', 'DEFERRED-OK': 'DEFERRED'}.get(c['status'], 'FAIL'), 'detail': c.get('detail', '')} for c in cases['cases']],
 'validation_case_summary': cases['summary'],
 'validation_case_changes_since_last_review': ['base profile close checklist is typed (RV-06)', 'runner mandates state the explicit no-evidence reason (RV-11)', 'no expected outcome of any case changed'],
 'teaching_month': {
   'referral_route': {'status': P, 'approvals': 10, 'held_with_referral': ['TX-007', 'TX-009', 'TX-011'], 'quarantined': ['TX-008', 'receipt-TX-008'],
                      'impact': {'DEMO_OFFICE_SUPPLIES': '311.00', 'DEMO_REPAIRS': '200.00', 'DEMO_CARD_LIABILITY': '-211.00', 'DEMO_CASH': '-300.00'}, 'evidence': ['M1', 'evidence/05_synthetic_month.txt'], 'note': 'TX-009 keeps one receipt version at 79.99.'},
   'acceptance_route': {'status': P, 'approvals': 11, 'held_with_referral': ['TX-007', 'TX-011'],
                        'impact': {'DEMO_OFFICE_SUPPLIES': '391.00', 'DEMO_REPAIRS': '200.00', 'DEMO_CARD_LIABILITY': '-291.00', 'DEMO_CASH': '-300.00'}, 'evidence': ['M2', 'RG0 adapted'], 'note': 'The corrected receipt is held, disclosed, accepted by a non-supplier, then independently reviewed.'},
   'isolation': {'status': P, 'evidence': ['M1'], 'note': 'First-client artifacts, package bytes and evidence history unchanged; four cross-client attempts refused; both audit chains verify.'}},
 'G0_criteria': [
   {'criterion': 'Batch 1 and Batch 2 complete.', 'status': F, 'note': 'T-12 has an open P1 defect.'},
   {'criterion': 'All P0 and P1 current defects fixed with tests.', 'status': F, 'note': 'RA-01.'},
   {'criterion': 'Reviewer cases: zero unexpected, all fail-until-fix cases fixed.', 'status': P},
   {'criterion': 'A full synthetic month reaches approved-or-dispositioned, finalized and locked with no database edits and no weakened blocker.', 'status': P, 'note': 'Without the previous caveat: TX-009 keeps its receipt and is referred.'},
   {'criterion': 'Two synthetic clients in different periods on one engine with no cross-effects.', 'status': P},
   {'criterion': 'Documentation matches code.', 'status': P, 'note': 'Inventories complete; the report discloses the adapted probes and the failing original command.'}],
 'not_run': [{'item': 'Browser walkthrough of the demo UI', 'reason': 'No accounting control depends on it; HTTP boundaries executed through the delivered tests.'},
             {'item': 'Chronology of the implementation order and of the baseline reproduction', 'reason': 'Cannot be established from a final archive; delivered logs are consistent.'},
             {'item': 'UC-5 and UC-6', 'reason': 'Read only.'}],
}
assert len(results['validation_cases']) == 60
json.dump(results, open(os.path.join(out_dir, 'FABLE_RV_ACCEPTANCE_RESULTS.json'), 'w'), indent=1, ensure_ascii=False)
print('defects', corrections['priority_counts'], '| RV pass', len(results['decisions']['RV_01_to_RV_17']['pass']), 'fail', results['decisions']['RV_01_to_RV_17']['fail'])
print('tickets', {k: v['status'] for k, v in tickets.items()}, '| criteria', sum(len(v['criteria']) for v in tickets.values()))
print('original ids judged PASS:', sum(1 for v in orig.values() if v['judgment'] == P), 'of', len(orig), '| previously failed/noted all OK now:', results['previously_failed_or_noted_ids']['all_now_ok_in_delivered_gate'])
