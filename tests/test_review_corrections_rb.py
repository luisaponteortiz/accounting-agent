"""New failure paths from Fable's RB review; all records are disposable fiction."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from accounting_agent.service import AccountingOS

ROOT=Path(__file__).resolve().parents[1]


class ReviewCorrectionsRB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py'
        spec=importlib.util.spec_from_file_location('rb_fixtures',path)
        cls.f=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(cls.f)

    @classmethod
    def tearDownClass(cls):cls.f.TMP.cleanup()

    def test_RB01_late_link_quarantines_previously_admitted_or_approved_destination(self):
        f=self.f
        for approved in (False,True):
            with self.subTest(destination_approved=approved):
                o=f.approved_locked_november()
                rows=[f.tx('B1','2026-12-02','40.00'),f.rc('B1','2026-12-02','40.00')]
                o.intake(f.PREP2,f.packet('plain',rows+[f.stmt(rows,f.DEC,opening='100.00')]))
                f.run(o,'card_preparation','2026-12',f.PREP2)
                a=f.gov(o,f.CARD+':B1','2026-12');self.assertTrue(a['eligible'])
                if approved:self.assertEqual(f.review(o,f.REV2,a,'approve')[0],'ok')
                o.intake(f.PREP2,f.packet('claim',[f.sup('B1','2026-12-02','40.00','A1')]))
                f.run(o,'card_preparation','2026-12',f.PREP2)
                self.assertIsNone(f.gov(o,f.CARD+':B1','2026-12'))
                self.assertEqual(f.gov(o,f.CARD+':A1')['review_status'],'approve')
                state=o.export(f.PREP)
                held={x['source_key'] for x in state['source_exceptions'] if x['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD' and x['period_id']=='2026-11'}
                self.assertTrue({f.CARD+':B1','receipt-B1'}<=held)
                self.assertTrue(any(m['blocked'] and m['had_approval'] and m['from_period_id']=='2026-11' and m['to_period_id']=='2026-12' for m in state['source_move_history']))
                if approved:
                    self.assertTrue(any(e['item_key']==f.CARD+':B1' and e['period_id']=='2026-12' and e['code'].startswith('APPROVED_SOURCE_') for e in state['accounting_events']))
                self.assertTrue(any(e['code']=='ITEM_LEFT_POPULATION' and e['item_key']==f.CARD+':B1' for e in state['accounting_events']))
                o.reopen_period(f.PADMIN,'2026-11','Review fictional late link')
                f.run(o,'card_preparation','2026-11');f.run(o,'card_preparation','2026-12',f.PREP2)
                self.assertIsNone(f.gov(o,f.CARD+':A1'))
                terminal=f.gov(o,f.CARD+':B1','2026-12')
                self.assertIn('SOURCE_TRANSITION_REQUIRES_REVIEW',terminal['blockers'])
                self.assertEqual(len([a for a in f.arts(o,None,'2026-12') if a['governing'] and a['kind']=='card_proposal']),1)
                self.assertTrue(all(m['from_period_id']!=m['to_period_id'] for m in o.export(f.PREP)['source_move_history']))
                self.assertTrue(o.verify_audit(f.PREP))

    def test_RB01_unresolved_link_then_predecessor_then_resolution_keeps_entire_quarantine(self):
        f=self.f;o=f.approved_locked_november()
        rows=[f.sup('A1Y','2026-12-03','40.00','A1X'),f.rc('A1Y','2026-12-03','40.00')]
        o.intake(f.PREP2,f.packet('terminal-first',rows+[f.stmt(rows,f.DEC,opening='100.00')]))
        f.run(o,'card_preparation','2026-12',f.PREP2)
        self.assertFalse(f.gov(o,f.CARD+':A1Y','2026-12')['eligible'])
        o.intake(f.PREP2,f.packet('middle-later',[f.sup('A1X','2026-12-02','40.00','A1'),f.rc('A1X','2026-12-02','40.00')]))
        o.intake(f.PREP2,f.packet('resolve',[rows[0]]));f.run(o,'card_preparation','2026-12',f.PREP2)
        self.assertIsNone(f.gov(o,f.CARD+':A1Y','2026-12'))
        held={e[0] for e in f.exceptions_of(o) if e[1:] == ('2026-11','SOURCE_MOVED_FROM_LOCKED_PERIOD')}
        self.assertTrue({f.CARD+':A1X',f.CARD+':A1Y','receipt-A1X','receipt-A1Y'}<=held)

    def test_RB02_repointed_receipt_and_statement_replacements_need_independent_acceptance(self):
        f=self.f
        for kind in ('receipt','statement'):
            with self.subTest(kind=kind):
                if kind=='receipt':
                    o,rows=f.mismatch_november()
                    away=f.rc('A1-VOID','2026-11-03','39.99',key='receipt-A1')
                    replacement=f.rc('A1','2026-11-03','40.00',key='receipt-A1-new',content='Corrected fictional support')
                    earlier_key='receipt-A1';changed_field='amount'
                else:
                    o,rows=f.short_statement()
                    away=f.stmt(rows,period=('2027-01','2027-01-01','2027-01-31'),key='stmt-2026-11',totals=f.WRONG,closing_balance='90.00')
                    replacement=f.stmt(rows,key='stmt-2026-11-new')
                    earlier_key='stmt-2026-11';changed_field='totals'
                o.intake(f.PREP2,f.packet('repoint-and-replace',[away,replacement]));f.run(o,'card_preparation')
                a=f.gov(o,f.CARD+':A1');revisions=a['payload']['data']['evidence_revisions']
                self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',a['blockers'])
                self.assertTrue(any(r['earlier']['source_key']==earlier_key and r['earlier']['version']==1 and changed_field in r['changed_fields'] for r in revisions))
                self.assertEqual(f.review(o,f.REV,a,'approve')[0],'refused')
                if kind=='statement':
                    self.assertTrue(f.workpaper(o)['payload']['data']['statement_revisions'])
                    self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',f.gov(o,f.CARD+':A2')['blockers'])
                for supplier in (f.PREP,f.PREP2):
                    o.grant_authority(f.ADMIN,supplier.id,['disposition'],'Probe supplier refusal')
                    self.assertEqual(f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=f.human(supplier.id,'reviewer'))[:2],('refused',403))
                self.assertEqual(f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')[0],'ok')
                f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible'])
                o.grant_authority(f.ADMIN,f.DISP.id,['review'],'Probe acceptance is not final review')
                self.assertEqual(f.review(o,f.DISP,a,'approve')[:2],('refused',403))
                self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')
                revised=copy.deepcopy(replacement);revised['data']['content']='Fictional support edited again'
                o.intake(f.PREP2,f.packet('next-revision',[revised]));f.run(o,'card_preparation')
                self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',f.gov(o,f.CARD+':A1')['blockers'])

    def test_RB03_equivalent_vendor_and_receipt_rules_keep_authors_across_scope_and_key(self):
        f=self.f
        for kind,key,value in (('vendor_mapping','demo_acme',f.ACME),('receipt_matching','default',f.RM)):
            for route in ('item_scope','new_key'):
                with self.subTest(kind=kind,route=route):
                    options={'item2':f.CARD+':A1'} if route=='item_scope' else {'key2':key+'-replacement','end1':'2026-11-02','start2':'2026-11-03'}
                    o,a=f.rule_case(f.REV4,value,dict(value),kind=kind,key=key,**options)
                    self.assertIn(f.REV4.id,a['contributors'])
                    self.assertEqual(f.review(o,f.REV4,a,'approve')[:2],('refused',403))
                    self.assertEqual(f.review(o,f.REV2,a,'approve')[0],'ok')

    def test_RB04_prior_restatement_waits_for_all_own_period_acceptances_and_revocation_reblocks(self):
        f=self.f;o=f.new_os(periods=(f.NOV,f.DEC));rows=f.clean_november(o)
        dec=[f.tx('D1','2026-12-05','15.00'),f.rc('D1','2026-12-05','15.00')]
        o.intake(f.PREP,f.packet('dec',dec+[f.stmt(dec,f.DEC,opening='120.00')]))
        f.run(o,'card_preparation','2026-12')
        self.assertIn('STATEMENT_OPENING_BALANCE_BREAK',f.gov(o,f.CARD+':D1','2026-12')['blockers'])
        o.intake(f.PREP2,f.packet('restate',[f.stmt(rows,opening='20.00')]))
        f.run(o,'card_preparation');f.run(o,'card_preparation','2026-12')
        wp=f.workpaper(o,'2026-12');data=wp['payload']['data']
        self.assertTrue(data['prior_statement_revisions'])
        self.assertEqual(data['opening_continuity'],'prior_statement_revision_unaccepted')
        self.assertIn('STATEMENT_PRIOR_REVISION_REQUIRES_REVIEW',wp['blockers'])
        self.assertFalse(f.gov(o,f.CARD+':D1','2026-12')['eligible'])
        decision=f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')
        self.assertEqual(decision[0],'ok')
        f.run(o,'card_preparation','2026-12')
        self.assertFalse(f.gov(o,f.CARD+':D1','2026-12')['eligible'])
        self.assertEqual(f.dispose(o,f.CARD+':A2','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')[0],'ok')
        f.run(o,'card_preparation');f.run(o,'card_preparation','2026-12')
        d=f.gov(o,f.CARD+':D1','2026-12');self.assertTrue(d['eligible'])
        self.assertEqual(f.workpaper(o,'2026-12')['payload']['data']['opening_continuity'],'verified')
        o.grant_authority(f.ADMIN,f.DISP.id,['review'],'Prior acceptance is preparation lineage')
        self.assertEqual(f.review(o,f.DISP,d,'approve')[:2],('refused',403))
        self.assertEqual(f.review(o,f.REV,d,'approve')[0],'ok')
        o.revoke_disposition(f.DISP,decision[1],'Withdraw fictional prior acceptance')
        f.run(o,'card_preparation','2026-12')
        current=f.gov(o,f.CARD+':D1','2026-12')
        self.assertIn('STATEMENT_PRIOR_REVISION_REQUIRES_REVIEW',current['blockers'])
        self.assertNotEqual(current['review_status'],'approve')
        self.assertTrue(o.verify_audit(f.PREP))

    def test_PR15_second_client_state_has_no_first_client_name(self):
        f=self.f;client='second_fictional_client';actor=f.human('neutral-preparer','preparer',client)
        o=AccountingOS(Path(f.TMP.name)/'neutral.sqlite3',[actor.scope])
        profile=copy.deepcopy(f.PROFILE)
        profile.update(client_id=client,name='Second fictional client',notice='Fictional client configuration')
        o.onboard(actor,profile)
        self.assertNotIn('Bird Bowl',json.dumps(o.state(actor)))
