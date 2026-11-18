"""Trusted execution/approval boundary shared by every accounting module."""
import json
import secrets
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path
from .core import (Actor, ControlError, SHARED_CONTROLS, canonical, day, digest,
                   instant, require_keys, text_field, utcnow)
from .modules import CAPABILITIES, WORKFLOWS, validate_source
from .storage import Store


class AccountingOS:
    def __init__(self, path, allowed_scopes, environment="local", mode="demo"):
        if environment != "local" or mode != "demo":
            raise ControlError("Only local/demo is implemented; hosted demo identity is forbidden", 403)
        self.allowed_scopes = frozenset(allowed_scopes)
        if not self.allowed_scopes or any(not s.endswith("/local") for s in self.allowed_scopes):
            raise ControlError("An explicit local client allowlist is required", 403)
        self.store = Store(path)
        # Conservative code/config lineage: code changes require renewed preparation/review.
        self.code_hash = digest({p.name: p.read_text() for p in Path(__file__).parent.glob("*.py")})

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
        require_keys(profile, {"schema_version", "version", "synthetic", "organization_id", "client_id", "name", "approval_status", "notice", "legal_entity", "accounting_framework", "accounting_basis", "external_company_id", "currency", "period", "accounts", "card_accounts", "vendors", "customers", "dimensions", "policies", "procedures", "historical_decisions", "credentials_reference", "systems", "required_close_evidence"})
        if (profile["synthetic"] is not True or profile["approval_status"] != "approved_demo_only" or
                profile["organization_id"] != actor.organization or profile["client_id"] != actor.client or
                profile["credentials_reference"] is not None):
            raise ControlError("Only scoped synthetic profiles without credentials are permitted", 403)
        for name in ("name", "version", "external_company_id", "currency"):
            text_field(profile[name], name)
        require_keys(profile["period"], {"start", "end", "locked"})
        if day(profile["period"]["start"]) > day(profile["period"]["end"]) or type(profile["period"]["locked"]) is not bool:
            raise ControlError("Invalid accounting period")
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
            if vendor["category"] is not None and vendor["category"] not in account_ids:
                raise ControlError("Vendor category must reference a configured account")
            vendor_ids.add(vendor["id"])
        for field in ("card_accounts", "required_close_evidence", "procedures"):
            for value in profile[field]:
                text_field(value, field)
            if len(set(profile[field])) != len(profile[field]):
                raise ControlError("Repeated profile value")
        if not set(profile["procedures"]).issubset(WORKFLOWS):
            raise ControlError("Profile references an unavailable workflow")
        # These are knowledge placeholders, not executable policy in this slice.
        if profile["customers"] or profile["dimensions"] or profile["historical_decisions"]:
            raise ControlError("Customer/dimension/decision activation is deferred; do not silently ignore it")

    def onboard(self, actor, profile):
        self.authorize(actor, ("preparer",))
        self.validate_profile(actor, profile)
        with self.store.transaction() as db:
            db.execute("INSERT OR IGNORE INTO clients(scope,organization,client,environment,generation) VALUES(?,?,?,?,0)",
                       (actor.scope, actor.organization, actor.client, actor.environment))
            old = self.store.latest(db, actor.scope, "profile")
            if old and old[0]["hash"] != digest(profile) and old[0]["value"]["version"] == profile["version"]:
                raise ControlError("A policy change requires a new explicit version", 409)
            sid, changed = self.store.snapshot(db, actor.scope, "profile", "profile", profile, actor.id)
            if changed:
                db.execute("UPDATE clients SET profile_id=?,generation=generation+1 WHERE scope=?", (sid, actor.scope))
                self.store.audit(db, actor.scope, actor.id, "profile_version_registered", {"snapshot_id": sid, "version": profile["version"], "authority": "synthetic_only"})
            return sid

    def context(self, db, actor):
        client = self.client(db, actor)
        profile_row = db.execute("SELECT * FROM snapshots WHERE id=? AND scope=?", (client["profile_id"], actor.scope)).fetchone()
        profile = json.loads(profile_row["payload"])
        sources = [s for s in self.store.latest(db, actor.scope) if s["kind"] not in ("profile", "batch")]
        manifest = {"profile_hash": profile_row["hash"], "sources": [(s["id"], s["hash"]) for s in sources], "code_hash": self.code_hash, "shared_controls": SHARED_CONTROLS}
        return {"scope": actor.scope, "generation": client["generation"], "profile": profile,
                "profile_ref": {"snapshot_id": profile_row["id"], "hash": profile_row["hash"], "version": profile["version"]},
                "sources": sources, "fingerprint": digest(manifest)}

    def intake(self, actor, packet):
        self.authorize(actor, ("preparer",))
        require_keys(packet, {"synthetic", "organization_id", "client_id", "external_company_id", "batch_id", "sources"})
        if packet["synthetic"] is not True or packet["organization_id"] != actor.organization or packet["client_id"] != actor.client:
            raise ControlError("Synthetic source scope mismatch", 403)
        text_field(packet["batch_id"], "batch_id")
        if not isinstance(packet["sources"], list) or not 1 <= len(packet["sources"]) <= 1000:
            raise ControlError("Intake requires 1–1000 sources")
        if len(canonical(packet).encode()) > 1024 * 1024:
            raise ControlError("Intake exceeds 1 MiB limit", 413)
        seen = set()
        for source in packet["sources"]:
            require_keys(source, {"kind", "key", "data"})
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
                return {"changed": False, "generation": ctx["generation"], "replay": True}
            size = db.execute("SELECT COALESCE(SUM(length(CAST(payload AS BLOB))),0) FROM snapshots WHERE scope=?", (actor.scope,)).fetchone()[0]
            if size + len(canonical(packet).encode()) * 2 > 10 * 1024 * 1024:
                raise ControlError("Synthetic client evidence quota exceeded", 413)
            self.store.snapshot(db, actor.scope, "batch", packet["batch_id"], packet, actor.id)
            changed = False
            for source in packet["sources"]:
                _, is_new = self.store.snapshot(db, actor.scope, source["kind"], source["key"], source["data"], actor.id)
                changed = changed or is_new
            if changed:
                db.execute("UPDATE clients SET generation=generation+1 WHERE scope=?", (actor.scope,))
            self.store.audit(db, actor.scope, actor.id, "source_intake", {"batch_id": packet["batch_id"], "source_count": len(packet["sources"]), "changed": changed, "prior_approvals_invalidated": changed})
            return {"changed": changed, "generation": ctx["generation"] + int(changed), "replay": False}

    def definition_hash(self, workflow):
        return digest(asdict(workflow))

    def _enqueue(self, db, actor, workflow_id, mandate_id=None, occurrence=None):
        ctx = self.context(db, actor)
        workflow = WORKFLOWS.get(workflow_id)
        if not workflow or workflow_id not in ctx["profile"]["procedures"]:
            raise ControlError("Workflow unavailable for this client", 403)
        for step in workflow.steps:
            cap = CAPABILITIES.get(step.capability)
            if not cap or not cap.handler or cap.effect != "prepare":
                raise ControlError("Workflow capability is unimplemented or denied", 403)
        if mandate_id is not None:
            prior = db.execute("SELECT id FROM runs WHERE mandate_id=? AND workflow=? AND occurrence=? AND scope=?", (mandate_id, workflow_id, occurrence, actor.scope)).fetchone()
            if prior:
                return prior["id"]
        else:
            prior = db.execute("SELECT id FROM runs WHERE scope=? AND workflow=? AND fingerprint=? AND status NOT IN ('failed','held') ORDER BY id DESC LIMIT 1", (actor.scope, workflow_id, ctx["fingerprint"])).fetchone()
            if prior:
                return prior["id"]
        run_id = db.execute("INSERT INTO runs(scope,workflow,definition_hash,generation,fingerprint,status,actor,mandate_id,occurrence,created) VALUES(?,?,?,?,?,'queued',?,?,?,?)", (actor.scope, workflow_id, self.definition_hash(workflow), ctx["generation"], ctx["fingerprint"], actor.id, mandate_id, occurrence, utcnow())).lastrowid
        for step in workflow.steps:
            db.execute("INSERT INTO steps(scope,run_id,name,capability,needs,status) VALUES(?,?,?,?,?,'queued')", (actor.scope, run_id, step.name, step.capability, canonical(step.needs)))
        self.store.audit(db, actor.scope, actor.id, "workflow_enqueued", {"run_id": run_id, "workflow": workflow_id, "mandate_id": mandate_id, "occurrence": occurrence})
        return run_id

    def enqueue(self, actor, workflow_id):
        self.authorize(actor, ("preparer",))
        with self.store.transaction() as db:
            return self._enqueue(db, actor, workflow_id)

    def _mandate_valid(self, db, run, now, use_simulated_clock=False):
        if run["mandate_id"] is None:
            return True
        if use_simulated_clock:
            clock = db.execute("SELECT simulated_now FROM demo_clock WHERE scope=?", (run["scope"],)).fetchone()
            if clock:
                now = instant(clock["simulated_now"])
        mandate = db.execute("SELECT * FROM mandates WHERE id=? AND scope=?", (run["mandate_id"], run["scope"])).fetchone()
        return bool(mandate and mandate["active"] and instant(mandate["starts"]) <= now < instant(mandate["ends"]) and run["workflow"] in json.loads(mandate["workflows"]))

    def _current(self, db, actor, run):
        workflow = WORKFLOWS.get(run["workflow"])
        return bool(workflow and run["fingerprint"] == self.context(db, actor)["fingerprint"] and run["definition_hash"] == self.definition_hash(workflow))

    def step_context(self, db, actor, job):
        ctx = self.context(db, actor)
        # Pass only declared, committed upstream outputs; modules cannot query the DB.
        ctx["dependencies"] = {}
        for name in json.loads(job["needs"]):
            rows = db.execute("SELECT a.id,a.hash,a.payload,a.blockers FROM artifacts a JOIN steps s ON s.id=a.step_id WHERE a.scope=? AND a.run_id=? AND s.name=? AND s.status='complete' ORDER BY a.id", (actor.scope, job["run_id"], name)).fetchall()
            ctx["dependencies"][name] = [{"artifact_id": r["id"], "hash": r["hash"], "payload": json.loads(r["payload"]), "blockers": json.loads(r["blockers"])} for r in rows]
        return ctx

    def claim(self, actor, now=None):
        self.authorize(actor, ("worker",))
        now_dt = instant(now or utcnow())
        with self.store.transaction() as db:
            self.client(db, actor)
            jobs = db.execute("SELECT s.* FROM steps s JOIN runs r ON r.id=s.run_id WHERE s.scope=? AND r.status IN ('queued','running') AND (s.status='queued' OR (s.status='running' AND s.lease_until<=?)) ORDER BY s.id", (actor.scope, now_dt.isoformat())).fetchall()
            for job in jobs:
                run = db.execute("SELECT * FROM runs WHERE id=? AND scope=?", (job["run_id"], actor.scope)).fetchone()
                if not self._current(db, actor, run) or not self._mandate_valid(db, run, now_dt, use_simulated_clock=now is None):
                    db.execute("UPDATE runs SET status='held' WHERE id=?", (run["id"],))
                    self.store.audit(db, actor.scope, actor.id, "run_held", {"run_id": run["id"], "reason": "stale_inputs_or_inactive_mandate"})
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
                db.execute("UPDATE runs SET status='held' WHERE id=?", (run["id"],))
                db.execute("UPDATE steps SET status='held',lease_token=NULL WHERE id=?", (job["id"],))
                self.store.audit(db, actor.scope, actor.id, "stale_result_discarded", {"run_id": run["id"], "step_id": job["id"]})
                return False
            if not isinstance(outputs, list) or not 1 <= len(outputs) <= 1000:
                raise ControlError("Module returned invalid output collection")
            ctx = self.step_context(db, actor, job)
            dependency_refs = {name: [{"artifact_id": a["artifact_id"], "hash": a["hash"]} for a in artifacts] for name, artifacts in ctx["dependencies"].items()}
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
                if ctx["profile"]["policies"]["model_review_required"] or WORKFLOWS[run["workflow"]].required_model_review:
                    blockers.append("MODEL_REVIEW_UNAVAILABLE")
                envelope = {"synthetic": True, "notice": "FICTIONAL DEMONSTRATION — no live accounting effects", "scope": actor.scope,
                            "workflow": run["workflow"], "workflow_version": WORKFLOWS[run["workflow"]].version,
                            "capability": job["capability"], "capability_version": CAPABILITIES[job["capability"]].version,
                            "shared_controls": SHARED_CONTROLS, "input_fingerprint": run["fingerprint"], "dependencies": dependency_refs,
                            "data": result["data"]}
                db.execute("INSERT INTO artifacts(scope,run_id,step_id,item_key,kind,payload,hash,blockers,eligible,created) VALUES(?,?,?,?,?,?,?,?,?,?)", (actor.scope, run["id"], job["id"], result["item_key"], result["kind"], canonical(envelope), digest(envelope), canonical(sorted(set(blockers))), int(result["eligible"] and not blockers), utcnow()))
            db.execute("UPDATE steps SET status='complete',lease_token=NULL,lease_until=NULL WHERE id=?", (job["id"],))
            incomplete = db.execute("SELECT COUNT(*) FROM steps WHERE run_id=? AND status!='complete'", (run["id"],)).fetchone()[0]
            if not incomplete:
                blocked = any(json.loads(r["blockers"]) for r in db.execute("SELECT blockers FROM artifacts WHERE run_id=? AND scope=?", (run["id"], actor.scope)))
                db.execute("UPDATE runs SET status=? WHERE id=?", ("prepared_with_exceptions" if blocked else "awaiting_review", run["id"]))
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

    def review(self, actor, artifact_id, artifact_hash, fingerprint, decision, reason):
        self.authorize(actor, ("reviewer",))
        if decision not in ("approve", "reject", "revoke"):
            raise ControlError("Unknown review decision")
        text_field(reason, "review reason", 2000)
        with self.store.transaction() as db:
            self.client(db, actor)
            artifact = db.execute("SELECT * FROM artifacts WHERE id=? AND scope=?", (artifact_id, actor.scope)).fetchone()
            if not artifact:
                raise ControlError("Artifact not found in client scope", 404)
            run = db.execute("SELECT * FROM runs WHERE id=? AND scope=?", (artifact["run_id"], actor.scope)).fetchone()
            if artifact["hash"] != artifact_hash or run["fingerprint"] != fingerprint:
                raise ControlError("Exact artifact/version mismatch", 409)
            if actor.id == run["actor"] or actor.id.startswith("worker"):
                raise ControlError("Independent human review required", 403)
            if decision != "revoke" and (not self._current(db, actor, run) or run["status"] in ("queued", "running", "failed", "held")):
                raise ControlError("Preparation is stale or unfinished; prepare current inputs", 409)
            if decision == "approve" and (not artifact["eligible"] or json.loads(artifact["blockers"])):
                raise ControlError("Unresolved controls block approval", 409)
            db.execute("INSERT INTO decisions(scope,artifact_id,artifact_hash,fingerprint,decision,reason,actor,created) VALUES(?,?,?,?,?,?,?,?)", (actor.scope, artifact_id, artifact_hash, fingerprint, decision, reason, actor.id, utcnow()))
            self.store.audit(db, actor.scope, actor.id, "review_" + decision, {"artifact_id": artifact_id, "artifact_hash": artifact_hash, "scope_of_approval": "preparation_only", "reason": reason})

    def create_mandate(self, actor, workflows, starts, ends, interval_seconds, max_occurrences):
        self.authorize(actor, ("preparer",))
        if not isinstance(workflows, list) or not workflows or len(set(workflows)) != len(workflows) or any(w not in WORKFLOWS for w in workflows):
            raise ControlError("Unknown mandate workflow")
        if instant(ends) <= instant(starts) or type(interval_seconds) is not int or not 60 <= interval_seconds <= 31536000 or type(max_occurrences) is not int or not 1 <= max_occurrences <= 100:
            raise ControlError("Invalid bounded mandate interval/window/limit")
        with self.store.transaction() as db:
            ctx = self.context(db, actor)
            if not set(workflows).issubset(ctx["profile"]["procedures"]):
                raise ControlError("Mandate exceeds client procedures", 403)
            mid = db.execute("INSERT INTO mandates(scope,workflows,starts,ends,interval_seconds,max_occurrences,active,issuer,created) VALUES(?,?,?,?,?,?,1,?,?)", (actor.scope, canonical(workflows), instant(starts).isoformat(), instant(ends).isoformat(), interval_seconds, max_occurrences, actor.id, utcnow())).lastrowid
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
                if not start <= now_dt < end:
                    continue
                occurrence_number = int((now_dt - start).total_seconds()) // mandate["interval_seconds"]
                # No unbounded catch-up: each tick considers the current occurrence only.
                occurrence = (start + timedelta(seconds=occurrence_number * mandate["interval_seconds"])).isoformat()
                for workflow in json.loads(mandate["workflows"]):
                    prior = db.execute("SELECT id FROM runs WHERE mandate_id=? AND workflow=? AND occurrence=? AND scope=?", (mandate["id"], workflow, occurrence, actor.scope)).fetchone()
                    if prior:
                        created.append(prior["id"])
                        continue
                    count = db.execute("SELECT COUNT(DISTINCT occurrence) FROM runs WHERE mandate_id=? AND scope=?", (mandate["id"], actor.scope)).fetchone()[0]
                    same_occurrence = db.execute("SELECT 1 FROM runs WHERE mandate_id=? AND occurrence=? AND scope=?", (mandate["id"], occurrence, actor.scope)).fetchone()
                    if count >= mandate["max_occurrences"] and not same_occurrence:
                        continue
                    created.append(self._enqueue(db, actor, workflow, mandate["id"], occurrence))
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
                a["payload"] = json.loads(a["payload"])
                a["blockers"] = json.loads(a["blockers"])
                run = runmap[a["run_id"]]
                a["current"] = run["current"] and run["status"] not in ("queued", "running", "held", "failed")
                a["fingerprint"] = run["fingerprint"]
                decisions = [dict(d) for d in db.execute("SELECT * FROM decisions WHERE artifact_id=? AND scope=? ORDER BY id", (a["id"], actor.scope))]
                a["decisions"] = decisions
                a["review_status"] = "stale" if not a["current"] else (decisions[-1]["decision"] if decisions else "pending")
                artifacts.append(a)
            audit = [dict(a) for a in db.execute("SELECT * FROM audit WHERE scope=? ORDER BY id DESC LIMIT 100", (actor.scope,))]
            mandates = [dict(m) for m in db.execute("SELECT * FROM mandates WHERE scope=? ORDER BY id DESC", (actor.scope,))]
            return {"synthetic": True, "environment": "local", "mode": "demo", "scope": actor.scope,
                    "notice": "Fictional sandbox; actual Bird Bowl accounting policies remain unconfigured.",
                    "profile": ctx["profile"], "fingerprint": ctx["fingerprint"], "generation": ctx["generation"],
                    "capabilities": [{k: v for k, v in asdict(c).items() if k != "handler"} for c in CAPABILITIES.values()],
                    "workflows": [asdict(w) for w in WORKFLOWS.values()],
                    "runs": runs, "artifacts": artifacts, "mandates": mandates, "audit": audit,
                    "sources": [{k: v for k, v in s.items() if k != "payload"} for s in ctx["sources"]],
                    "external": {"ledger": "unconnected", "models": "disabled", "model_calls": 0, "hosting": "not_deployed", "posting": "disabled", "final_close": "not_signed_off", "live_schedules": "disabled"}}

    def export(self, actor):
        state = self.state(actor)
        state["exported_at"] = utcnow()
        state["approval_scope"] = "Preparation review only. No posting, reconciliation or final close authority."
        # Include immutable versions and decisions for portable inspection, without active queue import.
        with self.store.transaction() as db:
            if self.context(db, actor)["fingerprint"] != state["fingerprint"]:
                raise ControlError("Inputs changed during export; retry for a consistent package", 409)
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
