"""Convert legacy FICTIONAL reviewer specifications to explicit statement fixtures.
Never used by accounting intake or as proof of a real statement population.
"""
import copy
from decimal import Decimal


def statement_specs(sources):
    rows=copy.deepcopy(sources)
    for row in rows:
        d=row['data']
        if row['kind']=='transaction' and d['activity']=='payment' and Decimal(d['amount'])>0:d['amount']=str(-Decimal(d['amount']))
    payments={(r['data']['account_id'],r['data']['source_id']):r['data']['amount'] for r in rows if r['kind']=='transaction' and r['data']['activity']=='payment'}
    for row in rows:
        if row['kind']=='receipt' and (row['data']['account_id'],row['data']['transaction_source_id']) in payments:row['data']['amount']=payments[(row['data']['account_id'],row['data']['transaction_source_id'])]
    for row in rows:
        c=row['data']
        if row['kind']!='statement_control':continue
        population=[r['data'] for r in rows if r['kind']=='transaction' and r['data']['account_id']==c['account_id'] and r['data']['currency']==c['currency'] and r['data']['status']=='posted' and c['period_start']<=r['data']['date']<=c['period_end']]
        totals={k:sum((Decimal(t['amount']) for t in population if t['activity']==k),Decimal('0.00')) for k in ('purchase','credit','payment','fee','interest','transfer','unknown')}
        # Preserve an intentionally incorrect declared legacy total as an incorrect purchase total.
        original_net=sum((abs(Decimal(t['amount'])) if t['activity']=='payment' else Decimal(t['amount']) for t in population),Decimal('0.00'))
        totals['purchase']+=Decimal(c['posted_total'])-original_net
        opening=Decimal('1000.00');closing=opening+sum(totals.values(),Decimal('0.00'))
        row['kind']='statement';row['data']={'account_id':c['account_id'],'statement_id':row['key'],'currency':c['currency'],'period_start':c['period_start'],'period_end':c['period_end'],'opening_balance':str(opening),'closing_balance':str(closing),'totals':{k:str(v) for k,v in totals.items()},'line_count':c['posted_count'],'line_ids':[t['source_id'] for t in population],'provenance':'manually_keyed','sign_convention':'positive_charges_negative_credits_and_payments','content':'Explicit fictional statement specification; no real client statement verified.'}
    return rows
