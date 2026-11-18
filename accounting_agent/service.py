"""Trusted execution/approval boundary shared by every accounting module."""
import json
import secrets
import math
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from .core import (Actor, ControlError, SHARED_CONTROLS, canonical, day, digest,
                   instant, normalize, require_keys, text_field, utcnow)
from .modules import CAPABILITIES, WORKFLOWS, validate_source
from .storage import Store
from .controls import AccountingControls
from .source_control import SourceControl
from .exceptions import ExceptionControls
from .packages import PackageControls


class AccountingOS(AccountingControls,SourceControl,ExceptionControls,PackageControls):
    def __init__(self, path, allowed_scopes, environment="local", mode="demo"):
        if environment != "local" or mode != "demo":
            raise ControlError("Only local/demo is implemented; hosted demo identity is forbidden", 403)
        self.allowed_scopes = frozenset(allowed_scopes)
        if not self.allowed_scopes or any(not s.endswith("/local") for s in self.allowed_scopes):
            raise ControlError("An explicit local client allowlist is required", 403)
        self.store = Store(path)
        # Conservative code/config lineage: code changes require renewed preparation/review.
        self.handler_hash = digest({name: (Path(__file__).parent/name).read_text() for name in ("core.py","modules.py")})

    def authorize(self, actor, roles=("preparer", "reviewer", "worker")):
        if not isinstance(actor, Actor) or actor.environment != "local" or actor.scope not in self.allowed_scopes or actor.role not in roles:
            raise ControlError("Client scope or role denied", 403)

    def client(self, db, actor):
        self.authorize(actor)
        row = db.execute("SELECT * FROM clients WHERE scope=?", (actor.scope,)).fetchone()
        if not row:
            raise ControlError("Client not configured", 404)
        return row

    def validate_profile(self, actor, profile):
        require_keys(profile, {"schema_version", "version", "synthetic", "organization_id", "client_id", "name", "approval_status", "notice", "legal_entity", "accounting_framework", "accounting_basis", "external_company_id", "currency", "accounts", "card_accounts", "vendors", "customers", "dimensions", "policies", "procedures", "historical_decisions", "credentials_reference", "systems", "required_close_evidence"}, {"profile_class","fact_waivers","entity_id","book_id","card_liabilities"})
        if (profile["synthetic"] is not True or profile["approval_status"] != "approved_demo_only" or
                profile["organization_id"] != actor.organization or profile["client_id"] != actor.client or
                profile["credentials_reference"] is not None):
            raise ControlError("Only scoped synthetic profiles without credentials are permitted", 403)
        if profile.get('profile_class') not in ('synthetic_demo','client_sample') or not isinstance(profile.get('fact_waivers'),dict):
            raise ControlError('Explicit profile_class and fact_waivers required')
        for name in ("name", "version", "external_company_id", "currency"):
            text_field(profile[name], name)
        require_keys(profile["policies"], {"receipt_required", "review", "model_review_required"})
        if (profile["policies"]["review"] != "independent_human" or
                type(profile["policies"]["receipt_required"]) is not bool or type(profile["policies"]["model_review_required"]) is not bool):
            raise ControlError("Unsupported review policy")
        for field in ("accounts", "vendors", "card_accounts", "customers", "dimensions", "procedures", "historical_decisions", "required_close_evidence"):
            if not isinstance(profile[field], list) or len(profile[field]) > 1000:
                raise ControlError("Invalid profile collection: " + field)
        account_ids = set()
        for account in profile["accounts"]:
            require_keys(account, {"id", "type", "active"})
            text_field(account["id"], "account id")
            if account["id"] in account_ids or type(account["active"]) is not bool or account["type"] not in ("asset", "liability", "equity", "revenue", "expense"):
                raise ControlError("Invalid or repeated account")
            account_ids.add(account["id"])
        vendor_ids = set()
        for vendor in profile["vendors"]:
            require_keys(vendor, {"id", "name", "aliases", "category"})
            for field in ("id", "name"):
                text_field(vendor[field], "vendor " + field)
            if vendor["id"] in vendor_ids or not isinstance(vendor["aliases"], list) or not vendor["aliases"] or len(vendor["aliases"]) > 100:
                raise ControlError("Invalid vendor aliases/identity")
            for alias in vendor["aliases"]:
                text_field(alias, "vendor alias")
                if not normalize(alias):
                    raise ControlError("Vendor alias must contain letters or digits")
            if vendor["category"] is not None and vendor["category"] not in account_ids:
                raise ControlError("Vendor category must reference a configured account")
            vendor_ids.add(vendor["id"])
        self.validate_rule("close_checklist",profile["required_close_evidence"])
        for field in ("card_accounts", "procedures"):
            for value in profile[field]:
                text_field(value, field)
            if len(set(profile[field])) != len(profile[field]):
                raise ControlError("Repeated profile value")
        if not set(profile["procedures"]).issubset(WORKFLOWS):
            raise ControlError("Profile references an unavailable workflow")
        # These are knowledge placeholders, not executable policy in this slice.
        if profile["customers"] or profile["dimensions"] or profile["historical_decisions"]:
            raise ControlError("Customer/dimension/decision activation is deferred; do not silently ignore it")

    def onboard(self, actor, profile, effective_from=None, effective_to=None):
        self.authorize(actor, ("preparer",))
        self.validate_profile(actor, profile)
        with self.store.transaction() as db:
            db.execute("INSERT OR IGNORE INTO clients(scope,organization,client,environment,generation) VALUES(?,?,?,?,0)",
                       (actor.scope, actor.organization, actor.client, actor.environment))
            old = self.store.latest(db, actor.scope, "profile")
            legacy_without_period=dict(old[0]["value"]) if old else {}
            legacy_without_period.pop("period",None)
            if old and old[0]["hash"] != digest(profile) and old[0]["value"]["version"] == profile["version"] and digest(legacy_without_period)!=digest(profile):
                raise ControlError("A policy change requires a new explicit version", 409)
            sid, changed = self.store.snapshot(db, actor.scope, "profile", "profile", profile, actor.id)
            if not db.execute('SELECT 1 FROM profile_proposals WHERE snapshot_id=?',(sid,)).fetchone():
                latest_period=db.execute('SELECT start,end,status FROM periods WHERE scope=? ORDER BY start DESC LIMIT 1',(actor.scope,)).fetchone()
                start=effective_from or ((day(latest_period['end'])+timedelta(days=1)).isoformat() if latest_period and latest_period['status']=='locked' else latest_period['start'] if latest_period else '0001-01-01');day(start)
                db.execute('INSERT INTO profile_proposals VALUES(?,?,?,?)',(actor.scope,sid,start,effective_to))
                previous=db.execute('SELECT profile_id FROM clients WHERE scope=?',(actor.scope,)).fetchone()['profile_id']
                old_profile=json.loads(db.execute('SELECT payload FROM snapshots WHERE id=?',(previous,)).fetchone()['payload']) if previous else {}
                values=[('vendor_mapping',v['id'],v) for v in profile['vendors']]+[('review_policy','review',profile['policies']),('close_checklist','close',profile['required_close_evidence'])]
                for kind,key,value in values:
                    current=db.execute("SELECT r.* FROM policy_rules r JOIN rule_decisions d ON d.rule_id=r.id WHERE r.scope=? AND r.kind=? AND r.rule_key=? AND d.decision='approve' ORDER BY r.id DESC LIMIT 1",(actor.scope,kind,key)).fetchone()
                    active=next((r for r in self.rules_at(db,actor.scope,start) if r['kind']==kind and r['rule_key']==key),None)
                    if not active or active['value']!=value:
                        self._propose_rule(db,actor,kind,key,value,start,effective_to,None,current['id'] if current else None,[],sid)
                self.store.audit(db,actor.scope,actor.id,'profile_proposed',{'snapshot_id':sid,'effective_from':start})
            return sid

    def period(self, db, actor, period_id=None):
        if period_id is None:
            row=db.execute("SELECT * FROM periods WHERE scope=? ORDER BY start DESC LIMIT 1",(actor.scope,)).fetchone()
        else:
            row=db.execute("SELECT * FROM periods WHERE scope=? AND period_id=?",(actor.scope,period_id)).fetchone()
        if not row:
            raise ControlError("Accounting period not configured",409)
        return dict(row)

    def open_period(self, actor, period_id, start, end, reason):
        self.authorize(actor,("reviewer",))
        if actor.kind!='human':
            raise ControlError("Period administration requires a human reviewer",403)
        text_field(period_id,"period id");text_field(reason,"period reason",2000)
        if day(start)>day(end):raise ControlError("Invalid period range")
        with self.store.transaction() as db:
            self.client(db,actor)
            existing=db.execute("SELECT * FROM periods WHERE scope=? AND period_id=?",(actor.scope,period_id)).fetchone()
            if existing:
                if existing['start']==start and existing['end']==end:return period_id
                raise ControlError("Period identity already binds another range",409)
            if db.execute("SELECT 1 FROM periods WHERE scope=? AND start<=? AND end>=?",(actor.scope,end,start)).fetchone():
                raise ControlError("Accounting periods may not overlap",409)
            db.execute("INSERT INTO periods VALUES(?,?,?,?, 'open',?,?,?)",(actor.scope,period_id,start,end,actor.id,utcnow(),reason))
            db.execute("INSERT INTO period_history(scope,period_id,status,actor,created,reason) VALUES(?,?,'open',?,?,?)",(actor.scope,period_id,actor.id,utcnow(),reason))
            for source in self.store.latest(db,actor.scope):
                if source['kind'] in ('profile','batch'):continue
                b=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(source['id'],)).fetchone()
                if not b or b['reason']=='UNASSIGNED_ACCOUNTING_PERIOD':
                    hint=db.execute('SELECT period_hint FROM source_metadata WHERE snapshot_id=?',(source['id'],)).fetchone()
                    self.bind_source(db,actor,source['id'],source['value'],hint['period_hint'] if hint else None)
            self.store.audit(db,actor.scope,actor.id,"accounting_period_opened",{"period_id":period_id,"start":start,"end":end,"reason":reason})
        return period_id

    def change_period_status(self,actor,period_id,status,reason,acknowledgement=None):
        self.authorize(actor,("reviewer",))
        if actor.kind!='human':raise ControlError("Period administration requires a human reviewer",403)
        text_field(reason,"period reason",2000)
        with self.store.transaction() as db:
            p=self.period(db,actor,period_id)
            self.require_grant(db,actor,"lock")
            contributors={r['actor'] for r in db.execute("SELECT actor FROM runs WHERE scope=? AND period_id=?",(actor.scope,period_id))}
            contributors.update(r['actor'] for r in db.execute("SELECT DISTINCT s.actor FROM snapshots s JOIN source_periods b ON b.snapshot_id=s.id WHERE b.scope=? AND b.period_id=?",(actor.scope,period_id)))
            contributors.update(r['actor'] for r in db.execute('SELECT DISTINCT c.actor FROM artifact_contributors c JOIN artifacts a ON a.id=c.artifact_id JOIN runs r ON r.id=a.run_id WHERE c.scope=? AND r.period_id=?',(actor.scope,period_id)))
            if actor.id in contributors:raise ControlError("Independent period administration required",403)
            if acknowledgement:self.store.audit(db,actor.scope,actor.id,'unsettled_period_acknowledged',{'period_id':period_id,'acknowledgement':acknowledgement})
            if p['status']==status:raise ControlError("Period already has that status",409)
            if status=='open' and p['status']!='locked':raise ControlError("Only a locked period can be reopened",409)
            if status=='locked':
                outcomes=self.period_outcomes(db,actor,period_id)
                unsettled=[a for a in outcomes['items'] if a['status']!='approve']
                if unsettled and not acknowledgement:raise ControlError('Unsettled preparation requires explicit acknowledgement',409)
                if acknowledgement:text_field(acknowledgement,'acknowledgement',2000)
                for r in db.execute("SELECT * FROM runs WHERE scope=? AND period_id=?",(actor.scope,period_id)).fetchall():
                    if r['status'] in ('awaiting_review','prepared_with_exceptions') and self._current(db,actor,r):
                        db.execute("INSERT OR IGNORE INTO frozen_runs VALUES(?,?,?)",(actor.scope,period_id,r['id']))
                    elif r['status'] in ('queued','running'):
                        self.hold_run(db,actor,r,'period_locked')
            else:
                db.execute("DELETE FROM frozen_runs WHERE scope=? AND period_id=?",(actor.scope,period_id))
                db.execute("UPDATE periods SET status='open' WHERE scope=? AND period_id=?",(actor.scope,period_id))
                # Re-evaluate quarantined moves only after the original lock is lifted.
                candidates=self.store.latest(db,actor.scope,include_removed=True)
                # Admit terminal replacements first; their ancestors never enter the
                # destination population, even transiently in the binding history.
                candidates.sort(key=lambda s:(s['kind']!='transaction',-len(self.supersession_refs(db,actor.scope,s['id'])),-s['id']))
                for s in candidates:
                    if s['kind'] in ('profile','batch'):continue
                    b=db.execute("SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1",(s['id'],)).fetchone()
                    live=db.execute('SELECT 1 FROM source_heads WHERE scope=? AND snapshot_id=? AND removed=0',(actor.scope,s['id'])).fetchone()
                    if not live and not (b and b['reason']=='LATE_ACTIVITY_IN_LOCKED_PERIOD'):continue
                    if b and b['period_id']==period_id and not b['admitted']:
                        move=db.execute("SELECT * FROM source_moves WHERE scope=? AND snapshot_id=? AND blocked=1 ORDER BY id DESC LIMIT 1",(actor.scope,s['id'])).fetchone()
                        self.bind_source(db,actor,s['id'],s['value'],move['to_period_id'] if move else period_id)
            db.execute("UPDATE periods SET status=?,changed_by=?,changed_at=?,reason=? WHERE scope=? AND period_id=?",(status,actor.id,utcnow(),reason,actor.scope,period_id))
            db.execute("INSERT INTO period_history(scope,period_id,status,actor,created,reason) VALUES(?,?,?,?,?,?)",(actor.scope,period_id,status,actor.id,utcnow(),reason))
            self.store.audit(db,actor.scope,actor.id,"accounting_period_"+status,{"period_id":period_id,"reason":reason,"acknowledgement":acknowledgement})

    def lock_period(self,actor,period_id,reason,acknowledgement=None):
        self.change_period_status(actor,period_id,'locked',reason,acknowledgement)

    def reopen_period(self,actor,period_id,reason):
        self.change_period_status(actor,period_id,'open',reason)

    def bind_source(self,db,actor,snapshot_id,value,requested_period,allow_locked_release=False):
        governing_date=value.get('date');parent_blocked=None
        if value.get('transaction_source_id'):
            key=value['account_id']+':'+value['transaction_source_id']
            transaction=db.execute("SELECT s.* FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.scope=? AND h.kind='transaction' AND h.source_key=? AND h.removed=0",(actor.scope,key)).fetchone()
            if transaction:
                governing_date=json.loads(transaction['payload'])['date']
                binding=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(transaction['id'],)).fetchone()
                if binding and not binding['admitted'] and binding['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD':parent_blocked=binding
        if governing_date:
            p=db.execute('SELECT * FROM periods WHERE scope=? AND start<=? AND end>=?',(actor.scope,governing_date,governing_date)).fetchone()
        elif value.get('period_start'):
            p=db.execute('SELECT * FROM periods WHERE scope=? AND start=? AND end=?',(actor.scope,value['period_start'],value['period_end'])).fetchone()
        elif requested_period:
            p=db.execute('SELECT * FROM periods WHERE scope=? AND period_id=?',(actor.scope,requested_period)).fetchone()
        else:
            periods=db.execute('SELECT * FROM periods WHERE scope=?',(actor.scope,)).fetchall();p=periods[0] if len(periods)==1 else None
        source=db.execute('SELECT kind,source_key FROM snapshots WHERE id=? AND scope=?',(snapshot_id,actor.scope)).fetchone()
        latest=db.execute('SELECT * FROM source_periods WHERE scope=? AND snapshot_id=? ORDER BY id DESC LIMIT 1',(actor.scope,snapshot_id)).fetchone()
        prior=self.source_origin(db,actor.scope,snapshot_id)
        link=self.supersession_link(db,actor.scope,snapshot_id)
        if parent_blocked:prior=parent_blocked
        if source['kind'] in ('transaction','receipt'):
            held=self.card_locked_hold(db,actor,source['kind'],source['source_key'])
            if held:prior=held
        old_period=self.period(db,actor,prior['period_id']) if prior and prior['period_id'] else None
        moved=old_period is not None and (p is None or p['period_id']!=old_period['period_id'])
        blocked=bool(moved and old_period['status']=='locked')
        if blocked and allow_locked_release:
            # A selected target's locked ancestry remains quarantined even
            # when the person may release the former target's hold.
            ancestors=self.supersession_refs(db,actor.scope,snapshot_id)
            selected_origin=self.source_origin(db,actor.scope,ancestors[0]['snapshot_id']) if ancestors else parent_blocked
            if not selected_origin or not selected_origin['period_id'] or self.period(db,actor,selected_origin['period_id'])['status']!='locked':blocked=False
        if p and latest and latest['admitted'] and latest['period_id']==p['period_id'] and not blocked:
            self.apply_supersession(db,actor,snapshot_id)
            return
        reason='SOURCE_MOVED_FROM_LOCKED_PERIOD' if blocked else 'UNASSIGNED_ACCOUNTING_PERIOD' if p is None else 'LATE_ACTIVITY_IN_LOCKED_PERIOD' if p['status']=='locked' else None
        bound_period=old_period['period_id'] if blocked else p['period_id'] if p else None
        if latest and latest['period_id']==bound_period and latest['reason']==reason and bool(latest['admitted'])==(reason is None):return
        if moved:
            origin_keys={source['source_key']}|{ref['source_key'] for ref in self.supersession_refs(db,actor.scope,snapshot_id)}
            had_approval=any(self.source_had_approval(db,actor.scope,key,old_period['period_id']) for key in origin_keys)
            db.execute('INSERT INTO source_moves(scope,snapshot_id,from_period_id,to_period_id,blocked,had_approval,created) VALUES(?,?,?,?,?,?,?)',(actor.scope,snapshot_id,old_period['period_id'],p['period_id'] if p else None,int(blocked),int(had_approval),utcnow()))
            self.store.audit(db,actor.scope,actor.id,'source_period_move',{'snapshot_id':snapshot_id,'from_period_id':old_period['period_id'],'to_period_id':p['period_id'] if p else None,'blocked':blocked,'had_recorded_approval':had_approval,'supersession_link_id':link['id'] if link else None})
        db.execute('INSERT INTO source_periods(scope,snapshot_id,period_id,admitted,reason,created) VALUES(?,?,?,?,?,?)',(actor.scope,snapshot_id,bound_period,int(reason is None),reason,utcnow()))
        if blocked:self.source_approval_events(db,actor,source['source_key'],snapshot_id,'APPROVED_SOURCE_REVISED')
        if reason:self.store.audit(db,actor.scope,actor.id,'source_period_exception',{'snapshot_id':snapshot_id,'period_id':bound_period,'code':reason})
        else:self.apply_supersession(db,actor,snapshot_id)

    def period_sources(self,db,actor,period_id):
        rows=db.execute("SELECT s.* FROM snapshots s JOIN source_periods b ON b.snapshot_id=s.id WHERE s.scope=? AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=s.id) AND b.period_id=? AND b.admitted=1 ORDER BY s.id",(actor.scope,period_id)).fetchall()
        if self.period(db,actor,period_id)['status']!='locked':
            newest={(s['kind'],s['source_key']):s['id'] for s in self.store.latest(db,actor.scope)}
            rows=[r for r in rows if newest.get((r['kind'],r['source_key']))==r['id']]
        latest={}
        for r in rows:latest[(r['kind'],r['source_key'])]=dict(r,value=json.loads(r['payload']))
        return list(latest.values())

    def context(self, db, actor, period_id=None, workflow_id=None):
        client = self.client(db, actor)
        selected = self.period(db,actor,period_id) if db.execute("SELECT 1 FROM periods WHERE scope=?",(actor.scope,)).fetchone() else None
        profile_row=self.approved_profile(db,actor,selected['start'] if selected else None,allow_proposed=workflow_id is None)
        profile=json.loads(profile_row['payload'])
        sources = self.period_sources(db,actor,selected["period_id"]) if selected else []
        transitions={s['source_key']:self.supersession_refs(db,actor.scope,s['id']) for s in sources if s['kind'] not in ('profile','batch')}
        transitions={k:v for k,v in transitions.items() if v}
        unresolved_transitions={}
        for source in sources:
            claim=self.pending_claim(db,actor.scope,source['kind'],source['source_key'])
            if claim:unresolved_transitions[source['source_key']]=claim
        source_claim_conflicts=self.card_claim_conflicts(db,actor,selected,sources)
        claims=[];owners={};heads={};stale_origins={}
        for src in sources:
            identity=self.source_identity(db,actor.scope,src['id']);heads[identity]=src
            if src['kind']=='journal' or (src['kind']=='transaction' and src['value']['account_id'] in profile['card_accounts']):owners.setdefault(identity,set()).add((src['kind'],src['source_key']))
        for j in sources:
            if j['kind']=='journal':
                for ref in j['value'].get('origin_sources',[]):
                    identity=self.source_identity(db,actor.scope,ref['snapshot_id'])
                    owners.setdefault(identity,set()).add(('journal',j['source_key']))
                    current=heads.get(identity)
                    if current is None or current['id']!=ref['snapshot_id'] or current['hash']!=ref['hash']:
                        stale_origins.setdefault(j['source_key'],[]).append(dict(ref,current_snapshot_id=current['id'] if current else None))
        for identity,keys in owners.items():
            if len(keys)>1:
                source=heads.get(identity)
                claims.append({'source_kind':identity[0],'source_key':identity[1],'snapshot_id':source['id'] if source else None,'hash':source['hash'] if source else None,'owners':sorted({key for _,key in keys})})
        rule_kinds={'vendor_mapping','review_policy','receipt_matching','close_checklist','statement_policy'}
        rule_sources=sources
        if workflow_id in WORKFLOWS:
            rule_caps=[CAPABILITIES[step.capability] for step in WORKFLOWS[workflow_id].steps]
            rule_kinds={'review_policy'}|{k for cap in rule_caps for k in cap.rule_reads}
            rule_source_kinds={k for cap in rule_caps for k in cap.rule_date_sources}
            rule_sources=[src for src in sources if src['kind'] in rule_source_kinds]
        item_rules={};applied={}
        for source in rule_sources:
            date=source['value'].get('date') or (selected['start'] if selected else '0001-01-01')
            rules=[r for r in self.rules_at(db,actor.scope,date,source['source_key']) if r['kind'] in rule_kinds and r['kind']!='statement_policy'];item_rules[source['source_key']]=rules
            for rule in rules:applied[rule['id']]=rule
        if not rule_sources:
            for rule in self.rules_at(db,actor.scope,selected['start'] if selected else '0001-01-01'):
                if rule['kind'] in rule_kinds:applied[rule['id']]=rule
        for rule in self.rules_at(db,actor.scope,selected['start'] if selected else '0001-01-01'):
            if rule['kind']=='review_policy':profile['policies']=rule['value']
            if rule['kind']=='close_checklist':profile['required_close_evidence']=rule['value']
        prior_period=None;statement_rules={}
        if workflow_id=='card_preparation' and selected:
            previous=db.execute('SELECT * FROM periods WHERE scope=? AND end<? ORDER BY end DESC LIMIT 1',(actor.scope,selected['start'])).fetchone()
            if previous:prior_period={k:previous[k] for k in ('period_id','start','end')}
            prior=[]
            for prior_row in db.execute('SELECT period_id FROM periods WHERE scope=? AND end<? ORDER BY end',(actor.scope,selected['start'])).fetchall():
                prior.extend(s for s in self.period_sources(db,actor,prior_row['period_id']) if s['kind']=='statement')
            latest={}
            for row in sorted(prior,key=lambda s:s['value']['period_end']):latest[row['value']['account_id']]=row
            sources+=list(latest.values())
            for account in profile['card_accounts']:
                statement_rules[account]=[r for r in self.rules_at(db,actor.scope,selected['start'],'statement:'+account) if r['kind']=='statement_policy']
                for rule in statement_rules[account]:applied[rule['id']]=rule
        sections=set(profile)
        capabilities=[]
        if workflow_id in WORKFLOWS:
            caps=[CAPABILITIES[s.capability] for s in WORKFLOWS[workflow_id].steps]
            kinds={k for c in caps for k in c.reads if k!='$workflow'}
            sources=[s for s in sources if s['kind'] in kinds]
            sections={'policies','profile_class','fact_waivers','legal_entity','accounting_framework','accounting_basis','entity_id','book_id'} | {key for c in caps for key in c.profile_reads}
            capabilities=[{'id':c.id,'version':c.version,'reads':c.reads,'profile_reads':c.profile_reads,'lookback':c.lookback,'rule_reads':c.rule_reads,'rule_date_sources':c.rule_date_sources} for c in caps]
        period_status=self.period_outcomes(db,actor,selected["period_id"]) if workflow_id=="close_readiness" and selected else None
        evidence_revisions=self.evidence_revisions(db,actor.scope,sources)
        dispositions=self.active_dispositions(db,actor,workflow_id,selected["period_id"],sources,evidence_revisions) if selected and workflow_id else []
        selection_history=self.card_selection_history(db,actor,workflow_id,sources)
        prior_acceptances=self.prior_statement_acceptances(db,actor,prior_period,sources) if workflow_id=='card_preparation' else {}
        manifest = {"selection_history":selection_history,"source_claim_conflicts":source_claim_conflicts,"prior_statement_acceptances":prior_acceptances,"unresolved_transitions":unresolved_transitions,"prior_period":prior_period,"statement_rules":statement_rules,"evidence_revisions":evidence_revisions,"stale_origins":stale_origins,"source_transitions":transitions,"period_status":period_status,"entry_claims":claims,"dispositions":dispositions,"period": {k:selected[k] for k in ("period_id","start","end")} if selected else None,
                    "profile_sections": {k:profile.get(k) for k in sorted(sections)},
                    "workflow_permitted": workflow_id in profile['procedures'] if workflow_id else None,
                    "sources": [{"kind":s['kind'],"key":s['source_key'],"snapshot_id":s['id'],"hash":s['hash']} for s in sources],
                    "rules":[{"id":r["id"],"version":r["version"],"value":r["value"]} for r in sorted(applied.values(),key=lambda r:r["id"])], "capabilities":capabilities,"handler_hash":self.handler_hash,"shared_controls":SHARED_CONTROLS}
        return {"period": selected, "scope": actor.scope, "generation": client["generation"], "profile": profile,
                "profile_ref": {"snapshot_id": profile_row["id"], "hash": profile_row["hash"], "version": profile["version"], "actor": profile_row["actor"]},
                "selection_history":selection_history,"source_claim_conflicts":source_claim_conflicts,"prior_statement_acceptances":prior_acceptances,"unresolved_transitions":unresolved_transitions,"prior_period":prior_period,"statement_rules":statement_rules,"evidence_revisions":evidence_revisions,"stale_origins":stale_origins,"source_transitions":transitions,"period_status":period_status,"entry_claims":claims,"dispositions":dispositions,"rules":list(applied.values()),"item_rules":item_rules,"sources": sources, "manifest":manifest, "fingerprint": digest(manifest)}

    def intake(self, actor, packet):
        self.authorize(actor, ("preparer",))
        require_keys(packet, {"synthetic", "organization_id", "client_id", "external_company_id", "batch_id", "sources"}, {"period_id"})
        if packet["synthetic"] is not True or packet["organization_id"] != actor.organization or packet["client_id"] != actor.client:
            raise ControlError("Synthetic source scope mismatch", 403)
        text_field(packet["batch_id"], "batch_id")
        if not isinstance(packet["sources"], list) or not 1 <= len(packet["sources"]) <= 1000:
            raise ControlError("Intake requires 1–1000 sources")
        if len(canonical(packet).encode()) > 1024 * 1024:
            raise ControlError("Intake exceeds 1 MiB limit", 413)
        seen = set()
        for source in packet["sources"]:
            require_keys(source, {"kind", "key", "data"}, {"as_of","source_system","tombstone","removal_reason","supersedes"})
            text_field(source["key"], "source key")
            validate_source(source["kind"], source["data"])
            if source["kind"] == "transaction" and source["key"] != source["data"]["account_id"] + ":" + source["data"]["source_id"]:
                raise ControlError("Transaction key must retain account and source identity")
            identity = (source["kind"], source["key"])
            if identity in seen:
                raise ControlError("Repeated source identity in batch")
            seen.add(identity)
        with self.store.transaction() as db:
            ctx = self.context(db, actor)
            if packet["external_company_id"] != ctx["profile"]["external_company_id"]:
                raise ControlError("External company scope mismatch", 403)
            old = db.execute("SELECT hash FROM snapshots WHERE scope=? AND kind='batch' AND source_key=?", (actor.scope, packet["batch_id"])).fetchone()
            if old:
                if old["hash"] != digest(packet):
                    raise ControlError("Batch id already binds different bytes; use a new batch id", 409)
                for source in packet['sources']:
                    head=db.execute('SELECT snapshot_id FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(actor.scope,source['kind'],source['key'])).fetchone()
                    if head:
                        binding=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(head['snapshot_id'],)).fetchone()
                        if binding and binding['reason']=='UNASSIGNED_ACCOUNTING_PERIOD':
                            actual=db.execute('SELECT payload FROM snapshots WHERE id=?',(head['snapshot_id'],)).fetchone()
                            self.bind_source(db,actor,head['snapshot_id'],json.loads(actual['payload']),packet.get('period_id'))
                return {"changed": False, "generation": ctx["generation"], "replay": True}
            size = db.execute("SELECT COALESCE(SUM(length(CAST(payload AS BLOB))),0) FROM snapshots WHERE scope=?", (actor.scope,)).fetchone()[0]
            if size + len(canonical(packet).encode()) * 2 > 10 * 1024 * 1024:
                raise ControlError("Synthetic client evidence quota exceeded", 413)
            for source in packet['sources']:
                if source['kind']=='journal':
                    for ref in source['data'].get('origin_sources',[]):
                        found=db.execute('SELECT hash,source_key FROM snapshots WHERE scope=? AND id=?',(actor.scope,ref.get('snapshot_id'))).fetchone()
                        if not found or found['hash']!=ref.get('hash') or found['source_key']!=ref.get('source_key'):raise ControlError('Journal origin outside scoped evidence',403)
            self.store.snapshot(db, actor.scope, "batch", packet["batch_id"], packet, actor.id)
            changed = False
            for source in packet["sources"]:
                sid,is_new=self.source_revision(db,actor,source,packet)
                changed = changed or is_new
            if changed:
                self.resolve_pending_supersessions(db,actor)
                self.rebind_chained_sources(db,actor,packet.get('period_id'))
                for receipt in self.store.latest(db,actor.scope,'receipt'):
                    self.bind_source(db,actor,receipt['id'],receipt['value'],packet.get('period_id'))
                db.execute("UPDATE clients SET generation=generation+1 WHERE scope=?", (actor.scope,))
            self.package_changes(db,actor)
            self.store.audit(db, actor.scope, actor.id, "source_intake", {"batch_id": packet["batch_id"], "source_count": len(packet["sources"]), "changed": changed, "relevant_preparations_must_recheck": changed})
            result={"changed": changed, "generation": ctx["generation"] + int(changed), "replay": False}
            clock=db.execute('SELECT simulated_now FROM demo_clock WHERE scope=?',(actor.scope,)).fetchone()
            waiting=db.execute("SELECT 1 FROM occurrences WHERE scope=? AND status='awaiting_evidence'",(actor.scope,)).fetchone()
        if changed and waiting and clock:self.tick(actor,clock['simulated_now'])
        return result

    def definition_hash(self, workflow):
        return digest(asdict(workflow))

    def _enqueue(self, db, actor, workflow_id, mandate_id=None, occurrence=None, occurrence_id=None, period_id=None):
        ctx = self.context(db, actor, period_id, workflow_id)
        if ctx["period"] is None or ctx["period"]["status"]=="locked":
            raise ControlError("PERIOD_LOCKED" if ctx["period"] else "Accounting period not configured",409)
        workflow = WORKFLOWS.get(workflow_id)
        if not workflow or workflow_id not in ctx["profile"]["procedures"]:
            raise ControlError("Workflow unavailable for this client", 403)
        for step in workflow.steps:
            cap = CAPABILITIES.get(step.capability)
            if not cap or not cap.handler or cap.effect != "prepare":
                raise ControlError("Workflow capability is unimplemented or denied", 403)
        if occurrence_id is not None:
            prior = db.execute("SELECT * FROM runs WHERE occurrence_id=? AND scope=? ORDER BY id DESC LIMIT 1", (occurrence_id,actor.scope)).fetchone()
            if prior and prior["status"] not in ('held','failed'):
                if self._current(db,actor,prior) or prior["status"] in ('awaiting_review','prepared_with_exceptions'):
                    return prior["id"]
                self.hold_run(db,actor,prior,"stale_inputs")
        else:
            prior = db.execute("SELECT * FROM runs WHERE scope=? AND workflow=? AND fingerprint=? AND status NOT IN ('failed','held') ORDER BY id DESC LIMIT 1", (actor.scope, workflow_id, ctx["fingerprint"])).fetchone()
            latest=db.execute("SELECT id FROM runs WHERE scope=? AND workflow=? AND period_id=? AND status IN ('awaiting_review','prepared_with_exceptions') ORDER BY id DESC LIMIT 1",(actor.scope,workflow_id,ctx['period']['period_id'])).fetchone()
            if prior and (not latest or prior['id']>=latest['id']):
                return prior['id']
        run_id = db.execute("INSERT INTO runs(scope,workflow,definition_hash,generation,fingerprint,status,actor,mandate_id,occurrence,created,occurrence_id,period_id,manifest) VALUES(?,?,?,?,?,'queued',?,?,?,?,?,?,?)", (actor.scope, workflow_id, self.definition_hash(workflow), ctx["generation"], ctx["fingerprint"], actor.id, mandate_id, occurrence, utcnow(), occurrence_id, ctx["period"]["period_id"],canonical(ctx["manifest"]))).lastrowid
        for step in workflow.steps:
            db.execute("INSERT INTO steps(scope,run_id,name,capability,needs,status) VALUES(?,?,?,?,?,'queued')", (actor.scope, run_id, step.name, step.capability, canonical(step.needs)))
        self.store.audit(db, actor.scope, actor.id, "workflow_enqueued", {"run_id": run_id, "workflow": workflow_id, "mandate_id": mandate_id, "occurrence": occurrence})
        return run_id

    def enqueue(self, actor, workflow_id, period_id=None):
        self.authorize(actor, ("preparer",))
        with self.store.transaction() as db:
            return self._enqueue(db, actor, workflow_id, period_id=period_id)

    def _mandate_valid(self, db, run, now, use_simulated_clock=False):
        if run["mandate_id"] is None:
            return True
        if use_simulated_clock:
            clock = db.execute("SELECT simulated_now FROM demo_clock WHERE scope=?", (run["scope"],)).fetchone()
            if clock:
                now = instant(clock["simulated_now"])
        mandate = db.execute("SELECT * FROM mandates WHERE id=? AND scope=?", (run["mandate_id"], run["scope"])).fetchone()
        return bool(mandate and mandate["active"] and mandate["approved_by"] and self.mandate_fresh(db,Actor("standing-authority-check","worker",run["scope"].split("/")[0],run["scope"].split("/")[1],kind="service"),mandate,run["period_id"],run["occurrence"]) and instant(mandate["starts"]) <= now < instant(mandate["ends"]) and run["workflow"] in json.loads(mandate["workflows"]))

    def _current(self, db, actor, run):
        if self.period(db,actor,run["period_id"])["status"]=="locked":
            return bool(db.execute("SELECT 1 FROM frozen_runs WHERE scope=? AND run_id=?",(actor.scope,run["id"])).fetchone())
        workflow = WORKFLOWS.get(run["workflow"])
        return bool(workflow and run["fingerprint"] == self.context(db, actor, run["period_id"], run["workflow"])["fingerprint"] and run["definition_hash"] == self.definition_hash(workflow))

    def step_context(self, db, actor, job):
        run=db.execute("SELECT period_id,workflow FROM runs WHERE id=? AND scope=?",(job["run_id"],actor.scope)).fetchone()
        ctx = self.context(db, actor, run["period_id"],run["workflow"])
        cap=CAPABILITIES[job["capability"]]
        if "$workflow" not in cap.reads:ctx["sources"]=[s for s in ctx["sources"] if s["kind"] in cap.reads]
        ctx["profile"]={key:ctx["profile"][key] for key in set(cap.profile_reads)|{"policies"}}
        ctx["profile_ref"]={"accounting_profile_hash":digest(ctx["profile"]),"rule_versions":[{"id":r["id"],"version":r["version"]} for r in ctx["rules"]]}
        # Pass only declared, committed upstream outputs; modules cannot query the DB.
        ctx["dependencies"] = {}
        for name in json.loads(job["needs"]):
            rows = db.execute("SELECT a.id,a.hash,a.payload,a.blockers FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id JOIN steps s ON s.id=l.step_id WHERE a.scope=? AND l.run_id=? AND s.name=? AND s.status='complete' ORDER BY a.id", (actor.scope, job["run_id"], name)).fetchall()
            ctx["dependencies"][name] = [{"artifact_id": r["id"], "hash": r["hash"], "payload": json.loads(r["payload"]), "blockers": json.loads(r["blockers"])} for r in rows]
        return ctx

    def hold_run(self, db, actor, run, reason):
        db.execute("UPDATE runs SET status='held' WHERE id=? AND scope=?",(run["id"],actor.scope))
        if run["occurrence_id"] is not None:
            db.execute("UPDATE occurrences SET status='held',reason=? WHERE id=? AND scope=? AND completed_run_id IS NULL",(reason,run["occurrence_id"],actor.scope))
        self.store.audit(db,actor.scope,actor.id,"run_held",{"run_id":run["id"],"reason":reason})

    def claim(self, actor, now=None):
        self.authorize(actor, ("worker",))
        now_dt = instant(now or utcnow())
        with self.store.transaction() as db:
            self.client(db, actor)
            jobs = db.execute("SELECT s.* FROM steps s JOIN runs r ON r.id=s.run_id WHERE s.scope=? AND r.status IN ('queued','running') AND (s.status='queued' OR (s.status='running' AND s.lease_until<=?)) ORDER BY s.id", (actor.scope, now_dt.isoformat())).fetchall()
            for job in jobs:
                run = db.execute("SELECT * FROM runs WHERE id=? AND scope=?", (job["run_id"], actor.scope)).fetchone()
                if run['workflow']=='close_readiness' and run['status']=='queued':
                    if db.execute("SELECT 1 FROM runs WHERE scope=? AND period_id=? AND id<? AND workflow IN ('card_preparation','journal_preparation') AND status IN ('queued','running')",(actor.scope,run['period_id'],run['id'])).fetchone():continue
                    ctx=self.context(db,actor,run['period_id'],run['workflow']);old=json.loads(run['manifest'])
                    if digest({k:v for k,v in old.items() if k!='period_status'})==digest({k:v for k,v in ctx['manifest'].items() if k!='period_status'}):
                        db.execute('UPDATE runs SET manifest=?,fingerprint=? WHERE id=?',(canonical(ctx['manifest']),ctx['fingerprint'],run['id']))
                        run=db.execute('SELECT * FROM runs WHERE id=?',(run['id'],)).fetchone()
                if not self._current(db, actor, run) or not self._mandate_valid(db, run, now_dt, use_simulated_clock=now is None):
                    self.hold_run(db, actor, run, "stale_inputs_or_inactive_mandate")
                    continue
                states = {s["name"]: s["status"] for s in db.execute("SELECT name,status FROM steps WHERE run_id=? AND scope=?", (run["id"], actor.scope))}
                if any(states.get(n) != "complete" for n in json.loads(job["needs"])):
                    continue
                if job["attempts"] >= SHARED_CONTROLS["max_step_attempts"]:
                    db.execute("UPDATE steps SET status='failed',lease_token=NULL,error='Retry limit reached' WHERE id=?", (job["id"],))
                    db.execute("UPDATE runs SET status='failed' WHERE id=?", (run["id"],))
                    self.store.audit(db, actor.scope, actor.id, "retry_limit_reached", {"step_id": job["id"]})
                    continue
                token = secrets.token_hex(16)
                until = (now_dt + timedelta(seconds=SHARED_CONTROLS["lease_seconds"])).isoformat()
                db.execute("UPDATE steps SET status='running',attempts=attempts+1,lease_until=?,lease_token=?,error=NULL WHERE id=?", (until, token, job["id"]))
                db.execute("UPDATE runs SET status='running' WHERE id=?", (run["id"],))
                self.store.audit(db, actor.scope, actor.id, "step_claimed", {"run_id": run["id"], "step_id": job["id"], "attempt": job["attempts"] + 1})
                return {"step_id": job["id"], "run_id": run["id"], "token": token, "capability": job["capability"], "context": self.step_context(db, actor, job)}
        return None

    def commit(self, actor, claim, outputs, now=None):
        self.authorize(actor, ("worker",))
        now_dt = instant(now or utcnow())
        with self.store.transaction() as db:
            job = db.execute("SELECT * FROM steps WHERE id=? AND scope=?", (claim["step_id"], actor.scope)).fetchone()
            if not job or job["status"] != "running" or job["lease_token"] != claim["token"] or instant(job["lease_until"]) <= now_dt:
                raise ControlError("Worker lease lost; result cannot be committed", 409)
            run = db.execute("SELECT * FROM runs WHERE id=? AND scope=?", (job["run_id"], actor.scope)).fetchone()
            if run["status"] == "held" or not self._current(db, actor, run) or not self._mandate_valid(db, run, now_dt, use_simulated_clock=now is None):
                self.hold_run(db, actor, run, "stale_inputs_or_inactive_mandate")
                db.execute("UPDATE steps SET status='held',lease_token=NULL WHERE id=?", (job["id"],))
                self.store.audit(db, actor.scope, actor.id, "stale_result_discarded", {"run_id": run["id"], "step_id": job["id"]})
                return False
            if not isinstance(outputs, list) or not 1 <= len(outputs) <= 1000:
                raise ControlError("Module returned invalid output collection")
            ctx = self.step_context(db, actor, job)
            dependency_refs = {name: [{"hash": a["hash"]} for a in artifacts] for name, artifacts in ctx["dependencies"].items()}
            run_ctx=self.context(db,actor,run["period_id"],run["workflow"])
            base_lineage={(run['actor'],'enqueuer'),(actor.id,'worker')}
            if run["mandate_id"] is not None:
                issuer=db.execute("SELECT issuer FROM mandates WHERE id=? AND scope=?",(run['mandate_id'],actor.scope)).fetchone()['issuer']
                base_lineage.add((issuer,'mandate_issuer'))
            seen = set()
            for result in outputs:
                require_keys(result, {"item_key", "kind", "data", "blockers", "eligible"})
                text_field(result["item_key"], "artifact item key")
                text_field(result["kind"], "artifact kind")
                if result["item_key"] in seen or not isinstance(result["blockers"], list) or type(result["eligible"]) is not bool or not isinstance(result["data"], dict):
                    raise ControlError("Invalid structured module result")
                for blocker in result["blockers"]:
                    text_field(blocker, "blocker")
                seen.add(result["item_key"])
                blockers = list(result["blockers"])
                step=next(st for st in WORKFLOWS[run['workflow']].steps if st.name==job['name'])
                if step.on_dependency_blockers=='propagate':
                    for upstream in ctx['dependencies'].values():
                        for dep in upstream:
                            blockers += [c for c in dep['blockers'] if c=='NO_SOURCE_EVIDENCE' or c.startswith(('STATEMENT_','CLIENT_FACT_MISSING:')) or c in ('MODEL_REVIEW_UNAVAILABLE','PERIOD_LOCKED')]
                cap=CAPABILITIES[job['capability']]
                lineage=set(base_lineage)
                evidence=result['data'].get('evidence',[])+result['data'].get('duplicate_population',result['data'].get('duplicate_candidates',[]))
                evidence += [revision[side] for revision in result['data'].get('evidence_revisions',[]) for side in ('earlier','current')]
                evidence += [e for disposition in run_ctx['dispositions'] if disposition['id'] in result['data'].get('disposition_ids',[]) for e in disposition['evidence']]
                ids={e['snapshot_id'] for e in evidence}
                item_sources=[src for src in run_ctx['sources'] if src['id'] in ids]
                for sid in ids-{src['id'] for src in item_sources}:
                    historical=db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(actor.scope,sid)).fetchone()
                    if historical:item_sources.append(dict(historical,value=json.loads(historical['payload'])))
                if result['kind'] not in ('card_proposal','journal_proposal'):item_sources=run_ctx['sources']
                for source in item_sources:
                    lineage.update((r['actor'],'source_supplier:'+source['kind']+':'+source['source_key']) for r in db.execute('SELECT actor FROM snapshots WHERE scope=? AND kind=? AND source_key=?',(actor.scope,source['kind'],source['source_key'])))
                # Static chart/entity/book configuration has authorship too; a rule's
                # author does not stand in for the people who prepared those inputs.
                relevant=(set(cap.profile_reads)|set(cap.requires_client_facts)|{'entity_id','book_id'})-{'vendors','policies','required_close_evidence'}
                last={}
                config_date=run_ctx['period']['start']
                for version in db.execute("SELECT s.*,d.actor AS approved_by FROM snapshots s JOIN profile_proposals p ON p.snapshot_id=s.id JOIN profile_decisions d ON d.snapshot_id=s.id WHERE s.scope=? AND d.decision='approve' AND p.effective_from<=? ORDER BY p.effective_from,s.id",(actor.scope,config_date)):
                    data=json.loads(version['payload'])
                    for field in relevant:
                        if field not in last or last[field]!=data.get(field):
                            lineage.add((version['actor'],'profile_component_proposer:'+field+':'+str(version['id'])))
                            lineage.add((version['approved_by'],'profile_component_approver:'+field+':'+str(version['id'])))
                            last[field]=data.get(field)
                item_rules=list(run_ctx['item_rules'].get(result['item_key'],run_ctx['rules']))
                if result['kind']=='card_proposal' and result['data'].get('transaction'):item_rules+=run_ctx['statement_rules'].get(result['data']['transaction']['account_id'],[])
                for rule in item_rules:
                    if rule['kind'] not in ('vendor_mapping','review_policy','receipt_matching','statement_policy') and result['kind']=='card_proposal':continue
                    if rule['kind']=='vendor_mapping' and (result['kind']!='card_proposal' or (result['data'].get('vendor') or {}).get('id')!=rule['value']['id']):continue
                    for ancestor in self.applied_rule_lineage(db,actor.scope,rule,result['data']):
                        lineage.add((ancestor['proposed_by'],'rule_proposer:'+str(ancestor['id'])))
                        if ancestor['approved_by']:lineage.add((ancestor['approved_by'],'rule_approver:'+str(ancestor['id'])))
                for d in run_ctx['dispositions']:
                    if d['item_key']==result['item_key'] or d['id'] in result['data'].get('disposition_ids',[]):lineage.add((d['actor'],'disposition:'+str(d['id'])))
                histories=run_ctx['selection_history']
                selected=histories.get(result['item_key'],[]) if result['kind']=='card_proposal' else [d for history in histories.values() for d in history]
                lineage.update((d['actor'],'source_target_selector:'+str(d['id'])) for d in selected)
                for acceptance in (result['data'].get('prior_statement_acceptance') or {}).get('acceptances',[]):
                    lineage.add((acceptance['actor'],'prior_statement_revision_acceptance:'+str(acceptance['id'])))
                cap=CAPABILITIES[job['capability']]
                waived={}
                for fact in cap.requires_client_facts:
                    if not run_ctx['profile'].get(fact):
                        waiver=run_ctx['profile'].get('fact_waivers',{}).get(fact)
                        if run_ctx['profile'].get('profile_class')=='synthetic_demo' and isinstance(waiver,str) and waiver.strip():waived[fact]=waiver
                        else:blockers.append('CLIENT_FACT_MISSING:'+fact)
                item_policy=next((r['value'] for r in item_rules if r['kind']=='review_policy'),ctx['profile']['policies'])
                if item_policy['model_review_required'] or WORKFLOWS[run["workflow"]].required_model_review:
                    blockers.append("MODEL_REVIEW_UNAVAILABLE")
                envelope = {"synthetic": True, "notice": "FICTIONAL DEMONSTRATION — no live accounting effects", "scope": actor.scope,
                            "entity_id":run_ctx["profile"].get("entity_id"),"book_id":run_ctx["profile"].get("book_id"),"period_id": run["period_id"], "workflow": run["workflow"], "workflow_version": WORKFLOWS[run["workflow"]].version,
                            "capability": job["capability"], "capability_version": CAPABILITIES[job["capability"]].version,
                            "fact_waivers":waived, "applied_rules":[{"id":r["id"],"version":r["version"]} for r in run_ctx["rules"]], "shared_controls": SHARED_CONTROLS, "input_fingerprint": run["fingerprint"], "dependencies": dependency_refs,
                            "data": result["data"]}
                content_hash=digest(envelope)
                governing=self.governing_id(db,actor.scope,run['workflow'],run['period_id'],result['item_key'])
                existing=db.execute("SELECT id,hash,payload FROM artifacts WHERE id=? AND scope=?",(governing,actor.scope)).fetchone()
                if not existing or existing['hash']!=content_hash:
                    historical=db.execute("SELECT a.id,a.hash,a.payload FROM artifacts a JOIN runs r ON r.id=a.run_id WHERE a.scope=? AND r.workflow=? AND r.period_id=? AND a.item_key=? AND a.hash=? ORDER BY a.id DESC LIMIT 1",(actor.scope,run['workflow'],run['period_id'],result['item_key'],content_hash)).fetchone()
                    if historical:existing=historical
                if existing and (existing['hash']==content_hash or digest({k:v for k,v in json.loads(existing['payload']).items() if k!='contributors'})==content_hash):
                    artifact_id=existing['id']
                else:
                    artifact_id=db.execute("INSERT INTO artifacts(scope,run_id,step_id,item_key,kind,payload,hash,blockers,eligible,created) VALUES(?,?,?,?,?,?,?,?,?,?)", (actor.scope, run["id"], job["id"], result["item_key"], result["kind"], canonical(envelope), content_hash, canonical(sorted(set(blockers))), int(result["eligible"] and not blockers), utcnow())).lastrowid
                for who,role in sorted(lineage):
                    db.execute("INSERT OR IGNORE INTO artifact_contributors VALUES(?,?,?,?,?)",(actor.scope,artifact_id,who,role,run['id']))
                self.record_exceptions(db,actor.scope,run["workflow"],run["period_id"],result["item_key"],artifact_id,blockers,[d for d in run_ctx["dispositions"] if d["item_key"]==result["item_key"] or d["id"] in result["data"].get("disposition_ids",[])])
                db.execute("INSERT INTO artifact_runs VALUES(?,?,?,?)",(actor.scope,run['id'],job['id'],artifact_id))
            db.execute("UPDATE steps SET status='complete',lease_token=NULL,lease_until=NULL WHERE id=?", (job["id"],))
            incomplete = db.execute("SELECT COUNT(*) FROM steps WHERE run_id=? AND status!='complete'", (run["id"],)).fetchone()[0]
            if not incomplete:
                if run["occurrence_id"] is not None:
                    changed = db.execute("UPDATE occurrences SET status='completed',completed_run_id=?,reason=NULL WHERE id=? AND scope=? AND completed_run_id IS NULL",(run["id"],run["occurrence_id"],actor.scope)).rowcount
                    if not changed:
                        raise ControlError("Occurrence already completed",409)
                blocked = any(json.loads(r["blockers"]) for r in db.execute("SELECT a.blockers FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id WHERE l.run_id=? AND a.scope=?", (run["id"], actor.scope)))
                db.execute("UPDATE runs SET status=? WHERE id=?", ("prepared_with_exceptions" if blocked else "awaiting_review", run["id"]))
            if not incomplete:self.record_population_departures(db,actor,run)
            self.package_changes(db,actor)
            self.store.audit(db, actor.scope, actor.id, "step_checkpoint_committed", {"run_id": run["id"], "step_id": job["id"], "artifacts": len(outputs)})
            return True

    def work_once(self, actor, now=None):
        claim = self.claim(actor, now)
        if not claim:
            return False
        try:
            cap = CAPABILITIES.get(claim["capability"])
            if not cap or not cap.handler or cap.effect != "prepare":
                raise ControlError("Tool not implemented/authorized")
            result = cap.handler(claim["context"])
            self.commit(actor, claim, result, now)
        except ControlError as exc:
            if exc.status == 409:
                return True
            self._fail(actor, claim, str(exc))
        except Exception:
            # Do not leak source text, credentials or arbitrary exception internals to logs.
            self._fail(actor, claim, "Module execution failed; inspect tests/technical support")
        return True

    def _fail(self, actor, claim, message):
        with self.store.transaction() as db:
            row = db.execute("SELECT * FROM steps WHERE id=? AND scope=? AND lease_token=?", (claim["step_id"], actor.scope, claim["token"])).fetchone()
            if row:
                failed = row["attempts"] >= SHARED_CONTROLS["max_step_attempts"]
                db.execute("UPDATE steps SET status=?,lease_token=NULL,lease_until=NULL,error=? WHERE id=?", ("failed" if failed else "queued", message, row["id"]))
                if failed:
                    db.execute("UPDATE runs SET status='failed' WHERE id=?", (row["run_id"],))
                self.store.audit(db, actor.scope, actor.id, "step_failed", {"step_id": row["id"], "retry_exhausted": failed, "error": message})

    def drain(self, actor, now=None, limit=100):
        count = 0
        while count < limit and self.work_once(actor, now):
            count += 1
        return count

    def governing_id(self,db,scope,workflow,period_id,item_key):
        row=db.execute("SELECT a.id FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id WHERE a.scope=? AND l.scope=? AND a.item_key=? AND l.run_id=(SELECT id FROM runs WHERE scope=? AND workflow=? AND period_id=? AND status IN ('awaiting_review','prepared_with_exceptions') ORDER BY id DESC LIMIT 1) ORDER BY a.id DESC LIMIT 1",(scope,scope,item_key,scope,workflow,period_id)).fetchone()
        return row['id'] if row else None

    def contributors(self,db,scope,artifact):
        legacy=json.loads(artifact['payload']).get('contributors',[])
        rows=db.execute("SELECT actor FROM artifact_contributors WHERE scope=? AND artifact_id=?",(scope,artifact['id'])).fetchall()
        return sorted(set(legacy)|{r['actor'] for r in rows}) if legacy or rows else None

    def review_state(self,decisions):
        state='pending';decider=None
        for d in decisions:
            choice=d['decision']
            if choice.startswith('resolve_'):
                state=choice.removeprefix('resolve_');decider=d['actor']
            elif state=='pending':state=choice;decider=d['actor']
            elif state=='approve' and choice=='revoke':state='revoke';decider=d['actor']
            elif state in ('approve','reject') and choice in ('approve','reject') and choice!=state and decider!=d['actor']:state='disputed'
        return state

    def review(self, actor, artifact_id, artifact_hash, fingerprint, decision, reason):
        self.authorize(actor, ("reviewer",))
        if decision not in ("approve", "reject", "revoke", "resolve_approve", "resolve_reject"):
            raise ControlError("Unknown review decision")
        text_field(reason, "review reason", 2000)
        with self.store.transaction() as db:
            self.client(db, actor)
            artifact = db.execute("SELECT * FROM artifacts WHERE id=? AND scope=?", (artifact_id, actor.scope)).fetchone()
            if not artifact:
                raise ControlError("Artifact not found in client scope", 404)
            run = db.execute("SELECT * FROM runs WHERE id=? AND scope=?", (artifact["run_id"], actor.scope)).fetchone()
            if self.period(db,actor,run["period_id"])["status"]=="locked":
                raise ControlError("PERIOD_LOCKED",409)
            if artifact["hash"] != artifact_hash or run["fingerprint"] != fingerprint:
                raise ControlError("Exact artifact/version mismatch", 409)
            self.require_grant(db,actor,"review")
            contributors = self.contributors(db,actor.scope,artifact)
            if actor.kind != "human" or contributors is None or actor.id in contributors:
                raise ControlError("Independent human review required", 403)
            links=db.execute("SELECT r.* FROM runs r JOIN artifact_runs l ON l.run_id=r.id WHERE l.artifact_id=? AND l.scope=? ORDER BY r.id DESC",(artifact_id,actor.scope)).fetchall()
            governing=self.governing_id(db,actor.scope,run['workflow'],run['period_id'],artifact['item_key'])
            if decision!='revoke' and (governing!=artifact_id or not any(r['status'] in ('awaiting_review','prepared_with_exceptions') and self._current(db,actor,r) for r in links)):
                raise ControlError("Preparation is stale, unfinished or not governing",409)
            previous=[dict(d) for d in db.execute("SELECT * FROM decisions WHERE artifact_id=? AND scope=? ORDER BY id",(artifact_id,actor.scope))]
            state=self.review_state(previous)
            if decision.startswith('resolve_'):
                if state not in ('disputed','revoke') or actor.id in {d['actor'] for d in previous}:
                    raise ControlError("Dispute requires an explicit third independent reviewer resolution",409)
            elif any(d['decision'].startswith('resolve_') for d in previous) and decision!='revoke':
                raise ControlError('Resolved judgment is final for this artifact; new preparation required',409)
            elif state=='disputed' or state=='revoke' or decision==state:
                raise ControlError("Duplicate or invalid review transition",409)
            elif decision=='revoke':
                if state!='approve':raise ControlError("Only an approval can be revoked",409)
            elif state!='pending' and (previous[-1]['actor']==actor.id or decision not in ('approve','reject')):
                raise ControlError("Changed judgment requires renewed preparation or dispute resolution",409)
            if decision in ('approve','resolve_approve') and (not artifact['eligible'] or json.loads(artifact['blockers'])):
                raise ControlError("Unresolved controls block approval",409)
            db.execute("INSERT INTO decisions(scope,artifact_id,artifact_hash,fingerprint,decision,reason,actor,created) VALUES(?,?,?,?,?,?,?,?)", (actor.scope, artifact_id, artifact_hash, fingerprint, decision, reason, actor.id, utcnow()))
            self.package_changes(db,actor)
            self.store.audit(db, actor.scope, actor.id, "review_" + decision, {"artifact_id": artifact_id, "artifact_hash": artifact_hash, "scope_of_approval": "preparation_only", "reason": reason})

    def create_mandate(self, actor, workflows, starts, ends, interval_seconds, max_occurrences, period_rule=None, freshness=None):
        self.authorize(actor, ("preparer",))
        if actor.kind != "human":
            raise ControlError("Synthetic mandate requires a human preparer", 403)
        if not isinstance(period_rule,dict) or period_rule.get('kind') not in ('fixed','previous_month','occurrence_calendar') or (period_rule['kind']=='fixed' and not isinstance(period_rule.get('period_id'),str)) or not isinstance(freshness,dict):
            raise ControlError('Explicit period_rule and freshness predicate required')
        if not isinstance(workflows, list) or not workflows or len(set(workflows)) != len(workflows) or any(w not in WORKFLOWS for w in workflows):
            raise ControlError("Unknown mandate workflow")
        freshness=self.validate_freshness(workflows,freshness)
        if instant(ends) <= instant(starts) or type(interval_seconds) is not int or not 60 <= interval_seconds <= 31536000 or type(max_occurrences) is not int or not 1 <= max_occurrences <= 100:
            raise ControlError("Invalid bounded mandate interval/window/limit")
        if (instant(ends)-instant(starts)).total_seconds() / interval_seconds > 10000:
            raise ControlError("Synthetic mandate window exceeds 10000 slots")
        with self.store.transaction() as db:
            ctx = self.context(db, actor)
            if not set(workflows).issubset(ctx["profile"]["procedures"]):
                raise ControlError("Mandate exceeds client procedures", 403)
            mid = db.execute("INSERT INTO mandates(scope,workflows,starts,ends,interval_seconds,max_occurrences,active,issuer,created,status,period_rule,freshness) VALUES(?,?,?,?,?,?,0,?,?,'proposed',?,?)", (actor.scope, canonical(workflows), instant(starts).isoformat(), instant(ends).isoformat(), interval_seconds, max_occurrences, actor.id, utcnow(), canonical(period_rule),canonical(freshness))).lastrowid
            self.store.audit(db, actor.scope, actor.id, "synthetic_mandate_issued", {"mandate_id": mid, "workflows": workflows, "live_schedule": False})
            return mid

    def revoke_mandate(self, actor, mandate_id):
        self.authorize(actor, ("preparer",))
        with self.store.transaction() as db:
            if not db.execute("UPDATE mandates SET active=0 WHERE id=? AND scope=?", (mandate_id, actor.scope)).rowcount:
                raise ControlError("Mandate not found", 404)
            self.store.audit(db, actor.scope, actor.id, "mandate_revoked", {"mandate_id": mandate_id})

    def tick(self, actor, now):
        self.authorize(actor, ("preparer",))
        now_dt = instant(now)
        created = []
        with self.store.transaction() as db:
            self.client(db, actor)
            prior_clock = db.execute("SELECT simulated_now FROM demo_clock WHERE scope=?", (actor.scope,)).fetchone()
            if prior_clock and instant(prior_clock["simulated_now"]) > now_dt:
                raise ControlError("Simulated recurring clock cannot move backwards", 409)
            db.execute("INSERT INTO demo_clock(scope,simulated_now) VALUES(?,?) ON CONFLICT(scope) DO UPDATE SET simulated_now=excluded.simulated_now", (actor.scope, now_dt.isoformat()))
            for mandate in db.execute("SELECT * FROM mandates WHERE scope=? AND active=1", (actor.scope,)).fetchall():
                start, end = instant(mandate["starts"]), instant(mandate["ends"])
                interval = mandate["interval_seconds"]
                if now_dt < start:
                    continue
                current_number = int((min(now_dt,end)-start).total_seconds()) // interval
                first_number = 0 if not mandate["last_tick"] else int((instant(mandate["last_tick"])-start).total_seconds()) // interval + 1
                # Bounded by the validated window; missed slots are records, never silently lost.
                skip_stop=current_number if now_dt<end else math.ceil((end-start).total_seconds()/interval)
                for number in range(max(0,first_number),skip_stop):
                    key = (start+timedelta(seconds=number*interval)).isoformat()
                    for workflow in json.loads(mandate["workflows"]):
                        db.execute("INSERT OR IGNORE INTO occurrences(scope,mandate_id,workflow,occurrence_key,status,reason,created) VALUES(?,?,?,?,'skipped_no_catch_up','No event delivered for this slot',?)",(actor.scope,mandate["id"],workflow,key,utcnow()))
                if now_dt >= end:
                    db.execute("UPDATE mandates SET last_tick=? WHERE id=?",(now_dt.isoformat(),mandate["id"]))
                    continue
                occurrence = (start+timedelta(seconds=current_number*interval)).isoformat()
                for workflow in json.loads(mandate["workflows"]):
                    if not db.execute("SELECT active FROM mandates WHERE id=?",(mandate["id"],)).fetchone()["active"]:break
                    count = db.execute("SELECT COUNT(DISTINCT occurrence_key) FROM occurrences WHERE mandate_id=? AND scope=? AND status!='skipped_no_catch_up'",(mandate["id"],actor.scope)).fetchone()[0]
                    existing = db.execute("SELECT 1 FROM occurrences WHERE mandate_id=? AND scope=? AND occurrence_key=? AND status!='skipped_no_catch_up'",(mandate["id"],actor.scope,occurrence)).fetchone()
                    if count < mandate["max_occurrences"] or existing:
                        db.execute("INSERT OR IGNORE INTO occurrences(scope,mandate_id,workflow,occurrence_key,status,created) VALUES(?,?,?,?,'dispatched',?)",(actor.scope,mandate["id"],workflow,occurrence,utcnow()))
                    pending = db.execute("SELECT * FROM occurrences WHERE mandate_id=? AND scope=? AND workflow=? AND (occurrence_key=? OR status IN ('held','awaiting_evidence')) ORDER BY id",(mandate["id"],actor.scope,workflow,occurrence)).fetchall()
                    for occurrence_row in pending:
                        if occurrence_row["status"] == 'skipped_no_catch_up':
                            continue
                        if occurrence_row["completed_run_id"] is not None:
                            if occurrence_row["occurrence_key"] == occurrence:
                                created.append(occurrence_row["completed_run_id"])
                            continue
                        try:
                            period_id=self.mandate_period(db,actor,mandate,occurrence_row['occurrence_key'])
                            current=self.policy_signature(db,self.context(db,actor,period_id,workflow))
                            if current!=json.loads(mandate['bound_rules']).get(workflow):
                                db.execute("UPDATE mandates SET active=0,status='needs_reconfirmation',reason='Bound policy changed' WHERE id=?",(mandate['id'],))
                                raise ControlError('Bound policy changed; independent reconfirmation required',409)
                            if not self.mandate_fresh(db,actor,mandate,period_id,occurrence_row['occurrence_key']):
                                db.execute("UPDATE occurrences SET status='awaiting_evidence',reason='Fresh evidence required' WHERE id=?",(occurrence_row['id'],))
                                continue
                            rid=self._enqueue(db,actor,workflow,mandate["id"],occurrence_row["occurrence_key"],occurrence_row["id"],period_id)
                            db.execute("UPDATE occurrences SET status='dispatched',reason=NULL WHERE id=?",(occurrence_row["id"],))
                            db.execute("UPDATE mandates SET status='active',reason=NULL WHERE id=?",(mandate["id"],))
                            created.append(rid)
                        except ControlError as exc:
                            db.execute("UPDATE occurrences SET status='held',reason=? WHERE id=?",(str(exc),occurrence_row["id"]))
                            db.execute("UPDATE mandates SET status=CASE WHEN active=0 THEN status ELSE 'held' END,reason=? WHERE id=?",(str(exc),mandate["id"]))
                            self.store.audit(db,actor.scope,actor.id,"mandate_dispatch_held",{"mandate_id":mandate["id"],"occurrence_id":occurrence_row["id"],"reason":str(exc)})
                db.execute("UPDATE mandates SET last_tick=? WHERE id=?",(now_dt.isoformat(),mandate["id"]))
            self.store.audit(db, actor.scope, actor.id, "simulated_recurring_event", {"time": now_dt.isoformat(), "run_ids": created, "live_schedule": False})
        return created

    def state(self, actor):
        self.authorize(actor)
        with self.store.transaction() as db:
            ctx = self.context(db, actor)
            runs = [dict(r) for r in db.execute("SELECT * FROM runs WHERE scope=? ORDER BY id DESC", (actor.scope,))]
            for run in runs:
                run["current"] = self._current(db, actor, run)
                run["steps"] = [dict(s) for s in db.execute("SELECT id,name,capability,status,attempts,error FROM steps WHERE scope=? AND run_id=? ORDER BY id", (actor.scope, run["id"]))]
            artifacts = []
            runmap = {r["id"]: r for r in runs}
            for row in db.execute("SELECT * FROM artifacts WHERE scope=? ORDER BY id DESC", (actor.scope,)):
                a = dict(row)
                a["contributors"]=self.contributors(db,actor.scope,row)
                a["contributor_history"]=[dict(c) for c in db.execute("SELECT * FROM artifact_contributors WHERE scope=? AND artifact_id=? ORDER BY run_id,actor,lineage_role",(actor.scope,a["id"]))]
                a["payload"] = json.loads(a["payload"])
                a["blockers"] = json.loads(a["blockers"])
                run = runmap[a["run_id"]]
                a['run_ids']=[r['run_id'] for r in db.execute("SELECT run_id FROM artifact_runs WHERE artifact_id=? AND scope=? ORDER BY run_id",(a['id'],actor.scope))]
                a['period_id']=run['period_id']
                a['governing']=self.governing_id(db,actor.scope,run['workflow'],run['period_id'],a['item_key'])==a['id']
                a["current"] = a['governing'] and any(runmap[r]['current'] and runmap[r]['status'] in ('awaiting_review','prepared_with_exceptions') for r in a['run_ids'])
                a["fingerprint"] = run["fingerprint"]
                decisions = [dict(d) for d in db.execute("SELECT * FROM decisions WHERE artifact_id=? AND scope=? ORDER BY id", (a["id"], actor.scope))]
                a["decisions"] = decisions
                a["review_status"] = "stale" if not a["current"] else self.review_state(decisions)
                artifacts.append(a)
            audit = [dict(a) for a in db.execute("SELECT * FROM audit WHERE scope=? ORDER BY id DESC LIMIT 100", (actor.scope,))]
            mandates = [dict(m) for m in db.execute("SELECT * FROM mandates WHERE scope=? ORDER BY id DESC", (actor.scope,))]
            return {"synthetic": True, "environment": "local", "mode": "demo", "scope": actor.scope,
                    "notice": "Fictional sandbox; actual client accounting policies remain unconfigured.",
                    "periods": [dict(p) for p in db.execute("SELECT * FROM periods WHERE scope=? ORDER BY start",(actor.scope,))],
                    "source_claim_conflicts": {row['source_key']:state for row in db.execute("SELECT source_key FROM source_heads WHERE scope=? AND kind='transaction'",(actor.scope,)) for state in [self.card_claim_state(db,actor.scope,row['source_key'])] if state and state['conflicted']},
                    "source_exceptions": [dict(b) for b in db.execute("SELECT b.*,s.source_key FROM source_periods b JOIN snapshots s ON s.id=b.snapshot_id WHERE b.scope=? AND b.reason IS NOT NULL AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=b.snapshot_id) AND EXISTS(SELECT 1 FROM source_heads h WHERE h.scope=b.scope AND h.snapshot_id=b.snapshot_id AND (h.removed=0 OR (b.admitted=0 AND b.reason='LATE_ACTIVITY_IN_LOCKED_PERIOD' AND EXISTS(SELECT 1 FROM periods p WHERE p.scope=b.scope AND p.period_id=b.period_id AND p.status='locked'))))",(actor.scope,))],
                    "feed_anomalies": self.card_feed_anomalies(db,actor.scope),
                    "profile": ctx["profile"], "fingerprint": ctx["fingerprint"], "generation": ctx["generation"],
                    "capabilities": [{k: v for k, v in asdict(c).items() if k != "handler"} for c in CAPABILITIES.values()],
                    "workflows": [asdict(w) for w in WORKFLOWS.values()],
                    "accounting_events":[dict(r) for r in db.execute("SELECT * FROM accounting_events WHERE scope=? ORDER BY id",(actor.scope,))],
                    "removed_items":[item for period in db.execute("SELECT period_id FROM periods WHERE scope=?",(actor.scope,)) for item in self.removed_items(db,actor,period["period_id"])],
                    "packages":self.package_records(db,actor.scope),
                    "exceptions":[dict(r) for r in db.execute("SELECT * FROM exceptions WHERE scope=?",(actor.scope,))],
                    "rules":self.rule_records(db,actor.scope),
                    "dispositions":[dict(r) for r in db.execute("SELECT * FROM dispositions WHERE scope=?",(actor.scope,))],
                    "runs": runs, "artifacts": artifacts, "mandates": mandates, "occurrences": [dict(o) for o in db.execute("SELECT * FROM occurrences WHERE scope=? ORDER BY id",(actor.scope,))], "audit": audit,
                    "sources": [{k: v for k, v in s.items() if k != "payload"} for s in self.store.latest(db,actor.scope) if s["kind"] not in ("profile","batch")],
                    "external": {"ledger": "unconnected", "models": "disabled", "model_calls": 0, "hosting": "not_deployed", "posting": "disabled", "final_close": "not_signed_off", "live_schedules": "disabled"}}

    def export(self, actor):
        state = self.state(actor)
        state["exported_at"] = utcnow()
        state["approval_scope"] = "Preparation review only. No posting, reconciliation or final close authority."
        # Include immutable versions and decisions for portable inspection, without active queue import.
        with self.store.transaction() as db:
            if self.context(db, actor)["fingerprint"] != state["fingerprint"]:
                raise ControlError("Inputs changed during export; retry for a consistent package", 409)
            state['rule_retirements']=[dict(r) for r in db.execute('SELECT * FROM rule_retirements WHERE scope=? ORDER BY id',(actor.scope,))]
            state['rule_decisions']=[dict(r) for r in db.execute('SELECT * FROM rule_decisions WHERE scope=? ORDER BY id',(actor.scope,))]
            state['profile_decisions']=[dict(r) for r in db.execute('SELECT * FROM profile_decisions WHERE scope=? ORDER BY id',(actor.scope,))]
            state['profile_proposals']=[dict(r) for r in db.execute('SELECT * FROM profile_proposals WHERE scope=? ORDER BY snapshot_id',(actor.scope,))]
            state['authority_grants']=[dict(r) for r in db.execute('SELECT * FROM authority_grants WHERE scope=? ORDER BY id',(actor.scope,))]
            state["exception_history"]=[dict(r) for r in db.execute("SELECT * FROM exception_history WHERE scope=? ORDER BY id",(actor.scope,))]
            state["artifact_contributor_history"] = [dict(r) for r in db.execute("SELECT * FROM artifact_contributors WHERE scope=? ORDER BY run_id,artifact_id,actor,lineage_role",(actor.scope,))]
            state["artifact_run_links"] = [dict(r) for r in db.execute("SELECT * FROM artifact_runs WHERE scope=? ORDER BY run_id,step_id,artifact_id",(actor.scope,))]
            state["period_history"] = [dict(r) for r in db.execute("SELECT * FROM period_history WHERE scope=? ORDER BY id",(actor.scope,))]
            state["source_lifecycle"] = [dict(r) for r in db.execute("SELECT * FROM source_metadata WHERE scope=? ORDER BY snapshot_id",(actor.scope,))]
            state["source_links"] = [dict(r) for r in db.execute("SELECT * FROM source_links WHERE scope=? ORDER BY id",(actor.scope,))]
            state["accounting_events"] = [dict(r) for r in db.execute("SELECT * FROM accounting_events WHERE scope=? ORDER BY id",(actor.scope,))]
            state["source_move_history"] = [dict(r) for r in db.execute("SELECT * FROM source_moves WHERE scope=? ORDER BY id",(actor.scope,))]
            state["source_period_history"] = [dict(r) for r in db.execute("SELECT * FROM source_periods WHERE scope=? ORDER BY id",(actor.scope,))]
            state["evidence_history"] = [dict(r) for r in db.execute("SELECT * FROM snapshots WHERE scope=? ORDER BY id", (actor.scope,))]
            state["audit_history"] = [dict(r) for r in db.execute("SELECT * FROM audit WHERE scope=? ORDER BY id", (actor.scope,))]
        state["package_hash"] = digest(state)
        return state

    def verify_audit(self, actor):
        self.authorize(actor)
        with self.store.transaction() as db:
            prev = "0" * 64
            for row in db.execute("SELECT * FROM audit WHERE scope=? ORDER BY id", (actor.scope,)):
                record = {"scope": row["scope"], "actor": row["actor"], "event": row["event"], "payload": json.loads(row["payload"]), "created": row["created"], "prev_hash": row["prev_hash"]}
                if row["prev_hash"] != prev or digest(record) != row["hash"]:
                    return False
                prev = row["hash"]
        return True
