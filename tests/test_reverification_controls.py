"""Adversarial regressions for RV-01..RV-17; service-only fictional fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from accounting_agent.core import ControlError

ROOT=Path(__file__).resolve().parents[1]

class ReverificationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_REVERIFICATION/fable_reverification_probes.py'
        spec=importlib.util.spec_from_file_location('fable_rv_fixtures',path)
        cls.f=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(cls.f)

    @classmethod
    def tearDownClass(cls):cls.f.TMP.cleanup()

    def clean(self,periods=None):
        f=self.f;o=f.new_os(periods=periods or (f.NOV,));rows=f.clean_november(o);f.run(o,'card_preparation');return o,rows

    def approve(self,o,keys=('A1','A2')):
        f=self.f
        for key in keys:self.assertEqual(f.review(o,f.REV,f.gov(o,f.CARD+':'+key),'approve')[0],'ok')

    def test_RV04_locked_receipts_are_not_rebound_by_unrelated_intake(self):
        f=self.f;o,rows=self.clean((f.NOV,f.DEC));self.approve(o)
        pid=o.finalize_package(f.FIN,'2026-11','card_preparation','Fictional handover');o.lock_period(f.PADMIN,'2026-11','Fictional lock')
        before=o.export(f.PREP);dec=[f.tx('D1','2026-12-05','15.00'),f.rc('D1','2026-12-05','15.00')]
        o.intake(f.PREP2,f.packet('dec',dec+[f.stmt(dec,f.DEC,opening='100.00')]))
        after=o.export(f.PREP)
        self.assertEqual(after['source_exceptions'],[]);self.assertEqual(after['accounting_events'],[])
        self.assertEqual(before['packages'],after['packages'])
        late=f.rc('A1','2026-11-03','40.00',content='Genuinely corrected fictional receipt')
        o.intake(f.PREP2,f.packet('late',[late]));self.assertTrue(any(e['code']=='APPROVED_SOURCE_REVISED' and e['item_key']==f.CARD+':A1' for e in o.state(f.PREP)['accounting_events']));self.assertTrue(any(e['source_key']=='receipt-A1' and e['reason']=='LATE_ACTIVITY_IN_LOCKED_PERIOD' for e in o.state(f.PREP)['source_exceptions']))

    def test_RV03_tombstone_removes_governing_item_and_supersedes_exceptions(self):
        f=self.f;o=f.new_os();pending=f.tx('P1','2026-11-08','10.00',status='pending',as_of=1)
        rows=f.clean_november(o,extra=[pending]);f.run(o,'card_preparation');old=f.gov(o,f.CARD+':P1')
        gone=copy.deepcopy(pending);gone.update(as_of=2,tombstone=True,removal_reason='feed_removed');o.intake(f.PREP,f.packet('gone',[gone]));f.run(o,'card_preparation')
        self.assertIsNone(f.gov(o,f.CARD+':P1'));self.approve(o)
        state=o.export(f.PREP);self.assertTrue(all(e['status']=='superseded' for e in state['exceptions'] if e['item_key']==f.CARD+':P1'))
        self.assertTrue(any(e['item_key']==f.CARD+':P1' and e['status']=='superseded' for e in state['exception_history']))
        self.assertEqual(next(a for a in state['artifacts'] if a['id']==old['id'])['review_status'],'stale')
        pid=o.finalize_package(f.FIN,'2026-11','card_preparation','Fictional removal handover')
        package=json.loads(next(p for p in o.export(f.PREP)['packages'] if p['id']==pid)['payload'])
        self.assertEqual([r['item_key'] for r in package['removed_items']],[f.CARD+':P1'])
        self.assertEqual(package['removed_items'][0]['source_change']['metadata']['removal_reason'],'feed_removed')

    def test_RV01_superseding_identity_respects_lock_then_releases_and_records_history(self):
        f=self.f;o,rows=self.clean((f.NOV,f.DEC));self.approve(o);o.lock_period(f.PADMIN,'2026-11','Fictional lock')
        new=f.tx('A1X','2026-12-02','40.00');new['supersedes']=f.CARD+':A1'
        dec=[new,f.rc('A1X','2026-12-02','40.00')];o.intake(f.PREP2,f.packet('replacement',dec+[f.stmt(dec,f.DEC,opening='100.00')]))
        f.run(o,'card_preparation','2026-12');self.assertIsNone(f.gov(o,f.CARD+':A1X','2026-12'))
        st=o.export(f.PREP)
        self.assertTrue(any(e['source_key']==f.CARD+':A1X' and e['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD' for e in st['source_exceptions']))
        self.assertTrue(any(m['from_period_id']=='2026-11' and m['blocked'] for m in st['source_move_history']))
        self.assertTrue(any(e['code']=='APPROVED_SOURCE_SUPERSEDED' and e['item_key']==f.CARD+':A1' for e in st['accounting_events']))
        self.assertTrue(any(s['source_key']==f.CARD+':A1' for s in st['sources']))
        o.reopen_period(f.PADMIN,'2026-11','Release fictional replacement');f.run(o,'card_preparation');f.run(o,'card_preparation','2026-12')
        self.assertIsNone(f.gov(o,f.CARD+':A1'));replacement=f.gov(o,f.CARD+':A1X','2026-12')
        self.assertIn('SOURCE_TRANSITION_REQUIRES_REVIEW',replacement['blockers'])
        self.assertNotIn('MISSING_RECEIPT',replacement['blockers']);self.assertIn(f.PREP.id,replacement['contributors'])
        self.assertTrue(any(r['item_key']==f.CARD+':A1' for r in o.state(f.PREP)['removed_items']))

    def test_RV02_origin_identity_survives_revision_and_current_reference_still_collides(self):
        f=self.f;o,rows=self.clean();a=f.gov(o,f.CARD+':A1');ref=a['payload']['data']['evidence'][0]
        lines=[('DEMO_OFFICE_SUPPLIES','40.00','0.00',None),('DEMO_CARD_LIABILITY','0.00','40.00',None)]
        j=f.journal('J1','2026-11-03',lines,['support'],origin_sources=[ref]);o.intake(f.PREP,f.packet('journal',[j,f.doc('support','journal_support',journal_keys=['J1'])]))
        changed=f.tx('A1','2026-11-03','40.00',desc='ACME  PAPER  DEMO');o.intake(f.PREP2,f.packet('cosmetic',[changed]))
        f.run(o,'card_preparation');f.run(o,'journal_preparation')
        self.assertIn('SOURCE_ALREADY_HAS_ENTRY',f.gov(o,f.CARD+':A1')['blockers']);self.assertIn('ORIGIN_SOURCE_SUPERSEDED',f.gov(o,'J1')['blockers'])
        j['data']['origin_sources']=[f.gov(o,f.CARD+':A1')['payload']['data']['evidence'][0]];o.intake(f.PREP,f.packet('refresh-origin',[j]));f.run(o,'journal_preparation');f.run(o,'card_preparation')
        self.assertIn('SOURCE_ALREADY_HAS_ENTRY',f.gov(o,'J1')['blockers']);self.assertNotIn('ORIGIN_SOURCE_SUPERSEDED',f.gov(o,'J1')['blockers'])

    def test_RV05_profile_withdrawal_is_effective_dated_and_can_be_reintroduced(self):
        f=self.f;o,rows=self.clean((f.NOV,f.DEC));self.approve(o)
        p=copy.deepcopy(f.PROFILE);p['version']='retire-metro';p['vendors']=[v for v in p['vendors'] if v['id']!='demo_metro']
        sid=o.onboard(f.PREP,p,effective_from='2026-12-01');o.approve_profile_version(f.CTRL,sid,'Withdraw fictional mapping in December')
        self.assertEqual(f.gov(o,f.CARD+':A2')['review_status'],'approve')
        dec=[f.tx('D2','2026-12-03','60.00',desc='METRO REPAIR DEMO'),f.rc('D2','2026-12-03','60.00',vendor='METRO REPAIR DEMO')]
        o.intake(f.PREP,f.packet('dec',dec+[f.stmt(dec,f.DEC,opening='100.00')]))
        f.run(o,'card_preparation','2026-12');self.assertIn('UNKNOWN_VENDOR',f.gov(o,f.CARD+':D2','2026-12')['blockers'])
        self.assertTrue(o.export(f.PREP)['rule_retirements'])
        restored=copy.deepcopy(f.PROFILE);restored['version']='restore-metro';sid=o.onboard(f.PREP,restored,effective_from='2026-12-01');o.approve_profile_version(f.CTRL,sid,'Explicitly reintroduce fictional vendor')
        f.run(o,'card_preparation','2026-12');self.assertNotIn('UNKNOWN_VENDOR',f.gov(o,f.CARD+':D2','2026-12')['blockers'])

    def test_RV06_untyped_new_knowledge_refused_and_legacy_requirement_unsatisfied(self):
        f=self.f;o=f.new_os();p=copy.deepcopy(f.PROFILE);p['version']='bad-untyped';p['required_close_evidence']=['bank_reconciliation']
        with self.assertRaises(ControlError) as caught:o.onboard(f.PREP,p)
        self.assertEqual(caught.exception.status,400)
        with self.assertRaises(ControlError):o.propose_rule(f.PREP,'close_checklist','close',['bank_reconciliation'],'2026-11-01')
        from accounting_agent.modules import close_readiness
        with o.store.transaction() as db:ctx=o.context(db,f.PREP,'2026-11','close_readiness')
        ctx['profile']['required_close_evidence']=['bank_reconciliation'];ctx['period_status']={'items':[],'quarantined_sources':[]}
        out=close_readiness(ctx)[0];self.assertIn('MISSING_CLOSE_EVIDENCE',out['blockers']);self.assertEqual(out['data']['requirements'][0]['reason'],'UNTYPED_REQUIREMENT')

    def test_RV12_revised_receipt_requires_independent_acceptance_and_discloses_history(self):
        f=self.f;o=f.new_os();rows=[f.tx('A1','2026-11-03','40.00'),f.rc('A1','2026-11-03','39.99')]
        o.intake(f.PREP,f.packet('original',rows+[f.stmt(rows)]));f.run(o,'card_preparation')
        a=f.gov(o,f.CARD+':A1');self.assertIn('RECEIPT_AMOUNT_POLICY_UNSET',a['blockers'])
        self.assertEqual(f.dispose(o,f.CARD+':A1','RECEIPT_AMOUNT_POLICY_UNSET','refer_external')[0],'ok')
        f.run(o,'card_preparation');self.assertFalse(f.gov(o,f.CARD+':A1')['eligible'])
        o.intake(f.PREP2,f.packet('corrected-evidence',[f.rc('A1','2026-11-03','40.00')]))
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',a['blockers'])
        revision=a['payload']['data']['evidence_revisions'][0];self.assertEqual(revision['earlier']['version'],1);self.assertIn('amount',revision['changed_fields']);self.assertEqual(revision['supplier'],f.PREP2.id)
        o.grant_authority(f.ADMIN,f.PREP.id,['disposition'],'Fictional former-supplier negative control')
        supplier=f.human(f.PREP.id,'reviewer');refusal=f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=supplier)
        self.assertEqual(refusal[0:2],('refused',403))
        self.assertEqual(f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')[0],'ok')
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible']);self.assertTrue(a['payload']['data']['evidence_revisions'])
        self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')

    def decision(self,o,key,code,choice,payload=None,evidence=None):
        f=self.f;a=f.gov(o,key)
        refs=evidence if evidence is not None else a['payload']['data']['evidence']+a['payload']['data'].get('duplicate_evidence',[])
        return o.disposition(f.DISP,'card_preparation','2026-11',key,code,choice,payload or {},refs,'Explicit fictional evidence-bound decision')

    def test_RV07_activity_and_account_types_constrain_treatment(self):
        f=self.f;o=f.new_os();extra=[f.tx('P1','2026-11-12','-300.00',desc='CARD PAYMENT DEMO',activity='payment'),f.rc('P1','2026-11-12','-300.00',vendor='CARD PAYMENT DEMO'),f.tx('U1','2026-11-13','20.00',desc='UNKNOWN'),f.rc('U1','2026-11-13','20.00',vendor='UNKNOWN')]
        f.clean_november(o,extra=extra);f.run(o,'card_preparation')
        with self.assertRaises(ControlError):self.decision(o,f.CARD+':P1','NON_EXPENSE_REQUIRES_REVIEW','standalone_credit',{'account_id':'DEMO_OFFICE_SUPPLIES'})
        for account in ('DEMO_CASH','DEMO_CARD_LIABILITY'):
            with self.assertRaises(ControlError):self.decision(o,f.CARD+':U1','UNKNOWN_CATEGORY','code_category',{'account_id':account})
        with self.assertRaises(ControlError):self.decision(o,f.CARD+':P1','NON_EXPENSE_REQUIRES_REVIEW','settlement_of_card_liability',{'cash_account':'DEMO_OFFICE_SUPPLIES'})
        self.decision(o,f.CARD+':P1','NON_EXPENSE_REQUIRES_REVIEW','settlement_of_card_liability',{'cash_account':'DEMO_CASH'});f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':P1')['eligible'])

    def test_RV08_new_candidate_invalidates_distinct_decision_without_statement_dependency(self):
        f=self.f;o,rows=f.duplicate_pair()
        for key in ('D1','D2'):
            a=f.gov(o,f.CARD+':'+key);refs=[e for e in a['payload']['data']['evidence']+a['payload']['data']['duplicate_evidence'] if e['source_key'].startswith('receipt-')]
            self.decision(o,f.CARD+':'+key,'POSSIBLE_DUPLICATE','distinct_purchases',evidence=refs)
        f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':D1')['eligible'])
        third=[f.tx('D3','2026-11-06','90.00'),f.rc('D3','2026-11-06','90.00')]
        o.intake(f.PREP,f.packet('third',third+[f.stmt(rows+third)]));f.run(o,'card_preparation')
        self.assertIn('POSSIBLE_DUPLICATE',f.gov(o,f.CARD+':D1')['blockers']);self.assertFalse(f.gov(o,f.CARD+':D1')['eligible'])

    def test_RV09_survivor_cites_exclusion_and_dispositioner_cannot_review(self):
        f=self.f;o,rows=f.duplicate_pair();did=self.decision(o,f.CARD+':D2','POSSIBLE_DUPLICATE','duplicate_of',{'duplicate_of':f.CARD+':D1'})
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':D1');self.assertNotIn('POSSIBLE_DUPLICATE',a['blockers']);self.assertIn(did,a['payload']['data']['disposition_ids']);self.assertIn(f.DISP.id,a['contributors'])
        o.grant_authority(f.ADMIN,f.DISP.id,['review'],'Explicit negative control grant')
        self.assertEqual(f.review(o,f.DISP,a,'approve')[0:2],('refused',403));self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')
        o.revoke_disposition(f.DISP,did,'Revoke fictional exclusion');f.run(o,'card_preparation')
        self.assertTrue(all('POSSIBLE_DUPLICATE' in f.gov(o,f.CARD+':'+key)['blockers'] for key in ('D1','D2')))

    def test_RV10_semantic_rule_authors_retained_but_different_category_author_not_barred(self):
        f=self.f
        for category,barred in (('DEMO_OFFICE_SUPPLIES',True),('DEMO_REPAIRS',False)):
            o=f.new_os();author=f.human('old-rule-author','preparer');value=copy.deepcopy(f.PROFILE['vendors'][0]);value['category']=category
            first=o.propose_rule(author,'vendor_mapping',value['id'],value,'2026-11-01');o.approve_rule(f.CTRL,first,'Fictional earlier mapping')
            latest=copy.deepcopy(value);latest.update(category='DEMO_OFFICE_SUPPLIES',name='Cosmetic display name')
            second=o.propose_rule(f.PREP2,'vendor_mapping',latest['id'],latest,'2026-11-01',supersedes=first);o.approve_rule(f.CTRL2,second,'Explicit current mapping')
            f.clean_november(o);f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1')
            o.grant_authority(f.ADMIN,author.id,['review'],'Fictional rule-author control grant')
            result=f.review(o,f.human(author.id,'reviewer'),a,'approve')
            self.assertEqual(result[0],'refused' if barred else 'ok')
            self.assertEqual(author.id in a['contributors'],barred)

    def test_RV11_freshness_schema_and_explicit_no_evidence_approval_are_audited(self):
        f=self.f;o=f.new_os();args=(f.PREP,['card_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,{'kind':'fixed','period_id':'2026-11'})
        for value in ({},{'bad_kind':'occurrence_start'},{'transaction':'not-a-date'},{'none':''},{'none':'reason','transaction':'occurrence_start'}):
            with self.assertRaises(ControlError) as failure:o.create_mandate(*args,value)
            self.assertEqual(failure.exception.status,400)
        reason={'none':'Fictional fixed snapshot exercise only; no evidence freshness claimed'}
        mid=o.create_mandate(*args,reason);o.approve_mandate(f.CTRL,mid,'Explicitly accept the no-evidence reason')
        event=next(e for e in o.export(f.PREP)['audit_history'] if e['event']=='mandate_approved');self.assertEqual(json.loads(event['payload'])['freshness'],reason)

    def test_RV13_statement_limits_are_visible_and_waiver_requires_approved_rule(self):
        f=self.f;o=f.new_os();rows=[f.tx('A1','2026-11-03','40.00'),f.rc('A1','2026-11-03','40.00')]
        o.intake(f.PREP,f.packet('no-ids',rows+[f.stmt(rows,line_ids=False,provenance='manually_keyed')]))
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertIn('STATEMENT_LINE_IDENTITY_NOT_VERIFIED',a['blockers']);self.assertEqual(a['payload']['data']['line_identity'],'not_supplied');self.assertEqual(a['payload']['data']['statement_provenance']['supplier'],f.PREP.id)
        rid=o.propose_rule(f.PREP,'statement_policy','line-identity',{'allow_without_line_ids':True},'2026-11-01');f.run(o,'card_preparation');self.assertFalse(f.gov(o,f.CARD+':A1')['eligible'])
        o.approve_rule(f.CTRL,rid,'Explicit fictional first-cycle document policy');f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':A1')['eligible'])
        self.assertIn(f.CTRL.id,f.gov(o,f.CARD+':A1')['contributors'])
        o.open_period(f.PADMIN,'2026-10','2026-10-01','2026-10-31','Configure prior continuity prerequisite');f.run(o,'card_preparation')
        self.assertIn('STATEMENT_PRIOR_PERIOD_MISSING',f.gov(o,f.CARD+':A1')['blockers'])

    def test_RV14_alias_preview_contains_normalization_and_collision_ids(self):
        f=self.f;o=f.new_os();value={'id':'another','name':'Fictional alias preview','aliases':['ACME-PAPER/DEMO'],'category':'DEMO_REPAIRS'}
        rid=o.propose_rule(f.PREP,'vendor_mapping','another',value,'2026-11-01');rule=next(r for r in o.state(f.CTRL)['rules'] if r['id']==rid)
        self.assertEqual(rule['normalized_aliases'],['acme paper demo']);self.assertTrue(rule['alias_collisions']);self.assertEqual(rule['status'],'proposed')
        self.assertEqual(rule,next(r for r in o.export(f.CTRL)['rules'] if r['id']==rid))

    def test_RV15_distinct_purchases_requires_document_for_every_candidate(self):
        f=self.f;o,rows=f.duplicate_pair();a=f.gov(o,f.CARD+':D1');own=[e for e in a['payload']['data']['evidence'] if e['source_key'] in (f.CARD+':D1','receipt-D1')]
        with self.assertRaises(ControlError):self.decision(o,f.CARD+':D1','POSSIBLE_DUPLICATE','distinct_purchases',evidence=own)
        self.decision(o,f.CARD+':D1','POSSIBLE_DUPLICATE','distinct_purchases',evidence=own+a['payload']['data']['duplicate_evidence'])
        f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':D1')['eligible'])

    def test_RV17_finalized_packages_have_supersession_and_one_governing_version(self):
        f=self.f;o,rows=self.clean();self.approve(o);first=o.finalize_package(f.FIN,'2026-11','card_preparation','First fictional handover')
        original=next(p for p in o.state(f.PREP)['packages'] if p['id']==first)
        o.intake(f.PREP2,f.packet('revision',[f.tx('A2','2026-11-04','60.00',desc='METRO  REPAIR  DEMO')]))
        f.run(o,'card_preparation');self.approve(o);second=o.finalize_package(f.FIN,'2026-11','card_preparation','Replacement fictional handover')
        rows=o.state(f.PREP)['packages'];old=next(p for p in rows if p['id']==first);new=next(p for p in rows if p['id']==second)
        self.assertEqual((old['hash'],old['payload']),(original['hash'],original['payload']));self.assertFalse(old['governing']);self.assertTrue(new['governing']);self.assertEqual(json.loads(new['payload'])['supersedes_package_id'],first)

    def test_RV16_inventory_and_patch_cover_every_changed_runtime_file(self):
        import hashlib
        import subprocess
        import tempfile
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,str(ROOT/'scripts/build_change_report.py'),'--output-dir',tmp],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            inventory=json.loads((Path(tmp)/'changed-files.json').read_text());listed={row['file'] for row in inventory['files']};patch_text=(Path(tmp)/'source-and-tests.patch').read_text()
            with zipfile.ZipFile(ROOT/inventory['baseline']) as baseline:
                members=set(baseline.namelist())
                for folder in ('accounting_agent','tests','scripts','review'):
                    for path in (ROOT/folder).rglob('*'):
                        if not path.is_file() or '__pycache__' in path.parts:continue
                        name=str(path.relative_to(ROOT))
                        if name not in members or path.read_bytes()!=baseline.read(name):
                            self.assertIn(name,listed,name);self.assertIn('+++ b/'+name,patch_text,name)
            self.assertIn('accounting_agent/web/app.js',listed);self.assertIn('accounting_agent/web/index.html',listed)

    def test_RV09_restoring_population_keeps_the_original_rejection(self):
        f=self.f;o,rows=f.duplicate_pair();original=f.gov(o,f.CARD+':D1')
        self.assertEqual(f.review(o,f.REV,original,'reject')[0],'ok')
        did=self.decision(o,f.CARD+':D2','POSSIBLE_DUPLICATE','duplicate_of',{'duplicate_of':f.CARD+':D1'})
        f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':D1')['eligible'])
        o.revoke_disposition(f.DISP,did,'Undo the only disposition');f.run(o,'card_preparation')
        restored=f.gov(o,f.CARD+':D1');self.assertEqual(restored['id'],original['id']);self.assertEqual(restored['review_status'],'reject');self.assertIn('POSSIBLE_DUPLICATE',restored['blockers'])

    def test_RV03_removed_quarantine_leaves_active_queue_but_preserves_history(self):
        f=self.f;o=f.new_os();source=f.tx('OUTSIDE','2026-10-01','12.00',as_of=1)
        o.intake(f.PREP,f.packet('outside',[source]));self.assertTrue(o.state(f.PREP)['source_exceptions'])
        removed=copy.deepcopy(source);removed.update(as_of=2,tombstone=True,removal_reason='voided');o.intake(f.PREP,f.packet('removed',[removed]))
        state=o.export(f.PREP);self.assertFalse(state['source_exceptions']);self.assertTrue(any(b['reason']=='UNASSIGNED_ACCOUNTING_PERIOD' for b in state['source_period_history']))

    def test_RV13_quarantined_prior_statement_cannot_replace_frozen_continuity(self):
        f=self.f;o,rows=self.clean((f.NOV,f.DEC));self.approve(o);o.lock_period(f.PADMIN,'2026-11','Fictional lock')
        late=f.stmt(rows,closing_balance='999.00');o.intake(f.PREP2,f.packet('late-statement',[late]))
        dec=[f.tx('D1','2026-12-03','20.00'),f.rc('D1','2026-12-03','20.00')]
        o.intake(f.PREP2,f.packet('dec',dec+[f.stmt(dec,f.DEC,opening='100.00')]))
        f.run(o,'card_preparation','2026-12');a=f.gov(o,f.CARD+':D1','2026-12')
        self.assertTrue(a['eligible']);self.assertEqual(a['payload']['data']['opening_continuity'],'verified')
        self.assertTrue(any(e['source_key']=='stmt-2026-11' and e['reason']=='LATE_ACTIVITY_IN_LOCKED_PERIOD' for e in o.state(f.PREP)['source_exceptions']))
