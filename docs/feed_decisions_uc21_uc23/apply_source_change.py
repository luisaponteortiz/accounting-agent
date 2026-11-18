"""Owner decision D-038: UC-21 (identical repeat of a row retired by a live replacement) and UC-22 (unordered message against an ordered row)."""
import sys
from pathlib import Path
root=Path(sys.argv[1])
def once(t,old,new):
    assert t.count(old)==1,(old[:80],t.count(old));return t.replace(old,new)
# ---- source_control.py
p=root/'accounting_agent/source_control.py';t=p.read_text()
t=once(t,"""        oldmeta=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(old['id'],)).fetchone() if old else None
        force=bool(old and int(removed)!=old['removed'])""","""        oldmeta=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(old['id'],)).fetchone() if old else None
        # D-038 / UC-21: an identical repeat of a receipt that was retired with its
        # replaced charge changes nothing while that replacement is live.
        if (kind=='receipt' and old and old['removed'] and not removed and old['hash']==digest(value) and oldmeta and not oldmeta['tombstone']
                and (as_of is None or (oldmeta['order_type']==order_type and oldmeta['as_of']==order_value))
                and self.retired_by_live_replacement(db,actor.scope,value['account_id']+':'+value['transaction_source_id'])):
            return old['id'],False
        force=bool(old and int(removed)!=old['removed'])""")
t=once(t,"""    def supersession_link(self,db,scope,snapshot_id):""","""    def retired_by_live_replacement(self,db,scope,key):
        \"\"\"D-038 / UC-21: this card row's head was retired by a replacement that still governs.

        A row the provider itself withdrew, a row whose replacement the provider
        withdrew, and a row no live row's governing chain reaches keep their
        earlier behaviour: restoration is not decided here (U4, UC-17).
        \"\"\"
        head=db.execute("SELECT h.removed,m.tombstone FROM source_heads h LEFT JOIN source_metadata m ON m.snapshot_id=h.snapshot_id WHERE h.scope=? AND h.kind='transaction' AND h.source_key=?",(scope,key)).fetchone()
        if not head or not head['removed'] or head['tombstone']:return False
        return any(ref['source_key']==key for live in self.store.latest(db,scope,'transaction') for ref in self.supersession_refs(db,scope,live['id']))

    def supersession_link(self,db,scope,snapshot_id):""")
p.write_text(t)
# ---- feed_contract.py
p=root/'accounting_agent/feed_contract.py';t=p.read_text()
t=once(t,"""CONFLICT='SOURCE_CLAIM_CONFLICT'
""","""CONFLICT='SOURCE_CLAIM_CONFLICT'
ORDER_MIXED='SOURCE_ORDER_MIXED'
""")
t=once(t,"""        same_row=bool(old and old['hash']==digest(value) and old['removed']==int(removed))
""","""        # D-038 / UC-21: a row retired by a live replacement is the same row when re-sent unchanged.
        retired=bool(old and old['removed'] and not removed and self.retired_by_live_replacement(db,actor.scope,key))
        same_row=bool(old and old['hash']==digest(value) and (old['removed']==int(removed) or retired))
""")
t=once(t,"""        if old and not accepted:
            retained=db.execute('SELECT s.id FROM snapshots s JOIN source_metadata m ON m.snapshot_id=s.id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND s.hash=? AND m.order_type=? AND m.as_of=? AND m.tombstone=? ORDER BY s.id DESC LIMIT 1',(actor.scope,kind,key,digest(value),order_type,order_value,int(removed))).fetchone()
            if retained:
""","""        if old and not accepted:
            # D-038 / UC-22: a message with no order value has only its arrival time,
            # so it is recognised on file by its content and kept once.
            unordered=order_type=='legacy_arrival'
            if unordered:retained=db.execute("SELECT s.id FROM snapshots s JOIN source_metadata m ON m.snapshot_id=s.id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND s.hash=? AND m.order_type='legacy_arrival' AND m.tombstone=? ORDER BY s.id DESC LIMIT 1",(actor.scope,kind,key,digest(value),int(removed))).fetchone()
            else:retained=db.execute('SELECT s.id FROM snapshots s JOIN source_metadata m ON m.snapshot_id=s.id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND s.hash=? AND m.order_type=? AND m.as_of=? AND m.tombstone=? ORDER BY s.id DESC LIMIT 1',(actor.scope,kind,key,digest(value),order_type,order_value,int(removed))).fetchone()
            if retained:
                if unordered:self.record_order_mixed(db,actor,key,old['id'],retained['id'],digest(value),meta['order_type'])
""")
t=once(t,"""            self.store.audit(db,actor.scope,actor.id,'older_or_conflicting_source_retained',{'snapshot_id':sid,'governing_snapshot_id':old['id']})
""","""            self.store.audit(db,actor.scope,actor.id,'older_or_conflicting_source_retained',{'snapshot_id':sid,'governing_snapshot_id':old['id']})
            if order_type=='legacy_arrival':self.record_order_mixed(db,actor,key,old['id'],sid,digest(value),meta['order_type'])
""")
t=once(t,"""    def apply_first_card_claim(self,db,actor,key,sid,target,predecessor,packet):""","""    def record_order_mixed(self,db,actor,key,governing_id,message_id,message_hash,governing_order):
        \"\"\"D-038 / UC-22: flag, once per distinct content, a message with no order value for a row governed by one.\"\"\"
        for event in db.execute('SELECT payload FROM accounting_events WHERE scope=? AND item_key=? AND code=?',(actor.scope,key,ORDER_MIXED)):
            if json.loads(event['payload']).get('message_hash')==message_hash:return False
        self.accounting_event(db,actor,None,key,ORDER_MIXED,{'snapshot_id':governing_id,'message_snapshot_id':message_id,'message_hash':message_hash,'governing_order_type':governing_order})
        self.store.audit(db,actor.scope,actor.id,'card_source_order_mixed',{'source_key':key,'message_snapshot_id':message_id,'governing_snapshot_id':governing_id,'governing_order_type':governing_order})
        return True

    def card_feed_anomalies(self,db,scope):
        \"\"\"Unordered messages retained against ordered card rows, for display and export.\"\"\"
        result=[]
        for event in db.execute('SELECT * FROM accounting_events WHERE scope=? AND code=? ORDER BY id',(scope,ORDER_MIXED)):
            value=json.loads(event['payload'])
            binding=db.execute('SELECT period_id FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(value['snapshot_id'],)).fetchone()
            result.append({'source_key':event['item_key'],'reason':ORDER_MIXED,'period_id':binding['period_id'] if binding else None,'message_snapshot_id':value['message_snapshot_id'],
                           'governing_snapshot_id':value['snapshot_id'],'governing_order_type':value['governing_order_type'],'event_id':event['id'],'created':event['created'],
                           'meaning':'A message with no order value was kept as evidence; it does not govern this row.'})
        return result

    def apply_first_card_claim(self,db,actor,key,sid,target,predecessor,packet):""")
p.write_text(t)
# ---- service.py: expose anomalies in state (and therefore export)
p=root/'accounting_agent/service.py';t=p.read_text()
t=once(t,"""                    "profile": ctx["profile"], "fingerprint": ctx["fingerprint"], "generation": ctx["generation"],
""","""                    "feed_anomalies": self.card_feed_anomalies(db,actor.scope),
                    "profile": ctx["profile"], "fingerprint": ctx["fingerprint"], "generation": ctx["generation"],
""")
p.write_text(t)
# ---- web page: show anomalies beside the source exceptions
p=root/'accounting_agent/web/app.js';t=p.read_text()
t=once(t,"""  $('source-exceptions').replaceChildren(...state.source_exceptions.map(e=>el('p',e.source_key+' · '+e.reason+' · '+(e.period_id||'period not configured'),'blocker')));""","""  $('source-exceptions').replaceChildren(...state.source_exceptions.map(e=>el('p',e.source_key+' · '+e.reason+' · '+(e.period_id||'period not configured'),'blocker')),...(state.feed_anomalies||[]).map(e=>el('p',e.source_key+' · '+e.reason+' · '+e.meaning,'blocker')));""")
p.write_text(t)
print('ok')
