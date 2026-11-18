"""One unattended run for one client: check the company, read the bank feed,
propose, post what a person already approved, queue the rest, leave a record."""
from .brain import Context
from .ledger import LedgerError
from .policy import hard_stops, route, same_treatment
from .store import dumps, now

AGENT = "agent"


class Blocked(Exception):
    pass


def preflight(store, ledger, client_id):
    """The company the ledger returns must be the one this client was set up
    with. Checked before every run and again before every posting."""
    client = store.client(client_id)
    try:
        company = ledger.company(client["realm_id"])
    except LedgerError as error:
        raise Blocked(str(error))
    if str(company["realm_id"]) != client["realm_id"] or company["name"] != client["name"]:
        raise Blocked("company check failed: expected %s (%s), the ledger returned %s (%s)" % (
            client["name"], client["realm_id"], company["name"], company["realm_id"]))
    return client, company


def execute(store, ledger, proposal_id, action, how, actor):
    """Post one approved treatment and read it back. The only function that writes to a ledger."""
    p = store.proposal(proposal_id)
    client, company = preflight(store, ledger, p["client_id"])
    if client["mode"] == "prepare_only":
        raise Blocked("client is in prepare-only mode; nothing posts")
    stops = hard_stops(p["item"], action, company)
    if stops:
        raise Blocked("; ".join(stops))
    realm, feed_id = client["realm_id"], p["item"]["id"]
    try:
        if action["kind"] == "categorize":
            ref = ledger.categorize(realm, feed_id, action["account"], action.get("vendor"), action.get("memo", ""))
        elif action["kind"] == "match":
            ref = ledger.match(realm, feed_id, action["txn_type"], action["txn_id"])
        elif action["kind"] == "transfer":
            ref = ledger.transfer(realm, feed_id, action["other_account"])
        else:
            raise LedgerError("unknown action " + str(action.get("kind")))
        back = ledger.read_back(realm, feed_id)
        error = None
    except LedgerError as problem:
        ref, back, error = None, {}, str(problem)
    verified = bool(ref) and verify(p["item"], action, back, ref)
    store.run("INSERT INTO postings(client_id,proposal_id,realm_id,how,action,ledger_ref,read_back,verified,actor,created) VALUES(?,?,?,?,?,?,?,?,?,?)",
              (p["client_id"], proposal_id, realm, how, dumps(action), ref, dumps(back), int(verified), actor, now()))
    if verified:
        store.run("UPDATE proposals SET status='posted', queue=NULL, closed=? WHERE id=?", (now(), proposal_id))
        store.audit(p["client_id"], actor, "posted", {"proposal": proposal_id, "how": how, "ledger_ref": ref})
    else:
        reason = "posting failed: " + error if error else "read-back did not match what was sent"
        store.run("UPDATE proposals SET status='waiting', queue='exception', reasons=? WHERE id=?", (dumps([reason]), proposal_id))
        store.audit(p["client_id"], actor, "posting_not_verified", {"proposal": proposal_id, "how": how, "ledger_ref": ref, "reason": reason})
    return verified


def verify(item, action, back, ref):
    posted = back.get("posted") or {}
    if posted.get("id") != ref or posted.get("amount_cents") != item["amount_cents"] or posted.get("date") != item["date"]:
        return False
    if action["kind"] == "categorize":
        return posted.get("account") == action["account"] and posted.get("vendor") == action.get("vendor")
    if action["kind"] == "match":
        return posted.get("matched_id") == action["txn_id"]
    return posted.get("account") == action["other_account"]


def treatment_of(posted):
    """The treatment a person gave a line outside the agent, in the agent's terms."""
    if posted.get("kind") == "match":
        return dict(kind="match", txn_type=posted.get("matched_type"), txn_id=posted.get("matched_id"))
    if posted.get("kind") == "transfer":
        return dict(kind="transfer", other_account=posted.get("account"))
    return dict(kind="categorize", account=posted.get("account"), vendor=posted.get("vendor"))


def observe(store, ledger, client_id):
    """If a person handled a waiting line directly in the books, record whether
    they did what the agent proposed. This is how agreement is measured before
    the agent is allowed to post anything."""
    client, _ = preflight(store, ledger, client_id)
    seen = 0
    for p in store.proposals(client_id, "waiting"):
        if store.one("SELECT 1 FROM postings WHERE proposal_id=?", (p["id"],)):
            continue  # the agent's own attempt, not a person's work: stays with a reviewer
        back = ledger.read_back(client["realm_id"], p["item"]["id"])
        if back["status"] == "pending" or not back.get("posted"):
            continue
        done = treatment_of(back["posted"])
        verdict = "approve" if same_treatment(p["action"], done) else "change"
        store.run("INSERT INTO decisions(client_id,proposal_id,actor,verdict,final_action,note,created) VALUES(?,?,?,?,?,?,?)",
                  (client_id, p["id"], "observed-in-books", verdict, dumps(done), "handled directly in the books", now()))
        store.run("UPDATE proposals SET status=?, queue=NULL, closed=? WHERE id=?",
                  ("observed_same" if verdict == "approve" else "observed_different", now(), p["id"]))
        store.audit(client_id, "observed-in-books", "observed", {"proposal": p["id"], "verdict": verdict})
        if verdict == "change":
            suspend_on_disagreement(store, p, "observed-in-books")
        seen += 1
    return seen


def suspend_on_disagreement(store, p, actor):
    """A person disagreed with an item in a class that has a standing approval: the approval ends."""
    for s in store.active_standing(p["client_id"]):
        if s["item_class"] == p["item_class"] and s["class_key"] == p["class_key"]:
            store.run("UPDATE standing_approvals SET ended_by=?, ended_at=?, ended_reason=? WHERE id=?",
                      ("system", now(), "a reviewer disagreed with proposal %s" % p["id"], s["id"]))
            store.audit(p["client_id"], "system", "standing_approval_suspended", {"standing": s["id"], "proposal": p["id"], "after": actor})


def reroute(store, ledger, client_id, post):
    """Apply today's mode and standing approvals to items that are already
    waiting. With post=True (a run), items a person has since covered are
    posted; otherwise they are only relabelled. A posting that failed stays
    with a person."""
    client, company = preflight(store, ledger, client_id)
    standing, posted = store.active_standing(client_id), 0
    for p in store.proposals(client_id, "waiting"):
        if store.one("SELECT 1 FROM postings WHERE proposal_id=? AND verified=0", (p["id"],)):
            continue
        prop = dict(action=p["action"], item_class=p["item_class"], class_key=p["class_key"], confidence=p["confidence"])
        queue, reasons, standing_id = route(client, company, p["item"], prop, standing)
        if queue == "auto":
            if not post:
                queue, reasons = "prepared", ["covered by a standing approval; posts on the next run"]
            else:
                try:
                    posted += bool(execute(store, ledger, p["id"], p["action"], "standing", AGENT))
                    continue
                except Blocked as stop:
                    queue, reasons = "exception", [str(stop)]
        store.run("UPDATE proposals SET queue=?, reasons=?, standing_id=? WHERE id=?", (queue, dumps(reasons), standing_id, p["id"]))
    return posted


def run_client(store, ledger, brain, client_id, job="bank_feed"):
    started = now()
    run_id = store.run("INSERT INTO runs(client_id,job,started,status,summary) VALUES(?,?,?,?,?)",
                       (client_id, job, started, "running", "{}"))
    counts = dict(read=0, new=0, auto_posted=0, spot_check=0, prepared=0, exception=0, failed=0, observed=0)
    try:
        client, company = preflight(store, ledger, client_id)
    except Blocked as stop:
        store.run("UPDATE runs SET finished=?, status='blocked', summary=? WHERE id=?", (now(), dumps({"blocked": str(stop)}), run_id))
        store.audit(client_id, AGENT, "run_blocked", {"run": run_id, "why": str(stop)})
        return dict(run_id=run_id, status="blocked", why=str(stop))
    counts["observed"] = observe(store, ledger, client_id)
    counts["auto_posted"] += reroute(store, ledger, client_id, post=True)
    ctx = Context(ledger, client["realm_id"])
    standing = store.active_standing(client_id)
    known = {p["item_key"] for p in store.proposals(client_id)}
    for item in ctx.feed:
        counts["read"] += 1
        if item["id"] in known:
            continue
        prop = brain.propose(item, ctx)
        queue, reasons, standing_id = route(client, company, item, prop, standing)
        proposal_id = store.run(
            "INSERT INTO proposals(client_id,run_id,item_key,item,action,item_class,class_key,confidence,evidence,brain,status,queue,reasons,standing_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (client_id, run_id, item["id"], dumps(item), dumps(prop["action"]) if prop["action"] else None,
             prop["item_class"], prop["class_key"], prop["confidence"], dumps(prop["evidence"]), brain.name,
             "waiting", None if queue == "auto" else queue, dumps(reasons), standing_id, now()))
        counts["new"] += 1
        if queue != "auto":
            counts[queue] += 1
            continue
        try:
            ok = execute(store, ledger, proposal_id, prop["action"], "standing", AGENT)
        except Blocked as stop:
            store.run("UPDATE proposals SET queue='exception', reasons=? WHERE id=?", (dumps([str(stop)]), proposal_id))
            ok = False
        counts["auto_posted" if ok else "failed"] += 1
    store.run("UPDATE runs SET finished=?, status='finished', summary=? WHERE id=?", (now(), dumps(counts), run_id))
    store.audit(client_id, AGENT, "run_finished", dict(counts, run=run_id))
    return dict(run_id=run_id, status="finished", **counts)
