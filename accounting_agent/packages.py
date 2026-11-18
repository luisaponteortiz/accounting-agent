"""Immutable preparation handover; does not finalize a ledger or external close."""
import json
from .core import ControlError, canonical, digest, text_field, utcnow

PACKAGE_CODES={'NO_SOURCE_EVIDENCE','MODEL_REVIEW_UNAVAILABLE','SOURCE_ALREADY_HAS_ENTRY'}

def package_blocker(code):
    return code in PACKAGE_CODES or code.startswith(('STATEMENT_','CLIENT_FACT_MISSING:'))

class PackageControls:
    def outcome_run_current(self,db,actor,run,cache):
        # Reuse only inside a database transaction: every read sees the same
        # snapshot, and period_outcomes performs no writes. Autocommit readers
        # keep the full per-item computation, including concurrent changes.
        if not db.in_transaction:return self._current(db,actor,run)
        if run['id'] not in cache:cache[run['id']]=self._current(db,actor,run)
        return cache[run['id']]

    def period_outcomes(self,db,actor,period_id):
        items=[];current_runs={}
        rows=db.execute("SELECT DISTINCT a.*,r.workflow FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id JOIN runs r ON r.id=l.run_id WHERE a.scope=? AND r.period_id=? AND r.workflow IN ('card_preparation','journal_preparation') AND a.kind IN ('card_proposal','journal_proposal') ORDER BY a.id",(actor.scope,period_id)).fetchall()
        for a in rows:
            if a['item_key'] in ('no-transactions','no-journals') or self.governing_id(db,actor.scope,a['workflow'],period_id,a['item_key'])!=a['id']:continue
            links=db.execute('SELECT r.* FROM runs r JOIN artifact_runs l ON l.run_id=r.id WHERE l.artifact_id=? AND l.scope=?',(a['id'],actor.scope)).fetchall()
            current=any(r['status'] in ('awaiting_review','prepared_with_exceptions') and self.outcome_run_current(db,actor,r,current_runs) for r in links)
            decisions=[dict(d) for d in db.execute('SELECT * FROM decisions WHERE scope=? AND artifact_id=? ORDER BY id',(actor.scope,a['id']))]
            items.append({'id':a['id'],'hash':a['hash'],'workflow':a['workflow'],'item_key':a['item_key'],'status':self.review_state(decisions) if current else 'stale','blockers':json.loads(a['blockers']),'decisions':decisions,'contributors':self.contributors(db,actor.scope,a),'payload':json.loads(a['payload'])})
        quarantined=[dict(r) for r in db.execute('SELECT b.*,s.source_key FROM source_periods b JOIN snapshots s ON s.id=b.snapshot_id WHERE b.scope=? AND (b.period_id=? OR b.period_id IS NULL) AND b.admitted=0 AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=b.snapshot_id) AND EXISTS(SELECT 1 FROM source_heads h WHERE h.snapshot_id=b.snapshot_id AND h.removed=0)',(actor.scope,period_id))]
        return {'items':items,'removed_items':self.removed_items(db,actor,period_id),'quarantined_sources':quarantined,'packages':[dict(r) for r in db.execute('SELECT id,workflow,hash FROM packages WHERE scope=? AND period_id=?',(actor.scope,period_id))]}

    def removed_items(self,db,actor,period_id,workflow=None):
        latest={}
        for event in db.execute("SELECT * FROM accounting_events WHERE scope=? AND period_id=? AND code='ITEM_LEFT_POPULATION' ORDER BY id",(actor.scope,period_id)):
            value=json.loads(event['payload']);wf=value['workflow']
            if (workflow is None or wf==workflow) and self.governing_id(db,actor.scope,wf,period_id,event['item_key']) is None:
                latest[(wf,event['item_key'])]=dict(value,event_id=event['id'],period_id=period_id,item_key=event['item_key'])
        return list(latest.values())

    def record_population_departures(self,db,actor,run):
        if run['workflow'] not in ('card_preparation','journal_preparation'):return
        later=db.execute("SELECT 1 FROM runs WHERE scope=? AND workflow=? AND period_id=? AND id>? AND status IN ('awaiting_review','prepared_with_exceptions')",(actor.scope,run['workflow'],run['period_id'],run['id'])).fetchone()
        if later:return
        prior=db.execute("SELECT id FROM runs WHERE scope=? AND workflow=? AND period_id=? AND id<? AND status IN ('awaiting_review','prepared_with_exceptions') ORDER BY id DESC LIMIT 1",(actor.scope,run['workflow'],run['period_id'],run['id'])).fetchone()
        if not prior:return
        current={r['item_key'] for r in db.execute('SELECT a.item_key FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id WHERE l.scope=? AND l.run_id=?',(actor.scope,run['id']))}
        for a in db.execute("SELECT a.* FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id WHERE l.scope=? AND l.run_id=? AND a.kind IN ('card_proposal','journal_proposal')",(actor.scope,prior['id'])).fetchall():
            if a['item_key'] in current or a['item_key'] in ('no-transactions','no-journals'):continue
            original=next((e for e in json.loads(a['payload'])['data'].get('evidence',[]) if e['source_key']==a['item_key']),None)
            reference={}
            if original:
                snapshot=db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(actor.scope,original['snapshot_id'])).fetchone()
                head=db.execute('SELECT * FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(actor.scope,snapshot['kind'],a['item_key'])).fetchone()
                metadata=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(head['snapshot_id'],)).fetchone() if head else None
                binding=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(head['snapshot_id'],)).fetchone() if head else None
                links=[dict(r) for r in db.execute('SELECT * FROM source_links WHERE scope=? AND old_snapshot_id IN (SELECT id FROM snapshots WHERE scope=? AND kind=? AND source_key=?)',(actor.scope,actor.scope,snapshot['kind'],a['item_key']))]
                reference={'original_source':original,'head':dict(head) if head else None,'metadata':dict(metadata) if metadata else None,'binding':dict(binding) if binding else None,'supersession_links':links}
            value={'workflow':run['workflow'],'run_id':run['id'],'previous_artifact_id':a['id'],'previous_artifact_hash':a['hash'],'source_change':reference}
            self.accounting_event(db,actor,run['period_id'],a['item_key'],'ITEM_LEFT_POPULATION',value)
            for exc in db.execute("SELECT * FROM exceptions WHERE scope=? AND workflow=? AND period_id=? AND item_key=? AND status!='superseded'",(actor.scope,run['workflow'],run['period_id'],a['item_key'])).fetchall():
                db.execute("UPDATE exceptions SET status='superseded' WHERE scope=? AND workflow=? AND period_id=? AND item_key=? AND code=?",(actor.scope,run['workflow'],run['period_id'],a['item_key'],exc['code']))
                db.execute("INSERT INTO exception_history(scope,workflow,period_id,item_key,code,status,artifact_id,created) VALUES(?,?,?,?,?,'superseded',?,?)",(actor.scope,run['workflow'],run['period_id'],a['item_key'],exc['code'],exc['artifact_id'],utcnow()))

    def package_records(self,db,scope):
        rows=[dict(r) for r in db.execute('SELECT * FROM packages WHERE scope=? ORDER BY id',(scope,))]
        latest={(r['period_id'],r['workflow']):r['id'] for r in rows}
        return [dict(r,governing=latest[(r['period_id'],r['workflow'])]==r['id'],supersedes_package_id=json.loads(r['payload']).get('supersedes_package_id')) for r in rows]

    def finalize_package(self,actor,period_id,workflow,reason,acknowledgement=None):
        self.authorize(actor,('reviewer',));text_field(reason,'finalization reason',2000)
        with self.store.transaction() as db:
            self.require_grant(db,actor,'finalize')
            if self.period(db,actor,period_id)['status']=='locked':raise ControlError('PERIOD_LOCKED',409)
            ctx=self.context(db,actor,period_id,workflow)
            outcomes=self.period_outcomes(db,actor,period_id);items=[i for i in outcomes['items'] if i['workflow']==workflow]
            removed=self.removed_items(db,actor,period_id,workflow)
            if not items and not removed:raise ControlError('No preparation items to finalize',409)
            if any(i['status'] in ('disputed','stale') for i in items):raise ControlError('Stale/disputed items cannot be finalized',409)
            latest_run=db.execute("SELECT id FROM runs WHERE scope=? AND period_id=? AND workflow=? AND status IN ('awaiting_review','prepared_with_exceptions') ORDER BY id DESC LIMIT 1",(actor.scope,period_id,workflow)).fetchone()
            controls=db.execute('SELECT a.blockers FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id WHERE l.scope=? AND l.run_id=?',(actor.scope,latest_run['id'])).fetchall() if latest_run else []
            if any(package_blocker(c) for row in controls for c in json.loads(row['blockers'])):raise ControlError('Package control remains open',409)
            carried=[{'item_key':i['item_key'],'status':i['status'],'blockers':i['blockers']} for i in items if i['status']!='approve' or i['blockers']]
            if (carried or outcomes['quarantined_sources']) and not acknowledgement:raise ControlError('Unreviewed/carried exceptions require acknowledgement',409)
            if acknowledgement:text_field(acknowledgement,'acknowledgement',2000)
            for i in items+[{'id':r['previous_artifact_id']} for r in removed]:
                a=db.execute('SELECT * FROM artifacts WHERE scope=? AND id=?',(actor.scope,i['id'])).fetchone()
                contributors=self.contributors(db,actor.scope,a)
                if contributors is None or actor.id in contributors:raise ControlError('Independent finalizer required',403)
            head=db.execute('SELECT hash FROM audit WHERE scope=? ORDER BY id DESC LIMIT 1',(actor.scope,)).fetchone()
            previous=db.execute('SELECT id FROM packages WHERE scope=? AND period_id=? AND workflow=? ORDER BY id DESC LIMIT 1',(actor.scope,period_id,workflow)).fetchone()
            value={'supersedes_package_id':previous['id'] if previous else None,'scope':actor.scope,'period_id':period_id,'workflow':workflow,'items':items,'removed_items':removed,'manifest':ctx['manifest'],'dispositions':ctx['dispositions'],'rule_versions':ctx['manifest']['rules'],'open_exceptions':carried,'quarantined_sources':outcomes['quarantined_sources'],'acknowledgement':acknowledgement,'reason':reason,'audit_head':head['hash'] if head else None,'authority':'preparation_only_not_external_close','finalizer':actor.id}
            hashed=digest(value)
            pid=db.execute('INSERT INTO packages(scope,workflow,period_id,payload,hash,actor,created) VALUES(?,?,?,?,?,?,?)',(actor.scope,workflow,period_id,canonical(value),hashed,actor.id,utcnow())).lastrowid
            self.store.audit(db,actor.scope,actor.id,'preparation_package_finalized',{'package_id':pid,'hash':hashed})
            return pid

    def package_changes(self,db,actor):
        for p in db.execute('SELECT * FROM packages WHERE scope=?',(actor.scope,)).fetchall():
            value=json.loads(p['payload']);ctx=self.context(db,actor,p['period_id'],p['workflow'])
            current=[i for i in self.period_outcomes(db,actor,p['period_id'])['items'] if i['workflow']==p['workflow']]
            changed=digest(value['manifest'])!=digest(ctx['manifest']) or digest(value['items'])!=digest(current) or digest(value.get('quarantined_sources',[]))!=digest(self.period_outcomes(db,actor,p['period_id'])['quarantined_sources'])
            if changed and not db.execute("SELECT 1 FROM accounting_events WHERE scope=? AND code='POST_FINALIZATION_CHANGE' AND payload=?",(actor.scope,canonical({'package_id':p['id'],'current_fingerprint':ctx['fingerprint']}))).fetchone():
                self.accounting_event(db,actor,p['period_id'],'package:'+str(p['id']),'POST_FINALIZATION_CHANGE',{'package_id':p['id'],'current_fingerprint':ctx['fingerprint']})
