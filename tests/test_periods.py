import copy
import sqlite3
from pathlib import Path
from accounting_agent.core import Actor, ControlError, canonical, digest
from accounting_agent.demo import SCOPE, actor
from accounting_agent.service import AccountingOS
from tests import test_platform as helpers


class PeriodTests(helpers.PlatformCase):
    def test_late_locked_evidence_preserves_approval_until_reopen(self):
        self.drain();a=self.item('J-001','journal_preparation');self.review(a)
        self.os.lock_period(actor('reviewer'),'2026-11','Fictional lock',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        j=copy.deepcopy(next(s for s in self.packet['sources'] if s['key']=='J-001'));j['data']['memo']='Late fictional revision'
        self.intake_one(j,'locked-revision')
        state=self.os.state(actor());old=next(x for x in state['artifacts'] if x['id']==a['id'])
        self.assertEqual(old['review_status'],'approve')
        self.assertTrue(any(e['reason']=='LATE_ACTIVITY_IN_LOCKED_PERIOD' for e in state['source_exceptions']))
        with self.assertRaises(ControlError):self.os.enqueue(actor(),'journal_preparation','2026-11')
        self.os.reopen_period(actor('reviewer'),'2026-11','Review late fictional activity')
        self.assertEqual(next(x for x in self.os.state(actor())['artifacts'] if x['id']==a['id'])['review_status'],'stale')
        self.os.enqueue(actor(),'journal_preparation','2026-11');self.drain()
        self.assertEqual(self.item('J-001','journal_preparation')['payload']['data']['journal']['memo'],'Late fictional revision')

    def test_period_authority_overlap_and_scope_denied(self):
        with self.assertRaises(ControlError):self.os.lock_period(actor(),'2026-11','No permission',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        with self.assertRaises(ControlError):self.os.lock_period(Actor(actor().id,'reviewer','demo_org','bird_bowl_demo', kind="human"),'2026-11','Contributor',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        with self.assertRaises(ControlError):self.os.open_period(actor('reviewer'),'overlap','2026-11-15','2026-12-15','Overlap')
        with self.assertRaises(ControlError):self.os.lock_period(actor('reviewer',client='other_demo'),'2026-11','Cross scope',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")

    def test_dated_sources_route_once_to_their_own_period(self):
        self.drain();before=self.item('demo_card_001:TX-001');self.review(before)
        self.os.open_period(actor('reviewer'),'2026-10','2026-10-01','2026-10-31','Prior fictional period')
        rid=self.os.enqueue(actor(),'card_preparation','2026-10');self.drain()
        rows=[a for a in self.os.state(actor())['artifacts'] if a['run_id']==rid and a['kind']=='card_proposal']
        self.assertEqual([a['item_key'] for a in rows],['demo_card_001:TX-008'])
        self.assertNotIn('OUTSIDE_PERIOD',rows[0]['blockers'])
        # RV-13: a newly configured prior period creates a real continuity prerequisite.
        self.assertEqual(next(a for a in self.os.state(actor())['artifacts'] if a['id']==before['id'])['review_status'],'stale')
        self.os.enqueue(actor(),'card_preparation','2026-11');self.drain()
        self.assertIn('STATEMENT_PRIOR_PERIOD_MISSING',self.item('demo_card_001:TX-001')['blockers'])

    def test_concurrent_database_migration_is_idempotent(self):
        from concurrent.futures import ThreadPoolExecutor
        path=Path(self.temp.name)/'concurrent-legacy.sqlite3'
        db=sqlite3.connect(path);db.executescript((Path(__file__).parent/'schema_v1.sql').read_text());db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _:AccountingOS(path,[SCOPE]),range(2)))
        db=sqlite3.connect(path)
        self.assertEqual([r[0] for r in db.execute('SELECT version FROM schema_version ORDER BY version')],list(range(1,15)))
        self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[]);db.close()

    def test_legacy_migration_keeps_immutable_bytes_and_relationships(self):
        path=Path(self.temp.name)/'legacy.sqlite3'
        db=sqlite3.connect(path);db.executescript((Path(__file__).parent/'schema_v1.sql').read_text())
        profile=copy.deepcopy(self.profile);profile['period']={'start':'2026-11-01','end':'2026-11-30','locked':False}
        db.execute('INSERT INTO clients VALUES(?,?,?,?,?,?)',(SCOPE,'demo_org','bird_bowl_demo','local',1,1))
        db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?,?)',(1,SCOPE,'profile','profile',1,digest(profile),canonical(profile),'human-old','2026-11-01'))
        db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?)",(1,SCOPE,'journal_preparation','old-definition',1,'old-fingerprint','awaiting_review','old-enqueuer',None,None,'2026-11-01'))
        db.execute("INSERT INTO steps(id,scope,run_id,name,capability,needs,status) VALUES(1,?,1,'inventory','evidence.inventory','[]','complete')",(SCOPE,))
        payload='{"synthetic":true,"old_evidence":"unaltered"}'
        db.execute('INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?,?,?,?)',(1,SCOPE,1,1,'legacy','journal_proposal',payload,'old-hash','[]',1,'2026-11-01'))
        db.commit();db.close()
        migrated=AccountingOS(path,[SCOPE])
        with migrated.store.transaction() as db:
            self.assertEqual(db.execute('SELECT payload FROM artifacts WHERE id=1').fetchone()[0],payload)
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(db.execute('SELECT MAX(version) FROM schema_version').fetchone()[0],14)
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE artifacts SET payload='changed'")
        AccountingOS(path,[SCOPE])  # migration is idempotent


for _name in list(helpers.PlatformCase.__dict__):
    if _name.startswith('test_'):setattr(PeriodTests,_name,None)
