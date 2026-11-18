"""Decides what may post without a person, and why everything else may not.

Two layers, both required:
1. Hard stops that no approval can override (the firm's own rules).
2. A standing approval a person granted for this client, this class of item and
   this exact treatment, within its amount limit.
"""
import hashlib
from .brain import AUTO_ELIGIBLE
from .ledger import OPENING_BALANCE_EQUITY

MIN_CONFIDENCE = 0.9


def same_treatment(a, b):
    if not a or not b or a.get("kind") != b.get("kind"):
        return False
    keys = {"categorize": ("account", "vendor"), "match": ("txn_type", "txn_id"), "transfer": ("other_account",),
            "move": ("txn_type", "txn_id")}[a["kind"]]
    return all(a.get(k) == b.get(k) for k in keys)


def hard_stops(item, action, company):
    """Reasons this item may never post unattended, whatever has been approved."""
    stops = []
    if item["date"] <= company["closed_through"]:
        stops.append("dated in a closed period")
    if item["date"] < company["fiscal_year_start"]:
        stops.append("dated before the current fiscal year")
    if item["date"] > company["today"]:
        stops.append("dated in the future")
    if action and OPENING_BALANCE_EQUITY in (action.get("account"), action.get("other_account")):
        stops.append("would touch Opening Balance Equity")
    return stops


def spot_check(client, item_key):
    """A fixed share of approved-class items still goes to a person, so
    agreement keeps being measured after a class stops being reviewed."""
    digest = hashlib.sha256(("%s|%s" % (client["client_id"], item_key)).encode()).hexdigest()
    return int(digest[:8], 16) % 100 < client["spot_check_percent"]


def route(client, company, item, prop, standing):
    """Returns (queue, reasons, standing_id). queue is 'auto', 'spot_check',
    'prepared' or 'exception'."""
    reasons = hard_stops(item, prop["action"], company)
    if prop["action"] is None:
        reasons.append("no proposal: " + prop["item_class"].replace("_", " "))
    elif prop["item_class"] not in AUTO_ELIGIBLE:
        reasons.append("class always reviewed: " + prop["item_class"].replace("_", " "))
    if prop["confidence"] < MIN_CONFIDENCE and prop["action"] is not None:
        reasons.append("low confidence")
    if abs(item["amount_cents"]) > client["auto_limit_cents"]:
        reasons.append("over the client's unattended limit")
    if reasons:
        return "exception", reasons, None

    grant = next((s for s in standing if s["item_class"] == prop["item_class"] and s["class_key"] == prop["class_key"]), None)
    if client["mode"] == "prepare_only":
        return "prepared", ["client is in prepare-only mode"], grant["id"] if grant else None
    if grant is None:
        return "exception", ["no standing approval for this class"], None
    if abs(item["amount_cents"]) > grant["max_amount_cents"]:
        return "exception", ["over the standing approval's amount limit"], grant["id"]
    if client["mode"] != "post_standing":
        return "exception", ["client mode does not allow unattended posting"], grant["id"]
    if spot_check(client, item["id"]):
        return "spot_check", ["spot check of an approved class"], grant["id"]
    return "auto", [], grant["id"]
