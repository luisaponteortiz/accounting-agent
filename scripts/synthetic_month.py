"""G0 walkthrough: fictional teaching month, service operations only; no SQL edits."""
import copy
import json
import sys
import tempfile
from pathlib import Path
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from accounting_agent.core import Actor,digest
from accounting_agent.demo import SCOPE,actor,seed,load,prepare_profile,grant_fixture_authority
from accounting_agent.service import AccountingOS


def exercise():
    with tempfile.TemporaryDirectory() as tmp:
        second_scope='demo_org/second_demo/local'
        os=AccountingOS(Path(tmp)/'g0.sqlite3',[SCOPE,second_scope]);seed(os);os.drain(actor('worker'))
        controller=Actor('teaching-dispositioner','reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(os,controller)
        reviewer=Actor('teaching-independent-reviewer','reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(os,reviewer)
        finalizer=Actor('teaching-independent-finalizer','reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(os,finalizer)
        def packet(rows,batch):
            p=load('fixtures/teaching.json');p.update(batch_id=batch,sources=rows);return p
        os.intake(actor(),load('fixtures/late_receipt.json'))
        original=load('fixtures/teaching.json')
        # Keep the mismatched third-party receipt unchanged and explicitly refer it.
        # Correct the deliberately unbalanced journal with a distinct supported fictional amount.
        j=copy.deepcopy(next(s for s in original['sources'] if s['key']=='J-002'))
        j['data']['lines'][0]['debit']='26.00';j['data']['lines'][1]['credit']='26.00'
        os.intake(actor(),packet([j],'teaching-corrections'))
        os.enqueue(actor(),'card_preparation');os.enqueue(actor(),'journal_preparation');os.drain(actor('worker'))
        def item(key):return next(a for a in os.state(actor())['artifacts'] if a['item_key']==key and a['governing'])
        def decide(key,code,choice,payload=None):
            a=item(key);return os.disposition(controller,'card_preparation','2026-11',key,code,choice,payload or {},a['payload']['data']['evidence']+a['payload']['data'].get('duplicate_evidence',[]),'Fictional teaching-month evidence reviewed; no client policy assertion')
        for key in ('TX-004','TX-005'):decide('demo_card_001:'+key,'POSSIBLE_DUPLICATE','distinct_purchases')
        for code,choice in [('UNKNOWN_VENDOR','confirm_vendor'),('UNKNOWN_CATEGORY','code_category')]:decide('demo_card_001:TX-003',code,choice,{'account_id':'DEMO_OFFICE_SUPPLIES'})
        decide('demo_card_001:TX-006','CREDIT_REQUIRES_REVIEW','standalone_credit',{'account_id':'DEMO_OFFICE_SUPPLIES'})
        decide('demo_card_001:TX-010','SPLIT_REQUIRES_REVIEW','allocate',{'allocations':[{'account_id':'DEMO_REPAIRS','amount':'20.00'},{'account_id':'DEMO_OFFICE_SUPPLIES','amount':'15.00'}]})
        decide('demo_card_001:TX-012','NON_EXPENSE_REQUIRES_REVIEW','settlement_of_card_liability',{'cash_account':'DEMO_CASH'})
        # Missing/pending evidence and foreign currency are explicitly referred for external
        # handling; their blockers remain. No invented receipt or FX/recognition policy.
        for key,code in [('TX-007','PENDING_TRANSACTION'),('TX-009','RECEIPT_AMOUNT_POLICY_UNSET'),('TX-011','CURRENCY_MISMATCH')]:decide('demo_card_001:'+key,code,'refer_external')
        os.enqueue(actor(),'card_preparation');os.drain(actor('worker'))
        current=[a for a in os.state(actor())['artifacts'] if a['current'] and a['period_id']=='2026-11' and a['kind'] in ('card_proposal','journal_proposal')]
        reviewed=[];carried=[];impact={}
        for a in current:
            if a['eligible']:
                os.review(reviewer,a['id'],a['hash'],a['fingerprint'],'approve','Independent fictional proposed-entry review')
                reviewed.append(a['item_key'])
                entry=a['payload']['data'].get('proposed_entry')
                for l in entry['lines'] if entry else []:impact[l['account_id']]=impact.get(l['account_id'],Decimal('0.00'))+Decimal(l['debit'])-Decimal(l['credit'])
            else:
                assert a['payload']['data'].get('disposition_ids'),(a['item_key'],a['blockers'])
                carried.append({'item_key':a['item_key'],'blockers':a['blockers']})
        ack='Pending TX-007, original mismatched receipt TX-009 and foreign-currency TX-011 referred externally; TX-008 belongs to unconfigured October. No ledger posting, reconciliation or external close represented.'
        ids=[os.finalize_package(finalizer,'2026-11',w,'Fictional G0 preparation handover',ack) for w in ('card_preparation','journal_preparation')]
        frozen=[p for p in os.export(actor())['packages']]
        os.lock_period(finalizer,'2026-11','G0 preparation lock with explicitly carried exceptions',ack)
        before=[(a['id'],a['hash'],a['review_status']) for a in os.state(actor())['artifacts'] if a['period_id']=='2026-11']
        # A second isolated client in December shares the engine, never the records or rules.
        prep2=actor(client='second_demo');rev2=actor('reviewer',client='second_demo');worker2=actor('worker',client='second_demo')
        p=load('config/bird_bowl.demo.json');p.update(client_id='second_demo',external_company_id='fictional-second-realm',entity_id='fictional-second-entity',book_id='fictional-second-book')
        prepare_profile(os,prep2,p);os.open_period(rev2,'2026-12','2026-12-01','2026-12-31','Fictional second-client month')
        sources=copy.deepcopy([s for s in original['sources'] if s['key'] in ('J-001','journal-support-001')])
        for s in sources:
            if s['kind']=='journal':s['data']['date']='2026-12-13'
            else:s['data']['period_id']='2026-12'
        p2=packet(sources,'second-teaching');p2.update(client_id='second_demo',external_company_id='fictional-second-realm')
        os.intake(prep2,p2);os.enqueue(prep2,'journal_preparation');os.drain(worker2)
        a=next(a for a in os.state(prep2)['artifacts'] if a['kind']=='journal_proposal');os.review(rev2,a['id'],a['hash'],a['fingerprint'],'approve','Independent second-client fictional review')
        after=[(a['id'],a['hash'],a['review_status']) for a in os.state(actor())['artifacts'] if a['period_id']=='2026-11']
        assert before==after
        assert frozen==os.export(actor())['packages']
        assert not any(a['scope']==SCOPE for a in os.state(prep2)['artifacts'])
        assert os.verify_audit(actor()) and os.verify_audit(prep2)
        return {'gate':'G0 software synthetic acceptance only','reviewed_items':reviewed,'carried_dispositioned_items':carried,'package_ids':ids,'package_hashes':[p['hash'] for p in frozen],'period_status':'locked','proposed_entry_impact':{k:str(v) for k,v in sorted(impact.items())},'impact_balances':sum(impact.values(),Decimal('0.00'))==0,'second_client_period':'2026-12','isolation':'PASS','audit_integrity':'PASS','records_changed_via':'service operations only','external_effects':'none','real_readiness':'NOT ESTABLISHED'}

if __name__=='__main__':print(json.dumps(exercise(),indent=2))
