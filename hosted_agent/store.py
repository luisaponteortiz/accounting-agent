"""SQLite store for the hosted agent. Every row belongs to exactly one client."""
import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone

MODES = ("prepare_only", "post_approved", "post_standing")
FEEDS = ("direct", "handoff")

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients(
 client_id TEXT PRIMARY KEY, name TEXT NOT NULL, realm_id TEXT NOT NULL UNIQUE,
 mode TEXT NOT NULL, auto_limit_cents INTEGER NOT NULL, spot_check_percent INTEGER NOT NULL,
 created TEXT NOT NULL, feed TEXT NOT NULL DEFAULT 'direct');
CREATE TABLE IF NOT EXISTS runs(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 job TEXT NOT NULL, started TEXT NOT NULL, finished TEXT, status TEXT NOT NULL, summary TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS proposals(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 run_id INTEGER NOT NULL REFERENCES runs(id), item_key TEXT NOT NULL, item TEXT NOT NULL,
 action TEXT, item_class TEXT NOT NULL, class_key TEXT NOT NULL, confidence REAL NOT NULL,
 evidence TEXT NOT NULL, brain TEXT NOT NULL, status TEXT NOT NULL, queue TEXT,
 reasons TEXT NOT NULL, standing_id INTEGER, created TEXT NOT NULL, closed TEXT,
 UNIQUE(client_id, item_key));
CREATE TABLE IF NOT EXISTS decisions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 proposal_id INTEGER NOT NULL REFERENCES proposals(id), actor TEXT NOT NULL, verdict TEXT NOT NULL,
 final_action TEXT, note TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS standing_approvals(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 item_class TEXT NOT NULL, class_key TEXT NOT NULL, max_amount_cents INTEGER NOT NULL,
 basis TEXT NOT NULL, granted_by TEXT NOT NULL, granted_at TEXT NOT NULL,
 ended_by TEXT, ended_at TEXT, ended_reason TEXT);
CREATE TABLE IF NOT EXISTS postings(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 proposal_id INTEGER NOT NULL REFERENCES proposals(id), realm_id TEXT NOT NULL, how TEXT NOT NULL,
 action TEXT NOT NULL, ledger_ref TEXT, read_back TEXT NOT NULL, verified INTEGER NOT NULL,
 actor TEXT NOT NULL, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feed_lines(
 client_id TEXT NOT NULL REFERENCES clients(client_id), item_key TEXT NOT NULL, item TEXT NOT NULL,
 status TEXT NOT NULL, received TEXT NOT NULL, carrier TEXT NOT NULL, PRIMARY KEY(client_id, item_key));
CREATE TABLE IF NOT EXISTS carrier_statements(
 client_id TEXT PRIMARY KEY REFERENCES clients(client_id), company TEXT NOT NULL, stated TEXT NOT NULL, carrier TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS instructions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL REFERENCES clients(client_id),
 proposal_id INTEGER NOT NULL REFERENCES proposals(id), action TEXT NOT NULL, how TEXT NOT NULL, actor TEXT NOT NULL,
 status TEXT NOT NULL, created TEXT NOT NULL, collected TEXT, done TEXT);
CREATE TABLE IF NOT EXISTS audit(
 id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL, actor TEXT NOT NULL,
 event TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL,
 created TEXT NOT NULL);
"""


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            if path != ":memory:":
                self.db.execute("PRAGMA journal_mode=WAL")
            self.db.executescript(SCHEMA)

    def close(self):
        self.db.close()

    # -- low level -------------------------------------------------------
    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        found = self.rows(sql, args)
        return found[0] if found else None

    def run(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).lastrowid

    # -- audit: an append-only chain, one per database ---------------------
    def audit(self, client_id, actor, event, payload):
        with self.lock:
            last = self.one("SELECT hash FROM audit ORDER BY id DESC LIMIT 1")
            prev = last["hash"] if last else "0" * 64
            created, body = now(), dumps(payload)
            digest = hashlib.sha256("|".join((prev, client_id, actor, event, body, created)).encode()).hexdigest()
            self.run("INSERT INTO audit(client_id,actor,event,payload,prev_hash,hash,created) VALUES(?,?,?,?,?,?,?)",
                     (client_id, actor, event, body, prev, digest, created))

    def verify_audit(self):
        prev = "0" * 64
        for r in self.rows("SELECT * FROM audit ORDER BY id"):
            expect = hashlib.sha256("|".join((prev, r["client_id"], r["actor"], r["event"], r["payload"], r["created"])).encode()).hexdigest()
            if r["prev_hash"] != prev or r["hash"] != expect:
                return False
            prev = r["hash"]
        return True

    # -- clients ---------------------------------------------------------
    def add_client(self, client_id, name, realm_id, mode="prepare_only", auto_limit_cents=250000,
                   spot_check_percent=10, actor="setup", feed="direct"):
        """feed: 'direct' (the agent reads and posts through its own connection) or 'handoff'
        (a carrier hands the bank feed in and posts what was approved; see handoff.py)."""
        if mode not in MODES:
            raise ValueError("unknown mode " + mode)
        if feed not in FEEDS:
            raise ValueError("unknown feed " + feed)
        self.run("INSERT INTO clients(client_id,name,realm_id,mode,auto_limit_cents,spot_check_percent,created,feed) VALUES(?,?,?,?,?,?,?,?)",
                 (client_id, name, str(realm_id), mode, auto_limit_cents, spot_check_percent, now(), feed))
        self.audit(client_id, actor, "client_added", {"name": name, "realm_id": str(realm_id), "mode": mode, "feed": feed})

    def client(self, client_id):
        found = self.one("SELECT * FROM clients WHERE client_id=?", (client_id,))
        if not found:
            raise KeyError("unknown client " + str(client_id))
        return found

    def clients(self):
        return self.rows("SELECT * FROM clients ORDER BY client_id")

    # -- proposals -------------------------------------------------------
    def proposal(self, proposal_id):
        r = self.one("SELECT * FROM proposals WHERE id=?", (proposal_id,))
        if not r:
            raise KeyError("unknown proposal " + str(proposal_id))
        return unpack(r)

    def proposals(self, client_id, status=None):
        sql, args = "SELECT * FROM proposals WHERE client_id=?", [client_id]
        if status:
            sql, args = sql + " AND status=?", args + [status]
        return [unpack(r) for r in self.rows(sql + " ORDER BY id", args)]

    def active_standing(self, client_id):
        return [dict(r, basis=json.loads(r["basis"])) for r in self.rows(
            "SELECT * FROM standing_approvals WHERE client_id=? AND ended_at IS NULL ORDER BY id", (client_id,))]


def unpack(row):
    for key in ("item", "action", "evidence", "reasons"):
        row[key] = json.loads(row[key]) if row[key] is not None else None
    return row
