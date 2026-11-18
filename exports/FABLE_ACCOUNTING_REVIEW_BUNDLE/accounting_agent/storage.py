"""Local durable repository. SQL is private to the application, never a model tool."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .core import ControlError, canonical, digest, utcnow

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
        with self.connect() as db:
            db.executescript(SCHEMA)
            # Evidence, outputs and decisions can only be appended through this repository.
            for table in ("snapshots", "artifacts", "decisions", "audit"):
                for op in ("UPDATE", "DELETE"):
                    db.execute("CREATE TRIGGER IF NOT EXISTS immutable_%s_%s BEFORE %s ON %s "
                               "BEGIN SELECT RAISE(ABORT, 'immutable record'); END" % (table, op, op, table))

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
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

    def snapshot(self, db, scope, kind, source_key, value, actor):
        latest = db.execute("SELECT * FROM snapshots WHERE scope=? AND kind=? AND source_key=? ORDER BY version DESC LIMIT 1",
                            (scope, kind, source_key)).fetchone()
        hashed = digest(value)
        if latest and latest["hash"] == hashed:
            return latest["id"], False
        version = latest["version"] + 1 if latest else 1
        result = db.execute("INSERT INTO snapshots(scope,kind,source_key,version,hash,payload,actor,created) VALUES(?,?,?,?,?,?,?,?)",
                            (scope, kind, source_key, version, hashed, canonical(value), actor, utcnow()))
        return result.lastrowid, True

    def latest(self, db, scope, kind=None):
        query = "SELECT s.* FROM snapshots s WHERE s.scope=?"
        values = [scope]
        if kind:
            query += " AND s.kind=?"
            values.append(kind)
        query += " AND s.version=(SELECT MAX(t.version) FROM snapshots t WHERE t.scope=s.scope AND t.kind=s.kind AND t.source_key=s.source_key) ORDER BY s.id"
        return [dict(r, value=json.loads(r["payload"])) for r in db.execute(query, values)]

    def backup(self, target):
        if Path(target).resolve() == Path(self.path).resolve() or Path(target).exists():
            raise ControlError("Backup requires a new destination distinct from the active database", 409)
        with self.connect() as source, sqlite3.connect(str(target)) as dest:
            source.backup(dest)
