"""Local durable repository. SQL is private to the application, never a model tool."""
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from .core import ControlError, canonical, digest, utcnow

BOOTSTRAP_LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO schema_version VALUES(1);
CREATE TABLE IF NOT EXISTS clients(
 scope TEXT PRIMARY KEY, organization TEXT NOT NULL, client TEXT NOT NULL,
 environment TEXT NOT NULL CHECK(environment='local'), generation INTEGER NOT NULL,
 profile_id INTEGER);
CREATE TABLE IF NOT EXISTS snapshots(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 kind TEXT NOT NULL, source_key TEXT NOT NULL, version INTEGER NOT NULL,
 hash TEXT NOT NULL, payload TEXT NOT NULL, actor TEXT NOT NULL, created TEXT NOT NULL,
 UNIQUE(scope,kind,source_key,version));
CREATE TABLE IF NOT EXISTS demo_clock(
 scope TEXT PRIMARY KEY REFERENCES clients(scope), simulated_now TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS mandates(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 workflows TEXT NOT NULL, starts TEXT NOT NULL, ends TEXT NOT NULL,
 interval_seconds INTEGER NOT NULL, max_occurrences INTEGER NOT NULL,
 active INTEGER NOT NULL, issuer TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 workflow TEXT NOT NULL, definition_hash TEXT NOT NULL, generation INTEGER NOT NULL,
 fingerprint TEXT NOT NULL, status TEXT NOT NULL, actor TEXT NOT NULL,
 mandate_id INTEGER REFERENCES mandates(id), occurrence TEXT, created TEXT NOT NULL,
 UNIQUE(mandate_id,workflow,occurrence));
CREATE TABLE IF NOT EXISTS steps(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 run_id INTEGER NOT NULL REFERENCES runs(id), name TEXT NOT NULL, capability TEXT NOT NULL,
 needs TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 lease_until TEXT, lease_token TEXT, error TEXT, UNIQUE(run_id,name));
CREATE TABLE IF NOT EXISTS artifacts(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 run_id INTEGER NOT NULL REFERENCES runs(id), step_id INTEGER NOT NULL REFERENCES steps(id),
 item_key TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, hash TEXT NOT NULL,
 blockers TEXT NOT NULL, eligible INTEGER NOT NULL, created TEXT NOT NULL,
 UNIQUE(step_id,item_key));
CREATE TABLE IF NOT EXISTS decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 artifact_id INTEGER NOT NULL REFERENCES artifacts(id), artifact_hash TEXT NOT NULL,
 fingerprint TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL,
 actor TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope),
 actor TEXT NOT NULL, event TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL,
 prev_hash TEXT NOT NULL, hash TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS jobs_claim ON steps(status,lease_until);
CREATE INDEX IF NOT EXISTS source_lookup ON snapshots(scope,kind,source_key,version);
CREATE INDEX IF NOT EXISTS artifacts_scope ON artifacts(scope,run_id);
"""


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with BOOTSTRAP_LOCK:
            with self.connect() as db:
                db.executescript(SCHEMA)
                self.migrate(db)
                # Evidence, outputs and decisions can only be appended through this repository.
                for table in ("snapshots", "artifacts", "decisions", "audit", "period_history", "source_periods", "artifact_runs", "artifact_contributors", "source_moves", "authority_grants", "profile_proposals", "profile_decisions", "policy_rules", "rule_decisions", "source_metadata", "source_links", "accounting_events", "exception_history", "dispositions", "packages", "rule_retirements"):
                    for op in ("UPDATE", "DELETE"):
                        db.execute("CREATE TRIGGER IF NOT EXISTS immutable_%s_%s BEFORE %s ON %s "
                                   "BEGIN SELECT RAISE(ABORT, 'immutable record'); END" % (table, op, op, table))

    def migrate(self, db):
        version = db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        if version < 2:
            # Rebuild the mutable runs table only; immutable evidence/audit bytes stay intact.
            db.execute("PRAGMA foreign_keys=OFF")
            try:
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=2:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE occurrences(id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope), mandate_id INTEGER NOT NULL REFERENCES mandates(id), workflow TEXT NOT NULL, occurrence_key TEXT NOT NULL, status TEXT NOT NULL, reason TEXT, completed_run_id INTEGER, created TEXT NOT NULL, UNIQUE(mandate_id,workflow,occurrence_key))")
                db.execute("ALTER TABLE mandates ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
                db.execute("ALTER TABLE mandates ADD COLUMN reason TEXT")
                db.execute("ALTER TABLE mandates ADD COLUMN last_tick TEXT")
                db.execute("CREATE TABLE runs_v2(id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL REFERENCES clients(scope), workflow TEXT NOT NULL, definition_hash TEXT NOT NULL, generation INTEGER NOT NULL, fingerprint TEXT NOT NULL, status TEXT NOT NULL, actor TEXT NOT NULL, mandate_id INTEGER REFERENCES mandates(id), occurrence TEXT, created TEXT NOT NULL, occurrence_id INTEGER REFERENCES occurrences(id))")
                db.execute("INSERT INTO runs_v2(id,scope,workflow,definition_hash,generation,fingerprint,status,actor,mandate_id,occurrence,created) SELECT id,scope,workflow,definition_hash,generation,fingerprint,status,actor,mandate_id,occurrence,created FROM runs")
                db.execute("DROP TABLE runs")
                db.execute("ALTER TABLE runs_v2 RENAME TO runs")
                for r in db.execute("SELECT * FROM runs WHERE mandate_id IS NOT NULL").fetchall():
                    done = r["status"] in ('awaiting_review','prepared_with_exceptions')
                    oid = db.execute("INSERT INTO occurrences(scope,mandate_id,workflow,occurrence_key,status,completed_run_id,created) VALUES(?,?,?,?,?,?,?)", (r["scope"],r["mandate_id"],r["workflow"],r["occurrence"], 'completed' if done else 'held' if r["status"] in ('held','failed') else 'dispatched',r["id"] if done else None,r["created"])).lastrowid
                    db.execute("UPDATE runs SET occurrence_id=? WHERE id=?",(oid,r["id"]))
                db.execute("CREATE UNIQUE INDEX one_completed_run_per_occurrence ON runs(occurrence_id) WHERE occurrence_id IS NOT NULL AND status IN ('awaiting_review','prepared_with_exceptions')")
                db.execute("INSERT INTO schema_version VALUES(2)")
                for c in db.execute("SELECT scope FROM clients").fetchall():
                    self.audit(db,c["scope"],"service-migration","schema_migrated",{"version":2})
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ControlError("Migration would break database relationships")
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.execute("PRAGMA foreign_keys=ON")

        version = db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        if version < 3:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=3:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE periods(scope TEXT NOT NULL REFERENCES clients(scope), period_id TEXT NOT NULL, start TEXT NOT NULL,end TEXT NOT NULL,status TEXT NOT NULL,changed_by TEXT NOT NULL,changed_at TEXT NOT NULL,reason TEXT NOT NULL,PRIMARY KEY(scope,period_id))")
                db.execute("CREATE TABLE period_history(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL,period_id TEXT NOT NULL,status TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL,reason TEXT NOT NULL,FOREIGN KEY(scope,period_id) REFERENCES periods(scope,period_id))")
                db.execute("CREATE TABLE source_periods(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),period_id TEXT,admitted INTEGER NOT NULL,reason TEXT,created TEXT NOT NULL,FOREIGN KEY(scope,period_id) REFERENCES periods(scope,period_id))")
                db.execute("CREATE TABLE frozen_runs(scope TEXT NOT NULL,period_id TEXT NOT NULL,run_id INTEGER NOT NULL REFERENCES runs(id),PRIMARY KEY(scope,period_id,run_id))")
                db.execute("ALTER TABLE runs ADD COLUMN period_id TEXT")
                for c in db.execute("SELECT * FROM clients").fetchall():
                    profile=db.execute("SELECT * FROM snapshots WHERE id=?",(c['profile_id'],)).fetchone()
                    value=json.loads(profile['payload']);period=value.get('period')
                    if not period:continue
                    pid=period['start'][:7];status='locked' if period.get('locked') else 'open'
                    db.execute("INSERT INTO periods VALUES(?,?,?,?,?,?,?,?)",(c['scope'],pid,period['start'],period['end'],status,'service-migration',utcnow(),'Legacy fictional period migration'))
                    db.execute("INSERT INTO period_history(scope,period_id,status,actor,created,reason) VALUES(?,?,?,?,?,?)",(c['scope'],pid,status,'service-migration',utcnow(),'Legacy fictional period migration'))
                    db.execute("UPDATE runs SET period_id=? WHERE scope=?",(pid,c['scope']))
                    for snap in self.latest(db,c['scope']):
                        if snap['kind'] in ('batch','profile'):continue
                        d=snap['value'].get('date');admitted=not d or period['start']<=d<=period['end']
                        db.execute("INSERT INTO source_periods(scope,snapshot_id,period_id,admitted,reason,created) VALUES(?,?,?,?,?,?)",(c['scope'],snap['id'],pid if admitted else None,int(admitted),None if admitted else 'UNASSIGNED_ACCOUNTING_PERIOD',utcnow()))
                    self.audit(db,c['scope'],'service-migration','schema_migrated',{'version':3})
                db.execute("INSERT INTO schema_version VALUES(3)");db.commit()
            except Exception:
                db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 4:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=4:
                    db.rollback();self.migrate(db);return
                db.execute("ALTER TABLE runs ADD COLUMN manifest TEXT NOT NULL DEFAULT '{}'")
                db.execute("INSERT INTO schema_version VALUES(4)");db.commit()
            except Exception:
                db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 5:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=5:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE artifact_runs(scope TEXT NOT NULL REFERENCES clients(scope),run_id INTEGER NOT NULL REFERENCES runs(id),step_id INTEGER NOT NULL REFERENCES steps(id),artifact_id INTEGER NOT NULL REFERENCES artifacts(id),PRIMARY KEY(run_id,step_id,artifact_id))")
                db.execute("INSERT INTO artifact_runs SELECT scope,run_id,step_id,id FROM artifacts")
                db.execute("CREATE INDEX artifact_link_lookup ON artifact_runs(scope,artifact_id,run_id)")
                db.execute("INSERT INTO schema_version VALUES(5)");db.commit()
            except Exception:
                db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 6:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=6:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE artifact_contributors(scope TEXT NOT NULL REFERENCES clients(scope),artifact_id INTEGER NOT NULL REFERENCES artifacts(id),actor TEXT NOT NULL,lineage_role TEXT NOT NULL,run_id INTEGER NOT NULL REFERENCES runs(id),PRIMARY KEY(scope,artifact_id,actor,lineage_role,run_id))")
                for r in db.execute("SELECT a.id,a.scope,a.payload,l.run_id FROM artifacts a JOIN artifact_runs l ON l.artifact_id=a.id").fetchall():
                    for actor in json.loads(r['payload']).get('contributors',[]):
                        db.execute("INSERT OR IGNORE INTO artifact_contributors VALUES(?,?,?,?,?)",(r['scope'],r['id'],actor,'legacy_envelope',r['run_id']))
                db.execute("INSERT INTO schema_version VALUES(6)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 7:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=7:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE source_moves(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),from_period_id TEXT NOT NULL,to_period_id TEXT,blocked INTEGER NOT NULL,had_approval INTEGER NOT NULL,created TEXT NOT NULL)")
                db.execute("INSERT INTO schema_version VALUES(7)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 8:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=8:
                    db.rollback();self.migrate(db);return
                statements=[
                    "CREATE TABLE authority_grants(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),subject TEXT NOT NULL,permission TEXT NOT NULL,effective_from TEXT NOT NULL,effective_to TEXT NOT NULL,issuer TEXT NOT NULL,reason TEXT NOT NULL,synthetic INTEGER NOT NULL)",
                    "CREATE TABLE profile_proposals(scope TEXT NOT NULL REFERENCES clients(scope),snapshot_id INTEGER PRIMARY KEY REFERENCES snapshots(id),effective_from TEXT NOT NULL,effective_to TEXT)",
                    "CREATE TABLE profile_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),decision TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL,created TEXT NOT NULL)",
                    "CREATE TABLE policy_rules(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),kind TEXT NOT NULL,rule_key TEXT NOT NULL,version INTEGER NOT NULL,value TEXT NOT NULL,effective_from TEXT NOT NULL,effective_to TEXT,item_key TEXT,supersedes INTEGER REFERENCES policy_rules(id),proposed_by TEXT NOT NULL,proposer_kind TEXT NOT NULL,evidence TEXT NOT NULL,profile_id INTEGER REFERENCES snapshots(id),UNIQUE(scope,kind,rule_key,version))",
                    "CREATE TABLE rule_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),rule_id INTEGER NOT NULL REFERENCES policy_rules(id),decision TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL,created TEXT NOT NULL)"]
                for statement in statements:db.execute(statement)
                db.execute("INSERT INTO schema_version VALUES(8)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 9:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=9:
                    db.rollback();self.migrate(db);return
                for statement in ["CREATE TABLE source_metadata(snapshot_id INTEGER PRIMARY KEY REFERENCES snapshots(id),scope TEXT NOT NULL REFERENCES clients(scope),source_system TEXT NOT NULL,order_type TEXT NOT NULL,as_of TEXT NOT NULL,tombstone INTEGER NOT NULL,removal_reason TEXT,period_hint TEXT)","CREATE TABLE source_heads(scope TEXT NOT NULL REFERENCES clients(scope),kind TEXT NOT NULL,source_key TEXT NOT NULL,snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),removed INTEGER NOT NULL,PRIMARY KEY(scope,kind,source_key))","CREATE TABLE source_links(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),old_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),new_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),reason TEXT NOT NULL,created TEXT NOT NULL)","CREATE TABLE accounting_events(id INTEGER PRIMARY KEY AUTOINCREMENT,scope TEXT NOT NULL REFERENCES clients(scope),period_id TEXT,item_key TEXT NOT NULL,code TEXT NOT NULL,payload TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL)"]:
                    db.execute(statement)
                for s in db.execute("SELECT * FROM snapshots s WHERE kind NOT IN ('profile','batch') AND version=(SELECT MAX(t.version) FROM snapshots t WHERE t.scope=s.scope AND t.kind=s.kind AND t.source_key=s.source_key)").fetchall():
                    db.execute('INSERT INTO source_heads VALUES(?,?,?,?,0)',(s['scope'],s['kind'],s['source_key'],s['id']))
                    db.execute('INSERT INTO source_metadata VALUES(?,?,?,?,?,0,NULL,NULL)',(s['id'],s['scope'],'fixture','legacy_arrival',s['created']))
                db.execute("INSERT INTO schema_version VALUES(9)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 10:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=10:
                    db.rollback();self.migrate(db);return
                db.execute("ALTER TABLE mandates ADD COLUMN period_rule TEXT NOT NULL DEFAULT '"+canonical({'kind':'occurrence_calendar'})+"'")
                db.execute("ALTER TABLE mandates ADD COLUMN freshness TEXT NOT NULL DEFAULT '{}'")
                db.execute("ALTER TABLE mandates ADD COLUMN bound_rules TEXT NOT NULL DEFAULT '{}'")
                db.execute("ALTER TABLE mandates ADD COLUMN approved_by TEXT")
                db.execute("UPDATE mandates SET active=0,status='needs_reconfirmation',reason='Legacy standing authority requires independent approval'")
                db.execute("INSERT INTO schema_version VALUES(10)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 11:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=11:
                    db.rollback();self.migrate(db);return
                for sql in ["CREATE TABLE exceptions(scope TEXT NOT NULL,workflow TEXT NOT NULL,period_id TEXT NOT NULL,item_key TEXT NOT NULL,code TEXT NOT NULL,status TEXT NOT NULL,artifact_id INTEGER NOT NULL REFERENCES artifacts(id),PRIMARY KEY(scope,workflow,period_id,item_key,code))","CREATE TABLE exception_history(id INTEGER PRIMARY KEY,scope TEXT NOT NULL,workflow TEXT NOT NULL,period_id TEXT NOT NULL,item_key TEXT NOT NULL,code TEXT NOT NULL,status TEXT NOT NULL,artifact_id INTEGER NOT NULL,created TEXT NOT NULL)","CREATE TABLE dispositions(id INTEGER PRIMARY KEY,scope TEXT NOT NULL,workflow TEXT NOT NULL,period_id TEXT NOT NULL,item_key TEXT NOT NULL,code TEXT NOT NULL,choice TEXT NOT NULL,payload TEXT NOT NULL,evidence TEXT NOT NULL,source_hash TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL,action TEXT NOT NULL,prior_id INTEGER,created TEXT NOT NULL)"]:
                    db.execute(sql)
                db.execute("INSERT INTO schema_version VALUES(11)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 12:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=12:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE packages(id INTEGER PRIMARY KEY,scope TEXT NOT NULL,workflow TEXT NOT NULL,period_id TEXT NOT NULL,payload TEXT NOT NULL,hash TEXT NOT NULL,actor TEXT NOT NULL,created TEXT NOT NULL)")
                db.execute("INSERT INTO schema_version VALUES(12)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 13:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=13:
                    db.rollback();self.migrate(db);return
                db.execute("CREATE TABLE rule_retirements(id INTEGER PRIMARY KEY,scope TEXT NOT NULL REFERENCES clients(scope),rule_id INTEGER NOT NULL REFERENCES policy_rules(id),effective_to TEXT NOT NULL,actor TEXT NOT NULL,profile_id INTEGER NOT NULL REFERENCES snapshots(id),created TEXT NOT NULL,UNIQUE(scope,rule_id,profile_id))")
                db.execute("INSERT INTO schema_version VALUES(13)");db.commit()
            except Exception:db.rollback();raise

        if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] < 14:
            db.execute("BEGIN IMMEDIATE")
            try:
                if db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]>=14:
                    db.rollback();self.migrate(db);return
                for mandate in db.execute('SELECT * FROM mandates').fetchall():
                    if not json.loads(mandate['freshness']):
                        db.execute("UPDATE mandates SET active=0,status='needs_reconfirmation',reason='Empty legacy freshness requires explicit replacement authority' WHERE id=?",(mandate['id'],))
                        self.audit(db,mandate['scope'],'service-migration','legacy_mandate_suspended',{'mandate_id':mandate['id'],'reason':'empty_freshness'})
                db.execute("INSERT INTO schema_version VALUES(14)");db.commit()
            except Exception:db.rollback();raise

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        # journal_mode changes do not always honor busy_timeout during concurrent startup.
        for attempt in range(100):
            try:
                if db.execute("PRAGMA journal_mode").fetchone()[0]!='wal':
                    db.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError as exc:
                if 'locked' not in str(exc).lower() or attempt==99:
                    db.close();raise
                time.sleep(0.01)
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def audit(self, db, scope, actor, event, payload):
        last = db.execute("SELECT hash FROM audit WHERE scope=? ORDER BY id DESC LIMIT 1", (scope,)).fetchone()
        prev = last["hash"] if last else "0" * 64
        created = utcnow()
        record = {"scope": scope, "actor": actor, "event": event, "payload": payload, "created": created, "prev_hash": prev}
        db.execute("INSERT INTO audit(scope,actor,event,payload,created,prev_hash,hash) VALUES(?,?,?,?,?,?,?)",
                   (scope, actor, event, canonical(payload), created, prev, digest(record)))

    def snapshot(self, db, scope, kind, source_key, value, actor, force_version=False):
        latest = db.execute("SELECT * FROM snapshots WHERE scope=? AND kind=? AND source_key=? ORDER BY version DESC LIMIT 1",
                            (scope, kind, source_key)).fetchone()
        hashed = digest(value)
        if latest and latest["hash"] == hashed and not force_version:
            return latest["id"], False
        version = latest["version"] + 1 if latest else 1
        result = db.execute("INSERT INTO snapshots(scope,kind,source_key,version,hash,payload,actor,created) VALUES(?,?,?,?,?,?,?,?)",
                            (scope, kind, source_key, version, hashed, canonical(value), actor, utcnow()))
        return result.lastrowid, True

    def latest(self, db, scope, kind=None, include_removed=False):
        query = "SELECT s.* FROM snapshots s WHERE s.scope=?"
        values = [scope]
        if kind:
            query += " AND s.kind=?"
            values.append(kind)
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_heads'").fetchone():
            query += " AND ((s.kind IN ('profile','batch') AND s.version=(SELECT MAX(t.version) FROM snapshots t WHERE t.scope=s.scope AND t.kind=s.kind AND t.source_key=s.source_key)) OR (s.kind NOT IN ('profile','batch') AND s.id=(SELECT h.snapshot_id FROM source_heads h WHERE h.scope=s.scope AND h.kind=s.kind AND h.source_key=s.source_key"+('' if include_removed else ' AND h.removed=0')+"))) ORDER BY s.id"
        else:
            query += " AND s.version=(SELECT MAX(t.version) FROM snapshots t WHERE t.scope=s.scope AND t.kind=s.kind AND t.source_key=s.source_key) ORDER BY s.id"
        return [dict(r, value=json.loads(r["payload"])) for r in db.execute(query, values)]

    def backup(self, target):
        if Path(target).resolve() == Path(self.path).resolve() or Path(target).exists():
            raise ControlError("Backup requires a new destination distinct from the active database", 409)
        with self.connect() as source, sqlite3.connect(str(target)) as dest:
            source.backup(dest)
