"""The part that reads a bank line and says what it is.

A brain only proposes. It never decides whether something posts: policy.py
does that, from what a person has approved. BaselineBrain is deterministic and
uses only the company's own history, so the rest of the system can be built
and tested without a model. A model-backed brain plugs in behind the same
`propose` method and is held to the same policy.
"""
import re
from collections import Counter
from datetime import date

STOP = {"POS", "DEBIT", "PURCHASE", "ACH", "PAYMENT", "CARD", "CHECKCARD", "WEB", "ID", "PPD", "ONLINE",
        "SUBSCR", "DEPOSIT", "CO", "INC", "LLC"}
FEE_WORDS = ("SERVICE FEE", "MONTHLY FEE", "WIRE FEE", "OVERDRAFT FEE", "MAINTENANCE FEE")
PERSON_RAILS = ("ZELLE", "VENMO", "CASH APP", "ATM WITHDRAWAL")

# Classes a standing approval may ever cover. Everything else always goes to a person.
AUTO_ELIGIBLE = {"recurring_vendor", "bill_payment_match", "invoice_payment_match", "own_transfer", "bank_fee"}


def vendor_key(description):
    """A stable key for 'the same payee', ignoring reference numbers."""
    words = [w for w in re.sub(r"[^A-Z ]", " ", description.upper()).split() if len(w) > 1 and w not in STOP]
    return " ".join(words[:2])


def proposal(item_class, class_key, action, confidence, **evidence):
    return dict(item_class=item_class, class_key=class_key, action=action, confidence=confidence, evidence=evidence)


class Context:
    """What the books already say about one company. Built fresh for each run."""

    def __init__(self, ledger, realm_id):
        self.chart = ledger.accounts(realm_id)
        self.accounts = [a["name"] for a in self.chart]
        self.banks = ledger.bank_accounts(realm_id)
        self.bills = ledger.open_bills(realm_id)
        self.invoices = ledger.open_invoices(realm_id)
        self.feed = ledger.pending_feed(realm_id)
        self.history = ledger.history(realm_id)
        self.by_vendor = {}
        for t in self.history:
            if t.get("kind") == "categorize" and t.get("vendor"):
                self.by_vendor.setdefault(vendor_key(t["description"]), []).append(t)


class BaselineBrain:
    name = "baseline-1"

    def propose(self, line, ctx):
        text, cents = line["description"].upper(), line["amount_cents"]

        same = [t for t in ctx.history if t["date"] == line["date"] and t["amount_cents"] == cents
                and t["description"] == line["description"] and t["bank_account"] == line["bank_account"]]
        if same:
            return proposal("possible_duplicate", vendor_key(text), None, 0.5, already_posted=[t["id"] for t in same])

        if any(text.startswith(rail) for rail in PERSON_RAILS):
            return proposal("person_payment", "person", None, 0.0, why="payment to an individual needs a person to say what it was for")

        other = [l for l in ctx.feed if l["id"] != line["id"] and l["amount_cents"] == -cents
                 and l["bank_account"] != line["bank_account"] and l["bank_account"] in ctx.banks
                 and abs((date.fromisoformat(l["date"]) - date.fromisoformat(line["date"])).days) <= 3]
        if "TRANSFER" in text and len(other) == 1:
            pair = " <> ".join(sorted([line["bank_account"], other[0]["bank_account"]]))
            return proposal("own_transfer", pair, dict(kind="transfer", other_account=other[0]["bank_account"]),
                            0.97, other_side=other[0]["id"])

        if any(word in text for word in FEE_WORDS) and cents < 0 and "Bank Charges" in ctx.accounts:
            return proposal("bank_fee", "Bank Charges", dict(kind="categorize", account="Bank Charges", vendor=None,
                            memo="Bank fee per bank feed"), 0.95, matched_words=[w for w in FEE_WORDS if w in text])

        book, kind, party = (ctx.bills, "bill", "vendor") if cents < 0 else (ctx.invoices, "invoice", "customer")
        exact = [t for t in book if t["amount_cents"] == abs(cents)]
        named = [t for t in exact if vendor_key(t[party]) and vendor_key(t[party]) == vendor_key(text)]
        if len(named) == 1 and len(exact) == 1:
            return proposal(kind + "_payment_match", named[0][party],
                            dict(kind="match", txn_type=kind, txn_id=named[0]["id"]), 0.99,
                            open_item=named[0]["id"], same_amount=True, same_name=True)

        seen = ctx.by_vendor.get(vendor_key(text), [])
        if seen:
            vendor = seen[-1]["vendor"]
            accounts = Counter(t["account"] for t in seen)
            account, count = accounts.most_common(1)[0]
            action = dict(kind="categorize", account=account, vendor=vendor, memo="Categorized as in prior months")
            evidence = dict(times_seen=len(seen), accounts_used=dict(accounts), last_dates=[t["date"] for t in seen[-3:]])
            if len(accounts) == 1 and count >= 3:
                return proposal("recurring_vendor", "%s | %s" % (vendor, account), action, 0.95, **evidence)
            if len(accounts) == 1:
                return proposal("vendor_seen_few_times", "%s | %s" % (vendor, account), action, 0.7, **evidence)
            return proposal("vendor_mixed_accounts", vendor, action, 0.5, **evidence)

        return proposal("unknown", vendor_key(text) or "unknown", None, 0.0, why="nothing in the books matches this line")
