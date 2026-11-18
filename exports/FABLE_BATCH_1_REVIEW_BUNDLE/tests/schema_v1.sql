
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
