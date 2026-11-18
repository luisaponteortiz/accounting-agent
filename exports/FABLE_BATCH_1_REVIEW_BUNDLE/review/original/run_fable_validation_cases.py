"""Runs FABLE_VALIDATION_CASES.json against an Accounting Agent OS checkout.

Usage: python3 run_fable_validation_cases.py <project-root> <cases.json>

Synthetic only. Uses temporary SQLite files. No network, model or ledger access.
Statuses:
  PASS            executable_now case matches its expected outcome
  FIXED           executable_now_fails_until_fix case now meets the required outcome
  KNOWN-FAIL      still shows the documented current_behavior_observed
  UNEXPECTED      neither the required outcome nor the documented current behaviour
  DEFERRED-OK     future module is still refused (required behaviour today)
  DEFERRED-LEAK   a deferred capability could be enqueued
Exit code 1 if any PASS-stage case fails, or any UNEXPECTED / DEFERRED-LEAK occurs.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT, CASES_PATH = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from accounting_agent.core import Actor, ControlError  # noqa: E402
from accounting_agent.service import AccountingOS  # noqa: E402

SPEC = json.loads(Path(CASES_PATH).read_text())
ORG = SPEC["validation_scope"]["organization_id"]
CLIENT = SPEC["validation_scope"]["client_id"]
SCOPE = SPEC["validation_scope"]["scope"]
REALM = SPEC["base_profile"]["external_company_id"]


def who(role="preparer", ident=None):
    return Actor(ident or ("worker-validation" if role == "worker" else "human-validation-" + role), role, ORG, CLIENT)


def profile_for(patch):
    p = copy.deepcopy(SPEC["base_profile"])
    for key, value in (patch or {}).items():
        if key == "version":
            p["version"] = value
        elif key == "vendors_append":
            p["vendors"].extend(value)
        elif key == "period_locked":
            p["period"]["locked"] = value
        else:
            raise ValueError("unknown profile patch " + key)
    return p


def packet(batch, sources):
    return {"synthetic": True, "organization_id": ORG, "client_id": CLIENT, "external_company_id": REALM, "batch_id": batch, "sources": sources}


class Box:
    def __init__(self, patch=None, actor=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.os = AccountingOS(Path(self.tmp.name) / "v.sqlite3", [SCOPE])
        self.os.onboard(actor or who(), profile_for(patch))

    def run(self, workflow, actor=None):
        rid = self.os.enqueue(actor or who(), workflow)
        self.os.drain(who("worker"))
        return rid

    def artifacts(self, rid=None, key=None):
        rows = self.os.state(who())["artifacts"]
        return [a for a in rows if (rid is None or a["run_id"] == rid) and (key is None or a["item_key"] == key)]

    def decide(self, a, decision="approve", actor=None):
        self.os.review(actor or who("reviewer"), a["id"], a["hash"], a["fingerprint"], decision, "validation case decision")


def check_item(a, blockers, eligible, case=None):
    problems = []
    if sorted(a["blockers"]) != sorted(blockers):
        problems.append("blockers %s != expected %s" % (sorted(a["blockers"]), sorted(blockers)))
    if bool(a["eligible"]) != eligible:
        problems.append("eligible %s != expected %s" % (bool(a["eligible"]), eligible))
    if case is not None and "expected_proposed_category" in case:
        got = a["payload"]["data"].get("proposed_category")
        if got != case["expected_proposed_category"]:
            problems.append("category %r != expected %r" % (got, case["expected_proposed_category"]))
    return problems


def run_prepare(case):
    inp = case["input"]
    try:
        box = Box(inp["profile_patch"])
    except ControlError as exc:
        if case.get("also_acceptable"):
            return [], "profile refused: %s" % exc
        return ["profile refused: %s" % exc], None
    box.os.intake(who(), packet(case["id"], inp["sources"]))
    if inp["workflow"] == "close_readiness":
        for upstream in ("card_preparation", "journal_preparation"):
            box.run(upstream)
    rid = box.run(inp["workflow"])
    target = box.artifacts(rid, inp["target_item_key"])
    if len(target) != 1:
        return ["target artifact count %d" % len(target)], None
    eligible = case["approval_eligibility"] == "eligible_for_independent_review"
    problems = check_item(target[0], case["expected_blockers"], eligible, case)
    for key, exp in (case.get("other_item_expectations") or {}).items():
        other = box.artifacts(rid, key)
        problems += ["%s: %s" % (key, p) for p in (check_item(other[0], exp["expected_blockers"], exp["eligible"]) if len(other) == 1 else ["missing"])]
    if any(a["decisions"] for a in box.artifacts()):
        problems.append("a decision was recorded without a reviewer")
    try:
        box.decide(target[0])
        approved = True
    except ControlError:
        approved = False
    if approved != eligible:
        problems.append("approval attempt %s but eligibility expected %s" % ("accepted" if approved else "refused", eligible))
    observed = {"blockers": sorted(target[0]["blockers"]), "eligible": bool(target[0]["eligible"])}
    return problems, observed


def run_intake_rejected(case):
    box = Box(case["input"]["profile_patch"])
    before = box.os.state(who())["generation"]
    try:
        box.os.intake(who(), packet(case["id"], case["input"]["sources"]))
        return ["intake accepted"], None
    except ControlError:
        pass
    after = box.os.state(who())
    problems = []
    if after["generation"] != before or after["sources"]:
        problems.append("rejected intake left state behind")
    return problems, {"intake": "rejected"}


JOURNAL = {"kind": "journal", "key": "VJ-01", "data": {"date": "2027-02-10", "currency": "USD", "memo": "Fictional validation journal", "lines": [
    {"account_id": "VAL_SUPPLIES", "debit": "20.00", "credit": "0.00"}, {"account_id": "VAL_ACCRUED_LIABILITIES", "debit": "0.00", "credit": "20.00"}], "supporting_keys": ["je-support-1"]}}
SUPPORT = {"kind": "document", "key": "je-support-1", "data": {"document_type": "journal_support", "content": "Fictional support."}}
START, END = "2027-02-10T00:00:00+00:00", "2027-02-20T00:00:00+00:00"


def s_supplier_self_approval(case):
    a_prep, b_prep, a_rev = who("preparer", "human-a"), who("preparer", "human-b"), who("reviewer", "human-a")
    box = Box(actor=a_prep)
    box.os.intake(a_prep, packet("r01", [SUPPORT, JOURNAL]))
    rid = box.run("journal_preparation", b_prep)
    try:
        box.decide(box.artifacts(rid, "VJ-01")[0], actor=a_rev)
        return ["approval accepted from the evidence and policy author"], {"result": "approval accepted"}
    except ControlError as exc:
        return ([] if exc.status == 403 else ["refused with status %s, expected 403" % exc.status]), {"result": "refused"}


def s_stale_hash_after_revision(case):
    box = Box()
    box.os.intake(who(), packet("r02a", [SUPPORT, JOURNAL]))
    old = box.artifacts(box.run("journal_preparation"), "VJ-01")[0]
    revised = copy.deepcopy(JOURNAL)
    revised["data"]["memo"] = "Fictional validation journal (memo revised)"
    box.os.intake(who(), packet("r02b", [revised]))
    problems = []
    try:
        box.decide(old)
        problems.append("stale approval accepted")
    except ControlError as exc:
        if exc.status != 409:
            problems.append("stale approval refused with %s, expected 409" % exc.status)
    new = box.artifacts(box.run("journal_preparation"), "VJ-01")[0]
    if new["hash"] == old["hash"]:
        problems.append("revised content kept the same artifact hash")
    box.decide(new)
    if box.artifacts(old["run_id"], "VJ-01")[0]["decisions"]:
        problems.append("decision attached to superseded artifact")
    return problems, {"result": "stale refused; new version approved"}


def s_conflicting_decisions_across_runs(case):
    box = Box()
    box.os.intake(who(), packet("r03", [SUPPORT, JOURNAL]))
    box.run("journal_preparation")
    box.os.create_mandate(who(), ["journal_preparation"], START, END, 86400, 3)
    r1 = box.os.tick(who(), "2027-02-10T12:00:00+00:00"); box.os.drain(who("worker"), now="2027-02-10T12:00:01+00:00")
    r2 = box.os.tick(who(), "2027-02-11T12:00:00+00:00"); box.os.drain(who("worker"), now="2027-02-11T12:00:01+00:00")
    problems = []
    for rid, decision in ((r1[0], "approve"), (r2[0], "reject")):
        rows = box.artifacts(rid, "VJ-01")
        if rows:
            try:
                box.decide(rows[0], decision)
            except ControlError:
                pass
    current = [a for a in box.artifacts(key="VJ-01") if a["current"]]
    statuses = sorted(a["review_status"] for a in current)
    if len(current) != 1:
        problems.append("%d current artifacts govern VJ-01 with statuses %s" % (len(current), statuses))
    return problems, {"current_artifacts_for_item": len(current), "review_statuses": statuses}


def s_lock_preserves_approval(case):
    box = Box()
    box.os.intake(who(), packet("r04", [SUPPORT, JOURNAL]))
    a = box.artifacts(box.run("journal_preparation"), "VJ-01")[0]
    box.decide(a)
    box.os.onboard(who(), profile_for({"version": "fable-validation-locked", "period_locked": True}))
    status = next(x for x in box.artifacts() if x["id"] == a["id"])["review_status"]
    return ([] if status == "approve" else ["approved artifact reported as %r after lock" % status]), {"review_status_after_lock": status}


def s_occurrence_held_then_redispatched(case):
    box = Box()
    box.os.intake(who(), packet("rc01a", [SUPPORT, JOURNAL]))
    box.os.create_mandate(who(), ["journal_preparation"], START, END, 86400, 3)
    first = box.os.tick(who(), "2027-02-10T12:00:00+00:00")
    box.os.intake(who(), packet("rc01b", [{"kind": "document", "key": "late-doc", "data": {"document_type": "journal_support", "content": "Late fictional evidence."}}]))
    box.os.drain(who("worker"), now="2027-02-10T12:05:00+00:00")
    box.os.tick(who(), "2027-02-10T13:00:00+00:00")
    box.os.drain(who("worker"), now="2027-02-10T13:05:00+00:00")
    state = box.os.state(who())
    produced = [a for a in state["artifacts"] if a["current"] and a["item_key"] == "VJ-01"]
    status = next(r for r in state["runs"] if r["id"] == first[0])["status"]
    return ([] if produced else ["occurrence produced no current preparation; first run status %s" % status]), {"occurrence_run_status": status, "artifacts": len(produced), "redispatch": bool(produced)}


def s_poison_mandate_isolated(case):
    box = Box()
    box.os.intake(who(), packet("rc02", [SUPPORT, JOURNAL]))
    box.os.create_mandate(who(), ["journal_preparation"], START, END, 86400, 3)
    box.os.create_mandate(who(), ["card_preparation"], START, END, 86400, 3)
    p = profile_for({"version": "fable-validation-no-journal"})
    p["procedures"] = ["card_preparation", "close_readiness"]
    box.os.onboard(who(), p)
    try:
        box.os.tick(who(), "2027-02-10T12:00:00+00:00")
    except ControlError as exc:
        return ["tick raised: %s" % exc], {"tick": "raises %s; zero runs created for any mandate" % exc.status}
    runs = [r for r in box.os.state(who())["runs"] if r["mandate_id"] and r["workflow"] == "card_preparation"]
    return ([] if runs else ["valid mandate was not dispatched"]), {"tick": "ok"}


def s_duplicate_delivery_and_clock_regression(case):
    box = Box()
    box.os.intake(who(), packet("rc03", [SUPPORT, JOURNAL]))
    box.os.create_mandate(who(), ["journal_preparation"], START, END, 86400, 3)
    a = box.os.tick(who(), "2027-02-10T12:00:00+00:00")
    b = box.os.tick(who(), "2027-02-10T18:00:00+00:00")
    problems = [] if a == b and len(a) == 1 else ["duplicate delivery produced %s then %s" % (a, b)]
    try:
        box.os.tick(who(), "2027-02-09T12:00:00+00:00")
        problems.append("clock moved backwards")
    except ControlError as exc:
        if exc.status != 409:
            problems.append("clock regression refused with %s" % exc.status)
    if sum(1 for r in box.os.state(who())["runs"] if r["mandate_id"]) != 1:
        problems.append("more than one mandate run exists")
    return problems, {"result": "one run"}


SCENARIOS = {n[2:]: f for n, f in list(globals().items()) if n.startswith("s_")}


def run_future(case):
    box = Box()
    cap = case["target_workflow_or_capability"].split(" ")[0]
    try:
        box.os.enqueue(who(), cap)
        return "DEFERRED-LEAK", "capability %s could be enqueued" % cap
    except ControlError as exc:
        return "DEFERRED-OK", "refused (%s)" % exc.status


def main():
    tally, bad = {}, False
    for case in SPEC["cases"]:
        stage, mode = case["test_stage"], case["input"]["mode"]
        if stage == "future_module_specification":
            status, detail = run_future(case)
        else:
            try:
                if mode == "prepare":
                    problems, observed = run_prepare(case)
                elif mode == "intake_rejected":
                    problems, observed = run_intake_rejected(case)
                else:
                    problems, observed = SCENARIOS[case["input"]["scenario"]](case)
            except Exception as exc:  # report, never hide
                problems, observed = ["runner error %s: %s" % (type(exc).__name__, exc)], None
            if stage == "executable_now":
                status, detail = ("PASS", "") if not problems else ("FAIL", "; ".join(problems))
            elif not problems:
                status, detail = "FIXED", "meets required outcome"
            else:
                doc = case.get("current_behavior_observed", {})
                same = observed is not None and all(observed.get(k) == v for k, v in doc.items() if k in observed)
                status, detail = ("KNOWN-FAIL" if same else "UNEXPECTED"), "; ".join(problems)
        tally[status] = tally.get(status, 0) + 1
        bad = bad or status in ("FAIL", "UNEXPECTED", "DEFERRED-LEAK")
        print("%-13s %-8s %s" % (status, case["id"], detail))
    print("\nSummary:", ", ".join("%s=%d" % kv for kv in sorted(tally.items())))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
