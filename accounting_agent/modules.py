"""Accounting modules: pure handlers behind the common execution contracts.

No handler can post, approve, access the filesystem or call a model/connector.
"""
from decimal import Decimal
from .core import (Capability, ControlError, Step, Workflow, day, money, normalize,
                   require_keys, text_field, validate_entry)


def validate_source(kind, value):
    if kind == "transaction":
        require_keys(value, {"source_id", "source_system", "account_id", "date", "description", "amount", "currency", "status", "activity"}, {"requires_split", "supersedes_source_id"})
        if value["source_system"] != "fixture":
            raise ControlError("Only fixture intake is implemented")
        for name in ("source_id", "account_id", "description", "currency"):
            text_field(value[name], name)
        if value["status"] not in ("pending", "posted") or value["activity"] not in ("purchase", "credit", "payment", "transfer", "unknown", "fee", "interest"):
            raise ControlError("Unsupported transaction status/activity")
        if "requires_split" in value and type(value["requires_split"]) is not bool:
            raise ControlError("requires_split must be boolean")
        if "supersedes_source_id" in value:
            text_field(value["supersedes_source_id"], "supersedes_source_id")
        day(value["date"])
        money(value["amount"])
    elif kind == "receipt":
        require_keys(value, {"transaction_source_id", "account_id", "date", "vendor", "amount", "currency", "content"})
        for name in ("transaction_source_id", "account_id", "vendor", "currency", "content"):
            text_field(value[name], name, 10000 if name == "content" else 200)
        day(value["date"])
        money(value["amount"])
    elif kind == "statement_control":
        require_keys(value, {"account_id", "currency", "period_start", "period_end", "posted_count", "posted_total", "content"})
        if type(value["posted_count"]) is not int or not 0 <= value["posted_count"] <= 10000:
            raise ControlError("Invalid statement count")
        day(value["period_start"])
        day(value["period_end"])
        money(value["posted_total"])
        for name in ("account_id", "currency", "content"):
            text_field(value[name], name)
    elif kind == 'statement':
        require_keys(value,{'account_id','statement_id','currency','period_start','period_end','opening_balance','closing_balance','totals','line_count','provenance','sign_convention','content'},{'line_ids'})
        day(value['period_start']);day(value['period_end']);money(value['opening_balance']);money(value['closing_balance'])
        require_keys(value['totals'],{'purchase','credit','payment','fee','interest','transfer','unknown'})
        for amount in value['totals'].values():money(amount)
        if type(value['line_count']) is not int or not 0<=value['line_count']<=10000:raise ControlError('Invalid statement line count')
        if value['provenance'] not in ('system_extract','manually_keyed') or value['sign_convention']!='positive_charges_negative_credits_and_payments':raise ControlError('Statement provenance/sign convention required')
        if 'line_ids' in value and (not isinstance(value['line_ids'],list) or len(set(value['line_ids']))!=len(value['line_ids'])):raise ControlError('Invalid statement line identities')
    elif kind == "journal":
        require_keys(value, {"date", "currency", "memo", "lines", "supporting_keys"},{"origin_sources"})
        day(value["date"])
        text_field(value["currency"], "currency")
        text_field(value["memo"], "memo", 2000)
        if not isinstance(value["lines"], list) or not 2 <= len(value["lines"]) <= 100:
            raise ControlError("Journal requires 2–100 lines")
        for line in value["lines"]:
            require_keys(line, {"account_id", "debit", "credit"},{"dimensions"})
            text_field(line["account_id"], "account_id")
            money(line["debit"])
            money(line["credit"])
        if not isinstance(value["supporting_keys"], list) or len(value["supporting_keys"]) > 100:
            raise ControlError("Invalid supporting keys")
        for key in value["supporting_keys"]:
            text_field(key, "supporting key")
    elif kind == "document":
        require_keys(value, {"document_type", "content"}, {"period_id","account_id","journal_keys"})
        text_field(value["document_type"], "document_type")
        text_field(value["content"], "content", 10000)
    else:
        raise ControlError("Source type is not implemented: " + str(kind))


def refs(rows):
    return [{"snapshot_id": r["id"], "hash": r["hash"], "source_key": r["source_key"], "version": r["version"]} for r in rows]


def output(key, kind, data, blockers=(), reviewable=False):
    return {"item_key": key, "kind": kind, "data": data, "blockers": sorted(set(blockers)),
            "eligible": reviewable and not blockers}


def source_inventory(ctx):
    return [output("inventory", "inventory", {
        "sources": refs(ctx["sources"]), "profile": ctx["profile_ref"],
        "source_count": len(ctx["sources"]), "execution": "deterministic",
        "notice": "Declared source inventory is not proof of a complete ledger or statement population."
    }, [] if ctx["sources"] else ["NO_SOURCE_EVIDENCE"])]


def period_issues(value, profile, period):
    result = []
    if not day(period["start"]) <= day(value["date"]) <= day(period["end"]):
        result.append("OUTSIDE_PERIOD")
    if period["status"] == "locked":
        result.append("PERIOD_LOCKED")
    if value["currency"] != profile["currency"]:
        result.append("CURRENCY_MISMATCH")
    return result


def statement_checks(ctx,txs):
    profile,period=ctx['profile'],ctx['period'];issues={};packages=[]
    statements=[s for s in ctx['sources'] if s['kind']=='statement']
    for account in profile['card_accounts']:
        prior_revisions=[];prior_acceptance=None
        blockers=[];identity='not_supplied';continuity='no_prior_statement';provenance={'provenance':'not_supplied','supplier':None,'independent_verification':'not_performed'}
        matching=[s for s in statements if s['value']['account_id']==account and s['value']['period_start']==period['start'] and s['value']['period_end']==period['end']]
        excluded=[]
        if len(matching)!=1:
            blockers.append('STATEMENT_CONTROL_MISSING_OR_AMBIGUOUS')
            statement=None
        else:
            statement=matching[0];c=statement['value']
            provenance={'provenance':c['provenance'],'supplier':statement['actor'],'snapshot_id':statement['id'],'independent_verification':'not_performed'}
            included=[]
            for row in txs:
                t=row['value']
                if t['account_id']!=account:continue
                reason='pending' if t['status']!='posted' else 'currency' if t['currency']!=c['currency'] else 'outside_cycle' if not c['period_start']<=t['date']<=c['period_end'] else None
                if reason:excluded.append({'snapshot_id':row['id'],'source_key':row['source_key'],'reason':reason})
                else:included.append(row)
            totals={k:sum((money(r['value']['amount']) for r in included if r['value']['activity']==k),Decimal('0.00')) for k in c['totals']}
            if money(c['opening_balance'])+sum((money(v) for v in c['totals'].values()),Decimal('0.00'))!=money(c['closing_balance']):blockers.append('STATEMENT_ACTIVITY_BALANCE_BREAK')
            if c['currency']!=profile['currency'] or len(included)!=c['line_count'] or any(totals[k]!=money(c['totals'][k]) for k in totals):blockers.append('STATEMENT_CONTROL_MISMATCH')
            if c.get('line_ids') is None:
                if not any(r['value']['allow_without_line_ids'] for r in ctx.get('statement_rules',{}).get(account,[])):blockers.append('STATEMENT_LINE_IDENTITY_NOT_VERIFIED')
            else:
                identity='verified' if sorted(c['line_ids'])==sorted(r['value']['source_id'] for r in included) else 'mismatch'
                if identity=='mismatch':blockers.append('STATEMENT_LINE_POPULATION_MISMATCH')
            prior=[s for s in statements if s['value']['account_id']==account and s['value']['period_end']<c['period_start']]
            if ctx.get('prior_period'):prior=[s for s in prior if s['value']['period_end']==ctx['prior_period']['end']]
            if not prior and ctx.get('prior_period'):
                continuity='prior_period_statement_missing';blockers.append('STATEMENT_PRIOR_PERIOD_MISSING')
            if prior:
                continuity='verified'
                last=max(prior,key=lambda s:s['value']['period_end'])
                if money(last['value']['closing_balance'])!=money(c['opening_balance']):
                    continuity='mismatch';blockers.append('STATEMENT_OPENING_BALANCE_BREAK')
                prior_revisions=ctx.get('evidence_revisions',{}).get(last['source_key'],[])
                prior_acceptance=ctx.get('prior_statement_acceptances',{}).get(last['source_key'])
                if prior_revisions and not (prior_acceptance and prior_acceptance['accepted']):
                    continuity='prior_statement_revision_unaccepted';blockers.append('STATEMENT_PRIOR_REVISION_REQUIRES_REVIEW')
            if any((r['value']['activity'] in ('credit','payment') and money(r['value']['amount'])>0) or (r['value']['activity'] in ('fee','interest') and money(r['value']['amount'])<0) for r in included):blockers.append('STATEMENT_ACTIVITY_SIGN_INVALID')
        issues[account]=blockers
        packages.append(output('statement:'+account,'statement_workpaper',{'account_id':account,'evidence':refs([statement]) if statement else [],'prior_statement_revisions':prior_revisions,'prior_statement_acceptance':prior_acceptance,'statement_revisions':ctx.get('evidence_revisions',{}).get(statement['source_key'],[]) if statement else [],'unreconciled_population':excluded,'line_identity':identity,'opening_continuity':continuity,'statement_provenance':provenance,'execution':'deterministic','external_reconciliation':'not_verified'},blockers))
    return issues,packages


def entry_for(ctx,row,lines,capability,entry_type='standard',source_refs=None):
    return {'entity_id':ctx['profile'].get('entity_id'),'book_id':ctx['profile'].get('book_id'),'period_id':ctx['period']['period_id'],'date':row['value']['date'],'currency':row['value']['currency'],'lines':[dict(l,dimensions=l.get('dimensions',{})) for l in lines],'entry_type':entry_type,'reverses':None,'origin':{'capability':capability,'item_key':row['source_key'],'source_references':source_refs or refs([row])},'external_posting':'not_posted'}


def supporting_revisions(source,sources,revisions):
    if source['kind']=='transaction':
        t=source['value'];keys={s['source_key'] for s in sources if s['kind']=='receipt' and s['value']['account_id']==t['account_id'] and s['value']['transaction_source_id']==t['source_id']}
        keys.update(s['source_key'] for s in sources if s['kind']=='statement' and s['value']['account_id']==t['account_id'] and s['value']['period_start']<=t['date']<=s['value']['period_end'])
    elif source['kind']=='journal':keys=set(source['value']['supporting_keys'])
    else:keys=set()
    return [revision for key in sorted(keys) for revision in revisions.get(key,[])]


def card_duplicates(row,transactions,vendors):
    value=row['value']
    def vendor_key(tx):
        aliases=[v['id'] for v in vendors if normalize(tx['description']) and normalize(tx['description']) in [normalize(a) for a in v['aliases']]]
        return ('vendor',aliases[0]) if len(aliases)==1 else ('descriptor',normalize(tx['description']) or tx['description'])
    return [other for other in transactions if other['id']!=row['id'] and all(other['value'][field]==value[field] for field in ('account_id','date','amount','currency')) and vendor_key(other['value'])==vendor_key(value)]


def card_prepare(ctx):
    profile = ctx["profile"]
    period = ctx["period"]
    sources = ctx["sources"]
    txs = [s for s in sources if s["kind"] == "transaction"]
    receipts = [s for s in sources if s["kind"] == "receipt"]
    controls = [s for s in sources if s['kind']=='statement']
    account_issues,statement_workpapers=statement_checks(ctx,txs)
    control_details={workpaper['data']['account_id']:{key:workpaper['data'][key] for key in ('line_identity','opening_continuity','statement_provenance','prior_statement_revisions','prior_statement_acceptance')} for workpaper in statement_workpapers}
    result = []
    for row in txs:
        t = row["value"]
        profile=dict(ctx['profile'])
        item_rules=ctx.get('item_rules',{}).get(row['source_key'],[])
        profile['vendors']=[r['value'] for r in item_rules if r['kind']=='vendor_mapping']
        for rule in item_rules:
            if rule['kind']=='review_policy':profile['policies']=rule['value']
        blockers = period_issues(t, profile, period) + account_issues.get(t["account_id"], ["ACCOUNT_NOT_CONFIGURED"])
        if t["status"] == "pending":
            blockers.append("PENDING_TRANSACTION")
        if money(t["amount"]) < 0 and t["activity"] not in ("payment","transfer") or t["activity"] == "credit":
            blockers.append("CREDIT_REQUIRES_REVIEW")
        if money(t["amount"]) == 0:
            blockers.append("ZERO_AMOUNT")
        if t["activity"] != "purchase":
            blockers.append("NON_EXPENSE_REQUIRES_REVIEW")
        if t.get("requires_split"):
            blockers.append("SPLIT_REQUIRES_REVIEW")
        if t.get("supersedes_source_id") or ctx.get("source_transitions",{}).get(row["source_key"]) or ctx.get("unresolved_transitions",{}).get(row["source_key"]):
            blockers.append("SOURCE_TRANSITION_REQUIRES_REVIEW")
        if ctx.get("unresolved_transitions",{}).get(row["source_key"]):blockers.append("SOURCE_TRANSITION_UNRESOLVED")
        if ctx.get('source_claim_conflicts',{}).get(row['source_key']):blockers.append('SOURCE_CLAIM_CONFLICT')
        candidates = [v for v in profile["vendors"] if normalize(t["description"]) and normalize(t["description"]) in [normalize(a) for a in v["aliases"]]]
        vendor = candidates[0] if len(candidates) == 1 else None
        if not candidates:
            blockers.append("UNKNOWN_VENDOR")
        if len(candidates) > 1:
            blockers.append("AMBIGUOUS_VENDOR")
        category = vendor.get("category") if vendor else None
        account = next((a for a in profile["accounts"] if a["id"] == category and a["active"] and a["type"] == "expense"), None)
        if account is None:
            category = None
            blockers.append("UNKNOWN_CATEGORY")
        # A credit/payment/transfer/split is never proposed as an ordinary expense.
        if t["activity"] != "purchase" or money(t["amount"]) <= 0 or t.get("requires_split"):
            category = None
        population=card_duplicates(row,txs,profile['vendors'])
        resolutions=[d for d in ctx.get('dispositions',[]) if d['code']=='POSSIBLE_DUPLICATE' and d['choice'] in ('duplicate_of','source_replay') and d['payload'].get('duplicate_of')==row['source_key'] and any(r['source_key']==d['item_key'] for r in population)]
        duplicates=[r for r in population if not any(d['item_key']==r['source_key'] for d in resolutions)]
        if duplicates:
            blockers.append("POSSIBLE_DUPLICATE")
        docs = [r for r in receipts if r["value"]["transaction_source_id"] == t["source_id"] and r["value"]["account_id"] == t["account_id"]]
        matching=next((r["value"] for r in item_rules if r["kind"]=="receipt_matching"),{})
        if profile["policies"]["receipt_required"] and not docs and matching.get("statement_substitution") is not True:
            blockers.append("MISSING_RECEIPT")
        matching=next((r['value'] for r in item_rules if r['kind']=='receipt_matching'),{})
        if len(docs)>1 and matching.get('multiple_receipts') is not True:
            blockers.append('RECEIPT_MULTIPLE_POLICY_UNSET' if matching.get('multiple_receipts') is None else 'MULTIPLE_RECEIPTS_REQUIRE_REVIEW')
        for doc in docs:
            d = doc["value"]
            if d['currency']!=t['currency']:blockers.append('RECEIPT_CURRENCY_MISMATCH')
            window=matching.get('date_window_days');tolerance=matching.get('amount_tolerance')
            if abs((day(d['date'])-day(t['date'])).days)>(window or 0):blockers.append('RECEIPT_DATE_POLICY_UNSET' if window is None else 'RECEIPT_DATE_MISMATCH')
            if abs(money(d['amount'])-money(t['amount']))>(money(tolerance) if tolerance is not None else Decimal('0.00')):blockers.append('RECEIPT_AMOUNT_POLICY_UNSET' if tolerance is None else 'RECEIPT_AMOUNT_MISMATCH')
            accepted = [normalize(a) for a in vendor['aliases']] if vendor else [normalize(t['description'])]
            if normalize(d['vendor']) not in accepted:blockers.append('RECEIPT_VENDOR_POLICY_UNSET' if matching.get('vendor_method') is None else 'RECEIPT_VENDOR_MISMATCH')
            # Reuse of identical declared receipt content for another source is suspicious.
            if any(r["id"] != doc["id"] and r["value"]["content"] == d["content"] and
                   (r["value"]["transaction_source_id"], r["value"]["account_id"]) != (t["source_id"], t["account_id"]) for r in receipts):
                blockers.append("RECEIPT_REUSED")
        revised=supporting_revisions(row,sources,ctx.get('evidence_revisions',{}))
        if revised:blockers.append('EVIDENCE_REVISED_REQUIRES_REVIEW')
        applied=[d for d in ctx.get('dispositions',[]) if d['item_key']==row['source_key']]+resolutions
        lineage_keys={row['source_key']}|{ref['source_key'] for ref in ctx.get('source_transitions',{}).get(row['source_key'],[])}
        selections=[d for d in ctx.get('dispositions',[]) if d['choice']=='select_supersession_target' and d['item_key'] in lineage_keys]
        excluded=False;allocations=[];settlement=None
        for d in applied:
            if d['item_key']!=row['source_key']:continue
            if d['choice']!='refer_external' and d['code'] in blockers:blockers.remove(d['code'])
            if d['choice'] in ('code_category','confirm_vendor','standalone_credit','refund_of','code_fee','code_interest'):category=d['payload']['account_id']
            if d['choice']=='allocate':allocations=d['payload']['allocations'];category=None
            if d['choice'] in ('duplicate_of','source_replay'):excluded=True;blockers.append('DUPLICATE_EXCLUDED')
            if d['choice'] in ('settlement_of_card_liability','transfer'):
                settlement=d['payload']
                blockers=[c for c in blockers if c not in ('UNKNOWN_VENDOR','UNKNOWN_CATEGORY')]
            if d['choice'] in ('standalone_credit','refund_of') and t['activity']=='credit':blockers=[c for c in blockers if c!='NON_EXPENSE_REQUIRES_REVIEW']
        if any(row['source_key'] in c['owners'] for c in ctx.get('entry_claims',[])):blockers.append('SOURCE_ALREADY_HAS_ENTRY')
        entry=None
        liability=profile.get('card_liabilities',{}).get(t['account_id'])
        if not liability and t['account_id'] in profile['card_accounts']:blockers.append('CARD_LIABILITY_NOT_CONFIGURED')
        if not excluded and liability:
            amount=money(t['amount']);parts=allocations or ([{'account_id':category,'amount':str(abs(amount))}] if category else [])
            lines=[]
            if settlement:
                lines=[{'account_id':liability,'debit':str(abs(amount)) if amount<0 else '0.00','credit':'0.00' if amount<0 else str(abs(amount))},{'account_id':settlement['cash_account'],'debit':'0.00' if amount<0 else str(abs(amount)),'credit':str(abs(amount)) if amount<0 else '0.00'}]
            elif parts:
                lines=[{'account_id':l['account_id'],'debit':l['amount'] if amount>0 else '0.00','credit':'0.00' if amount>0 else l['amount']} for l in parts]
                lines.append({'account_id':liability,'debit':'0.00' if amount>0 else str(abs(amount)),'credit':str(abs(amount)) if amount>0 else '0.00'})
            if lines:
                entry=entry_for(ctx,row,lines,'banking.card_prepare','settlement' if settlement else 'standard')
                blockers+=validate_entry(entry,ctx['profile'],period)
        result.append(output(row["source_key"], "card_proposal", {
            "proposed_entry":entry,"evidence_revisions":revised,**control_details.get(t["account_id"],{}),
            "disposition_ids":sorted({d['id'] for d in applied+selections}),"excluded_duplicate":excluded,"allocations":allocations,"settlement":settlement,
            "transaction": t, "vendor": {"id": vendor["id"], "name": vendor["name"]} if vendor else None,
            "proposed_category": category, "duplicate_candidates": refs(duplicates), "duplicate_population":refs(population), "duplicate_evidence":refs([receipt for receipt in receipts if any(receipt["value"]["account_id"]==candidate["value"]["account_id"] and receipt["value"]["transaction_source_id"]==candidate["value"]["source_id"] for candidate in population)]),
            "source_claim_conflict": ctx.get("source_claim_conflicts",{}).get(row["source_key"]), "evidence": refs([row] + docs + controls)+ctx.get("source_transitions",{}).get(row["source_key"],[]), "profile": ctx["profile_ref"],
            "rationale": "Exact fictional alias proposal; human must validate business purpose and treatment.",
            "execution": "deterministic", "external_posting": "not_performed"
        }, blockers, True))
    return (result or [output("no-transactions", "card_proposal", {}, ["NO_TRANSACTIONS"])])+statement_workpapers


def journal_validate(ctx):
    profile = ctx["profile"]
    period = ctx["period"]
    journals = [s for s in ctx["sources"] if s["kind"] == "journal"]
    documents = {s["source_key"]: s for s in ctx["sources"] if s["kind"] == "document"}
    result = []
    for row in journals:
        j = row["value"]
        blockers = period_issues(j, profile, period)
        entry=entry_for(ctx,row,j['lines'],'gl.journal_validate',source_refs=refs([row])+j.get('origin_sources',[]))
        blockers+=validate_entry(entry,profile,period)
        if ctx.get('stale_origins',{}).get(row['source_key']):blockers.append('ORIGIN_SOURCE_SUPERSEDED')
        if any(row["source_key"] in c["owners"] for c in ctx.get("entry_claims",[])):blockers.append("SOURCE_ALREADY_HAS_ENTRY")
        debits=sum((money(l['debit']) for l in j['lines']),Decimal('0.00'));credits=sum((money(l['credit']) for l in j['lines']),Decimal('0.00'))
        signature=lambda v:(v['date'],v['currency'],sorted((l['account_id'],l['debit'],l['credit'],str(sorted(l.get('dimensions',{}).items()))) for l in v['lines']))
        duplicates=[r for r in journals if r['id']!=row['id'] and signature(r['value'])==signature(j)]
        if duplicates:blockers.append('POSSIBLE_DUPLICATE_JOURNAL')
        net={}
        for l in j['lines']:
            key=(l['account_id'],str(sorted(l.get('dimensions',{}).items())));net[key]=net.get(key,Decimal('0.00'))+money(l['debit'])-money(l['credit'])
        if net and not any(net.values()):blockers.append('NO_NET_LEDGER_EFFECT')
        if any(documents[k]['value']['document_type']!='journal_support' or row['source_key'] not in documents[k]['value'].get('journal_keys',[]) for k in j['supporting_keys'] if k in documents):blockers.append('JOURNAL_SUPPORT_NOT_BOUND')
        if not j["supporting_keys"] or any(key not in documents for key in j["supporting_keys"]):
            blockers.append("MISSING_JOURNAL_SUPPORT")
        revised=supporting_revisions(row,ctx['sources'],ctx.get('evidence_revisions',{}))
        if revised:blockers.append('EVIDENCE_REVISED_REQUIRES_REVIEW')
        applied=[d for d in ctx.get('dispositions',[]) if d['item_key']==row['source_key']]
        if any(d['code']=='EVIDENCE_REVISED_REQUIRES_REVIEW' and d['choice']=='revised_evidence_accepted' for d in applied):blockers=[c for c in blockers if c!='EVIDENCE_REVISED_REQUIRES_REVIEW']
        result.append(output(row["source_key"], "journal_proposal", {
            'evidence_revisions':revised,'disposition_ids':[d['id'] for d in applied],
            "proposed_entry":entry,"duplicate_candidates":refs(duplicates),"journal": j, "debit_total": str(debits), "credit_total": str(credits),
            "evidence": refs([row] + [documents[k] for k in j["supporting_keys"] if k in documents]),
            "profile": ctx["profile_ref"], "execution": "deterministic",
            "rationale": "Mechanical validation does not establish correct recognition, tax or business treatment.",
            "external_posting": "not_performed"
        }, blockers, True))
    return result or [output("no-journals", "journal_proposal", {}, ["NO_JOURNALS"])]


def close_readiness(ctx):
    documents=[s for s in ctx['sources'] if s['kind']=='document' and s['value'].get('period_id')==ctx['period']['period_id']]
    status=ctx.get('period_status',{'items':[],'quarantined_sources':[],'packages':[]})
    requirements=ctx['profile']['required_close_evidence'];missing=[];results=[]
    for requirement in requirements:
        if not isinstance(requirement,dict):
            missing.append(requirement);results.append({'requirement':{'type':'untyped','document_type':str(requirement)},'satisfied':False,'reason':'UNTYPED_REQUIREMENT'});continue
        r=requirement
        kind=r['type'];ok=False
        if kind=='workflow_outcome':
            relevant=[i for i in status['items'] if i['workflow']==r['workflow']]
            ok=bool(relevant) and all(i['status']=='approve' and not i['blockers'] for i in relevant)
        elif kind in ('reconciliation','tieout'):
            # These capabilities remain deferred. A document's label cannot assert
            # the verified workpaper outcome a future accounting module must emit.
            field='external_reconciliation' if kind=='reconciliation' else 'control_tie'
            ok=any(i['status']=='approve' and i['payload']['data'].get(field)=='verified' and (not r.get('account_id') or i['payload']['data'].get('account_id')==r['account_id']) for i in status['items'])
        elif kind=='document':ok=any(s['value']['document_type']==r['document_type'] for s in documents)
        if not ok:missing.append(r)
        results.append({'requirement':r,'satisfied':ok})
    blockers=['FINAL_CLOSE_SIGNOFF_REQUIRED','EXTERNAL_STEPS_UNVERIFIED']
    if missing:blockers.append('MISSING_CLOSE_EVIDENCE')
    if status['quarantined_sources'] or any(i['blockers'] or i['status'] in ('reject','revoke','disputed','stale') for i in status['items']):blockers.append('OPEN_PREPARATION_EXCEPTIONS')
    if any(not i['blockers'] and i['status']=='pending' for i in status['items']):blockers.append('UNREVIEWED_PREPARATION')
    return [output('close-checklist','close_readiness',{'required_evidence':requirements,'missing_evidence':missing,'requirements':results,'period_status':status,'evidence':refs(documents),'execution':'deterministic','status':'incomplete_readiness_only','final_close':'not_signed_off','external_posting':'not_verified','external_reconciliation':'not_verified'},blockers)]


def package_manifest(ctx):
    return [output("package-manifest", "package_manifest", {
        "input_fingerprint": ctx["fingerprint"], "execution": "deterministic",
        "source_scope": ctx["scope"], "model_calls": 0,
        "external_posting": "not_performed", "final_close": "not_signed_off"
    })]


CAPABILITIES = {c.id: c for c in (
    Capability("evidence.inventory", "shared", "fixture-demonstrated", "deterministic", source_inventory, reads=("$workflow",)),
    Capability("banking.card_prepare", "banking_reconciliation", "fixture-demonstrated", "deterministic", card_prepare, reads=("transaction","receipt","statement","statement_control"), profile_reads=("accounts","vendors","card_accounts","card_liabilities","currency","policies","entity_id","book_id"), requires_client_facts=("legal_entity","accounting_framework","accounting_basis","entity_id","book_id"),lookback="prior_statement",rule_reads=("vendor_mapping","receipt_matching","statement_policy"),rule_date_sources=("transaction",)),
    Capability("gl.journal_validate", "general_ledger", "fixture-demonstrated", "deterministic", journal_validate, reads=("journal","document"), profile_reads=("accounts","currency","policies","entity_id","book_id"), requires_client_facts=("legal_entity","accounting_framework","accounting_basis","entity_id","book_id"),rule_date_sources=("journal",)),
    Capability("close.readiness", "month_end_close", "fixture-demonstrated", "deterministic", close_readiness, reads=("document",), profile_reads=("required_close_evidence",),rule_reads=("close_checklist",)),
    Capability("package.manifest", "shared", "fixture-demonstrated", "deterministic", package_manifest),
    Capability("gl.account_maintenance", "general_ledger", "deferred", "human"),
    Capability("gl.post", "general_ledger", "deferred", "human", effect="write"),
    Capability("ap.bills_expenses_payments", "accounts_payable", "deferred", "human", effect="write"),
    Capability("ar.invoices_collections_application_aging", "accounts_receivable", "deferred", "human"),
    Capability("banking.match_transfer_reconcile", "banking_reconciliation", "deferred", "human"),
    Capability("close.accruals_adjustments_signoff", "month_end_close", "deferred", "human"),
    Capability("reporting.statements_management_variances_insights", "financial_reporting", "deferred", "human"),
)}

WORKFLOWS = {w.id: w for w in (
    Workflow("card_preparation", "banking_reconciliation", (
        Step("inventory", "evidence.inventory"),
        Step("prepare", "banking.card_prepare", ("inventory",)),
        Step("package", "package.manifest", ("prepare",)))),
    Workflow("journal_preparation", "general_ledger", (
        Step("inventory", "evidence.inventory"),
        Step("validate", "gl.journal_validate", ("inventory",)),
        Step("package", "package.manifest", ("validate",)))),
    Workflow("close_readiness", "month_end_close", (
        Step("inventory", "evidence.inventory"),
        Step("checklist", "close.readiness", ("inventory",)),
        Step("package", "package.manifest", ("checklist",)))),
)}
for _workflow in WORKFLOWS.values():
    _workflow.validate()
