"""Accounting modules: pure handlers behind the common execution contracts.

No handler can post, approve, access the filesystem or call a model/connector.
"""
from decimal import Decimal
from .core import (Capability, ControlError, Step, Workflow, day, money, normalize,
                   require_keys, text_field)


def validate_source(kind, value):
    if kind == "transaction":
        require_keys(value, {"source_id", "source_system", "account_id", "date", "description", "amount", "currency", "status", "activity"}, {"requires_split", "supersedes_source_id"})
        if value["source_system"] != "fixture":
            raise ControlError("Only fixture intake is implemented")
        for name in ("source_id", "account_id", "description", "currency"):
            text_field(value[name], name)
        if value["status"] not in ("pending", "posted") or value["activity"] not in ("purchase", "credit", "payment", "transfer", "unknown"):
            raise ControlError("Unsupported transaction status/activity")
        if "requires_split" in value and type(value["requires_split"]) is not bool:
            raise ControlError("requires_split must be boolean")
        if "supersedes_source_id" in value:
            text_field(value["supersedes_source_id"], "supersedes_source_id")
        day(value["date"])
        money(value["amount"])
    elif kind == "receipt":
        require_keys(value, {"transaction_source_id", "account_id", "date", "vendor", "amount", "currency", "content"})
        for name in ("transaction_source_id", "account_id", "vendor", "currency", "content"):
            text_field(value[name], name, 10000 if name == "content" else 200)
        day(value["date"])
        money(value["amount"])
    elif kind == "statement_control":
        require_keys(value, {"account_id", "currency", "period_start", "period_end", "posted_count", "posted_total", "content"})
        if type(value["posted_count"]) is not int or not 0 <= value["posted_count"] <= 10000:
            raise ControlError("Invalid statement count")
        day(value["period_start"])
        day(value["period_end"])
        money(value["posted_total"])
        for name in ("account_id", "currency", "content"):
            text_field(value[name], name)
    elif kind == "journal":
        require_keys(value, {"date", "currency", "memo", "lines", "supporting_keys"})
        day(value["date"])
        text_field(value["currency"], "currency")
        text_field(value["memo"], "memo", 2000)
        if not isinstance(value["lines"], list) or not 2 <= len(value["lines"]) <= 100:
            raise ControlError("Journal requires 2–100 lines")
        for line in value["lines"]:
            require_keys(line, {"account_id", "debit", "credit"})
            text_field(line["account_id"], "account_id")
            money(line["debit"])
            money(line["credit"])
        if not isinstance(value["supporting_keys"], list) or len(value["supporting_keys"]) > 100:
            raise ControlError("Invalid supporting keys")
        for key in value["supporting_keys"]:
            text_field(key, "supporting key")
    elif kind == "document":
        require_keys(value, {"document_type", "content"})
        text_field(value["document_type"], "document_type")
        text_field(value["content"], "content", 10000)
    else:
        raise ControlError("Source type is not implemented: " + str(kind))


def refs(rows):
    return [{"snapshot_id": r["id"], "hash": r["hash"], "source_key": r["source_key"], "version": r["version"]} for r in rows]


def output(key, kind, data, blockers=(), reviewable=False):
    return {"item_key": key, "kind": kind, "data": data, "blockers": sorted(set(blockers)),
            "eligible": reviewable and not blockers}


def source_inventory(ctx):
    return [output("inventory", "inventory", {
        "sources": refs(ctx["sources"]), "profile": ctx["profile_ref"],
        "source_count": len(ctx["sources"]), "execution": "deterministic",
        "notice": "Declared source inventory is not proof of a complete ledger or statement population."
    }, [] if ctx["sources"] else ["NO_SOURCE_EVIDENCE"])]


def period_issues(value, profile):
    result = []
    if not day(profile["period"]["start"]) <= day(value["date"]) <= day(profile["period"]["end"]):
        result.append("OUTSIDE_PERIOD")
    if profile["period"]["locked"]:
        result.append("PERIOD_LOCKED")
    if value["currency"] != profile["currency"]:
        result.append("CURRENCY_MISMATCH")
    return result


def card_prepare(ctx):
    profile = ctx["profile"]
    sources = ctx["sources"]
    txs = [s for s in sources if s["kind"] == "transaction"]
    receipts = [s for s in sources if s["kind"] == "receipt"]
    controls = [s for s in sources if s["kind"] == "statement_control"]
    account_issues = {}
    for account in profile["card_accounts"]:
        issue = []
        matching = [s for s in controls if s["value"]["account_id"] == account]
        if len(matching) != 1:
            issue.append("STATEMENT_CONTROL_MISSING_OR_AMBIGUOUS")
        else:
            c = matching[0]["value"]
            rows = [t["value"] for t in txs if t["value"]["account_id"] == account and
                    t["value"]["status"] == "posted" and t["value"]["currency"] == profile["currency"] and
                    profile["period"]["start"] <= t["value"]["date"] <= profile["period"]["end"]]
            if (c["currency"] != profile["currency"] or c["period_start"] != profile["period"]["start"] or
                    c["period_end"] != profile["period"]["end"] or c["posted_count"] != len(rows) or
                    money(c["posted_total"]) != sum((money(t["amount"]) for t in rows), Decimal("0.00"))):
                issue.append("STATEMENT_CONTROL_MISMATCH")
        account_issues[account] = issue
    result = []
    for row in txs:
        t = row["value"]
        blockers = period_issues(t, profile) + account_issues.get(t["account_id"], ["ACCOUNT_NOT_CONFIGURED"])
        if t["status"] == "pending":
            blockers.append("PENDING_TRANSACTION")
        if money(t["amount"]) < 0 or t["activity"] == "credit":
            blockers.append("CREDIT_REQUIRES_REVIEW")
        if money(t["amount"]) == 0:
            blockers.append("ZERO_AMOUNT")
        if t["activity"] != "purchase":
            blockers.append("NON_EXPENSE_REQUIRES_REVIEW")
        if t.get("requires_split"):
            blockers.append("SPLIT_REQUIRES_REVIEW")
        if t.get("supersedes_source_id"):
            blockers.append("SOURCE_TRANSITION_REQUIRES_REVIEW")
        candidates = [v for v in profile["vendors"] if normalize(t["description"]) in [normalize(a) for a in v["aliases"]]]
        vendor = candidates[0] if len(candidates) == 1 else None
        if not candidates:
            blockers.append("UNKNOWN_VENDOR")
        if len(candidates) > 1:
            blockers.append("AMBIGUOUS_VENDOR")
        category = vendor.get("category") if vendor else None
        account = next((a for a in profile["accounts"] if a["id"] == category and a["active"] and a["type"] == "expense"), None)
        if account is None:
            category = None
            blockers.append("UNKNOWN_CATEGORY")
        # A credit/payment/transfer/split is never proposed as an ordinary expense.
        if t["activity"] != "purchase" or money(t["amount"]) <= 0 or t.get("requires_split"):
            category = None
        def vendor_key(tx):
            aliases = [v["id"] for v in profile["vendors"] if normalize(tx["description"]) in [normalize(a) for a in v["aliases"]]]
            return aliases[0] if len(aliases) == 1 else normalize(tx["description"])
        duplicates = [other for other in txs if other["id"] != row["id"] and all(
            other["value"][f] == t[f] for f in ("account_id", "date", "amount", "currency")) and
            vendor_key(other["value"]) == vendor_key(t)]
        if duplicates:
            blockers.append("POSSIBLE_DUPLICATE")
        docs = [r for r in receipts if r["value"]["transaction_source_id"] == t["source_id"] and r["value"]["account_id"] == t["account_id"]]
        if profile["policies"]["receipt_required"] and not docs:
            blockers.append("MISSING_RECEIPT")
        if len(docs) > 1:
            blockers.append("MULTIPLE_RECEIPTS_REQUIRE_REVIEW")
        for doc in docs:
            d = doc["value"]
            for field, code in (("amount", "RECEIPT_AMOUNT_MISMATCH"), ("currency", "RECEIPT_CURRENCY_MISMATCH"), ("date", "RECEIPT_DATE_MISMATCH")):
                if d[field] != t[field]:
                    blockers.append(code)
            accepted = [normalize(a) for a in vendor["aliases"]] if vendor else [normalize(t["description"])]
            if normalize(d["vendor"]) not in accepted:
                blockers.append("RECEIPT_VENDOR_MISMATCH")
            # Reuse of identical declared receipt content for another source is suspicious.
            if any(r["id"] != doc["id"] and r["value"]["content"] == d["content"] and
                   (r["value"]["transaction_source_id"], r["value"]["account_id"]) != (t["source_id"], t["account_id"]) for r in receipts):
                blockers.append("RECEIPT_REUSED")
        result.append(output(row["source_key"], "card_proposal", {
            "transaction": t, "vendor": {"id": vendor["id"], "name": vendor["name"]} if vendor else None,
            "proposed_category": category, "duplicate_candidates": refs(duplicates),
            "evidence": refs([row] + docs + controls), "profile": ctx["profile_ref"],
            "rationale": "Exact fictional alias proposal; human must validate business purpose and treatment.",
            "execution": "deterministic", "external_posting": "not_performed"
        }, blockers, True))
    return result or [output("no-transactions", "card_proposal", {}, ["NO_TRANSACTIONS"])]


def journal_validate(ctx):
    profile = ctx["profile"]
    journals = [s for s in ctx["sources"] if s["kind"] == "journal"]
    documents = {s["source_key"]: s for s in ctx["sources"] if s["kind"] == "document"}
    result = []
    for row in journals:
        j = row["value"]
        blockers = period_issues(j, profile)
        debits = sum((money(line["debit"]) for line in j["lines"]), Decimal("0.00"))
        credits = sum((money(line["credit"]) for line in j["lines"]), Decimal("0.00"))
        if debits != credits:
            blockers.append("UNBALANCED_JOURNAL")
        if debits <= 0:
            blockers.append("EMPTY_OR_NEGATIVE_JOURNAL")
        for line in j["lines"]:
            debit, credit = money(line["debit"]), money(line["credit"])
            if debit < 0 or credit < 0 or (debit > 0) == (credit > 0):
                blockers.append("INVALID_JOURNAL_LINE")
            if not any(a["id"] == line["account_id"] and a["active"] for a in profile["accounts"]):
                blockers.append("ACCOUNT_NOT_CONFIGURED")
        if not j["supporting_keys"] or any(key not in documents for key in j["supporting_keys"]):
            blockers.append("MISSING_JOURNAL_SUPPORT")
        result.append(output(row["source_key"], "journal_proposal", {
            "journal": j, "debit_total": str(debits), "credit_total": str(credits),
            "evidence": refs([row] + [documents[k] for k in j["supporting_keys"] if k in documents]),
            "profile": ctx["profile_ref"], "execution": "deterministic",
            "rationale": "Mechanical validation does not establish correct recognition, tax or business treatment.",
            "external_posting": "not_performed"
        }, blockers, True))
    return result or [output("no-journals", "journal_proposal", {}, ["NO_JOURNALS"])]


def close_readiness(ctx):
    documents = [s for s in ctx["sources"] if s["kind"] == "document"]
    present = {s["value"]["document_type"] for s in documents}
    missing = sorted(set(ctx["profile"]["required_close_evidence"]) - present)
    return [output("close-checklist", "close_readiness", {
        "required_evidence": ctx["profile"]["required_close_evidence"], "missing_evidence": missing,
        "evidence": refs(documents), "execution": "deterministic",
        "status": "incomplete_readiness_only", "final_close": "not_signed_off",
        "external_posting": "not_verified", "external_reconciliation": "not_verified",
        "rationale": "Document presence alone cannot establish reconciliation or completed close."
    }, (["MISSING_CLOSE_EVIDENCE"] if missing else []) + ["FINAL_CLOSE_SIGNOFF_REQUIRED", "EXTERNAL_STEPS_UNVERIFIED"])]


def package_checks(ctx):
    return [output("package-checks", "package_checks", {
        "input_fingerprint": ctx["fingerprint"], "execution": "deterministic",
        "source_scope": ctx["scope"], "model_calls": 0,
        "external_posting": "not_performed", "final_close": "not_signed_off"
    })]


CAPABILITIES = {c.id: c for c in (
    Capability("evidence.inventory", "shared", "fixture-demonstrated", "deterministic", source_inventory),
    Capability("banking.card_prepare", "banking_reconciliation", "fixture-demonstrated", "deterministic", card_prepare),
    Capability("gl.journal_validate", "general_ledger", "fixture-demonstrated", "deterministic", journal_validate),
    Capability("close.readiness", "month_end_close", "fixture-demonstrated", "deterministic", close_readiness),
    Capability("package.check", "shared", "fixture-demonstrated", "deterministic", package_checks),
    Capability("gl.account_maintenance", "general_ledger", "deferred", "human"),
    Capability("gl.post", "general_ledger", "deferred", "human", effect="write"),
    Capability("ap.bills_expenses_payments", "accounts_payable", "deferred", "human", effect="write"),
    Capability("ar.invoices_collections_application_aging", "accounts_receivable", "deferred", "human"),
    Capability("banking.match_transfer_reconcile", "banking_reconciliation", "deferred", "human"),
    Capability("close.accruals_adjustments_signoff", "month_end_close", "deferred", "human"),
    Capability("reporting.statements_management_variances_insights", "financial_reporting", "deferred", "human"),
)}

WORKFLOWS = {w.id: w for w in (
    Workflow("card_preparation", "banking_reconciliation", (
        Step("inventory", "evidence.inventory"),
        Step("prepare", "banking.card_prepare", ("inventory",)),
        Step("package", "package.check", ("prepare",)))),
    Workflow("journal_preparation", "general_ledger", (
        Step("inventory", "evidence.inventory"),
        Step("validate", "gl.journal_validate", ("inventory",)),
        Step("package", "package.check", ("validate",)))),
    Workflow("close_readiness", "month_end_close", (
        Step("inventory", "evidence.inventory"),
        Step("checklist", "close.readiness", ("inventory",)),
        Step("package", "package.check", ("checklist",)))),
)}
for _workflow in WORKFLOWS.values():
    _workflow.validate()
