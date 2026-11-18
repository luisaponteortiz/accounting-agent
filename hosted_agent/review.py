"""What people do: decide waiting items, grant and end standing approvals,
change a client's mode. The agent itself can do none of these."""
import json
from .brain import AUTO_ELIGIBLE
from .policy import hard_stops
from .runner import AGENT, Blocked, execute, preflight, reroute, suspend_on_disagreement
from .store import MODES, dumps, now

ROLES = {"owner": {"decide", "standing", "mode"}, "reviewer": {"decide"}}
MIN_STREAK = 5  # consecutive agreements, with no disagreement since, before a class can be proposed


class Refused(Exception):
    pass


def allow(person, right):
    if not person or person.get("name") in (AGENT, "system", None) or right not in ROLES.get(person.get("role"), ()):
        raise Refused("%s may not %s" % ((person or {}).get("name", "nobody"), right))


def decide(store, ledger, person, proposal_id, verdict, final_action=None, note=""):
    allow(person, "decide")
    p = store.proposal(proposal_id)
    if p["status"] != "waiting":
        raise Refused("proposal %s is already %s" % (proposal_id, p["status"]))
    if verdict not in ("approve", "change", "reject"):
        raise Refused("unknown verdict " + str(verdict))
    action = p["action"] if verdict == "approve" else final_action if verdict == "change" else None
    if verdict != "reject" and not action:
        raise Refused("nothing to post: give a treatment" if verdict == "change" else "this item has no proposal to approve")
    if verdict == "reject" and not note.strip():
        raise Refused("a rejection needs a reason")
    posts = verdict != "reject" and store.client(p["client_id"])["mode"] != "prepare_only"
    if posts:
        try:
            _, company = preflight(store, ledger, p["client_id"])
        except Blocked as stop:
            raise Refused(str(stop))
        stops = hard_stops(p["item"], action, company)
        if stops:
            raise Refused("cannot be posted from here (%s); handle it in the books or reject it with a note" % "; ".join(stops))
    store.run("INSERT INTO decisions(client_id,proposal_id,actor,verdict,final_action,note,created) VALUES(?,?,?,?,?,?,?)",
              (p["client_id"], proposal_id, person["name"], verdict, dumps(action) if action else None, note, now()))
    store.audit(p["client_id"], person["name"], "decided", {"proposal": proposal_id, "verdict": verdict})
    if verdict != "approve":
        suspend_on_disagreement(store, p, person["name"])
    if verdict == "reject":
        store.run("UPDATE proposals SET status='rejected', queue=NULL, closed=? WHERE id=?", (now(), proposal_id))
        return "rejected"
    if store.client(p["client_id"])["mode"] == "prepare_only":
        store.run("UPDATE proposals SET status='approved_not_posted', queue=NULL, closed=? WHERE id=?", (now(), proposal_id))
        return "approved_not_posted"
    try:
        ok = execute(store, ledger, proposal_id, action, "approved" if verdict == "approve" else "changed", person["name"])
    except Blocked as stop:
        raise Refused(str(stop))
    return "sent" if ok is None else "posted" if ok else "failed"


def record(store, client_id):
    """Per class of item: how often people agreed with the agent, and the current streak."""
    classes = {}
    for d in store.rows("""SELECT p.item_class, p.class_key, p.item, d.verdict FROM decisions d
                           JOIN proposals p ON p.id=d.proposal_id WHERE d.client_id=? ORDER BY d.id""", (client_id,)):
        c = classes.setdefault((d["item_class"], d["class_key"]), dict(item_class=d["item_class"], class_key=d["class_key"],
                               decided=0, agreed=0, streak=0, max_seen_cents=0))
        c["decided"] += 1
        if d["verdict"] == "approve":
            c["agreed"] += 1
            c["streak"] += 1
            c["max_seen_cents"] = max(c["max_seen_cents"], abs(json.loads(d["item"])["amount_cents"]))
        else:
            c["streak"] = 0
    granted = {(s["item_class"], s["class_key"]) for s in store.active_standing(client_id)}
    for key, c in classes.items():
        c["has_standing"] = key in granted
        c["eligible"] = c["item_class"] in AUTO_ELIGIBLE and c["streak"] >= MIN_STREAK and not c["has_standing"]
    return sorted(classes.values(), key=lambda c: (-c["eligible"], c["item_class"], c["class_key"]))


def grant_standing(store, person, client_id, item_class, class_key, max_amount_cents, override_reason=""):
    """A person extends their approval to a class of item for one client."""
    allow(person, "standing")
    if item_class not in AUTO_ELIGIBLE:
        raise Refused("%s is always reviewed by a person" % item_class.replace("_", " "))
    if max_amount_cents <= 0:
        raise Refused("a standing approval needs an amount limit")
    if any(s["item_class"] == item_class and s["class_key"] == class_key for s in store.active_standing(client_id)):
        raise Refused("this class already has a standing approval")
    found = next((c for c in record(store, client_id) if (c["item_class"], c["class_key"]) == (item_class, class_key)), None)
    earned = bool(found and found["streak"] >= MIN_STREAK)
    if not earned and not override_reason.strip():
        raise Refused("the record does not yet support this (%s agreements in a row, %s needed); give a reason to grant it anyway"
                      % (found["streak"] if found else 0, MIN_STREAK))
    basis = dict(record=found, override_reason=override_reason.strip() or None)
    standing_id = store.run("INSERT INTO standing_approvals(client_id,item_class,class_key,max_amount_cents,basis,granted_by,granted_at) VALUES(?,?,?,?,?,?,?)",
                            (client_id, item_class, class_key, max_amount_cents, dumps(basis), person["name"], now()))
    store.audit(client_id, person["name"], "standing_approval_granted", {"standing": standing_id, "item_class": item_class,
                "class_key": class_key, "max_amount_cents": max_amount_cents, "earned": earned})
    return standing_id


def end_standing(store, person, standing_id, reason):
    allow(person, "standing")
    s = store.one("SELECT * FROM standing_approvals WHERE id=? AND ended_at IS NULL", (standing_id,))
    if not s:
        raise Refused("no active standing approval %s" % standing_id)
    store.run("UPDATE standing_approvals SET ended_by=?, ended_at=?, ended_reason=? WHERE id=?", (person["name"], now(), reason, standing_id))
    store.audit(s["client_id"], person["name"], "standing_approval_ended", {"standing": standing_id, "reason": reason})


def set_mode(store, person, client_id, mode, ledger=None):
    allow(person, "mode")
    if mode not in MODES:
        raise Refused("unknown mode " + str(mode))
    store.client(client_id)
    store.run("UPDATE clients SET mode=? WHERE client_id=?", (mode, client_id))
    store.audit(client_id, person["name"], "mode_changed", {"mode": mode})
    if ledger is not None:
        try:
            reroute(store, ledger, client_id, post=False)
        except Blocked:
            pass


def state(store, client_id):
    """Everything the review page shows for ONE client. Never mixes clients."""
    client = store.client(client_id)
    return dict(
        client=client, waiting=store.proposals(client_id, "waiting"), sent=store.proposals(client_id, "sent"), record=record(store, client_id),
        standing=store.active_standing(client_id),
        runs=store.rows("SELECT id,job,started,finished,status,summary FROM runs WHERE client_id=? ORDER BY id DESC LIMIT 10", (client_id,)),
        posted=store.rows("""SELECT po.id, po.how, po.actor, po.created, po.ledger_ref, po.verified, p.item, po.action
                             FROM postings po JOIN proposals p ON p.id=po.proposal_id WHERE po.client_id=? ORDER BY po.id DESC LIMIT 50""", (client_id,)),
        audit_ok=store.verify_audit())


def roster(store):
    """The cross-client view: names and counts only."""
    out = []
    for c in store.clients():
        waiting = store.rows("SELECT queue, COUNT(*) n FROM proposals WHERE client_id=? AND status='waiting' GROUP BY queue", (c["client_id"],))
        last = store.one("SELECT started,status,summary FROM runs WHERE client_id=? ORDER BY id DESC LIMIT 1", (c["client_id"],))
        out.append(dict(client_id=c["client_id"], name=c["name"], mode=c["mode"], feed=c["feed"], waiting={w["queue"]: w["n"] for w in waiting}, last_run=last))
    return out
