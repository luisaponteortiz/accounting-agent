"""Connection to a QuickBooks Online SANDBOX company.

Endpoints are Intuit's published ones (discovery document
developer.api.intuit.com/.well-known/openid_sandbox_configuration). The API
host is the sandbox host and nothing else: this module has no way to reach a
real company's books. Tokens stay in this process and are never logged, sent
to the page, or written to the audit trail.

It reads, and it makes one kind of change: moving a payment that is already
recorded from its bank account to the clearing account (D-042), so that it
cancels the bank's own line there. It changes an existing record and reads it
back. It never deletes.
"""
import base64
import json
import re
from datetime import date
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

AUTHORIZE = "https://appcenter.intuit.com/connect/oauth2"
TOKEN = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API = "https://sandbox-quickbooks.api.intuit.com"   # sandbox only, on purpose
SCOPE = "com.intuit.quickbooks.accounting"
MINOR_VERSION = "75"
STATE_SECONDS = 600
RECORDED = ("Purchase", "Deposit", "Transfer", "JournalEntry", "BillPayment", "Payment", "SalesReceipt")
FEED_NAMES = ("BankTransaction", "BankFeed", "BankFeedTransaction", "OlbTransaction", "PendingTransaction", "DownloadedTransaction")
FEED_PATHS = ("banking/transactions", "bankfeeds", "olb/transactions")
CLEARING = "Bank Feed Clearing"
CARD_CLEARING = "Card Feed Clearing"      # D-045: a credit card account, because QuickBooks will not turn a card charge into a bank payment
MATCH_DAYS = 21
PAIR_DAYS = 3                 # the two bank lines of one transfer between the company's own accounts are at most this far apart
PAIR_NOTE = "Own-account transfer, other side: %s %s"
_PAIR = re.compile(r"\s*\|?\s*Own-account transfer, other side: (Purchase|Deposit|Transfer) (\w+)")


def pair_of(note):
    """The record a memo names as the other side of an own-account transfer, or None."""
    found = _PAIR.search(note or "")
    return (found.group(1), found.group(2)) if found else None


def without_pair(note):
    return _PAIR.sub("", note or "").strip() or None
_deposit_to = lambda t: t.get("DepositToAccountRef")
def _bill_payment_place(t):
    if "CheckPayment" in t:
        return t["CheckPayment"].setdefault("BankAccountRef", {})
    return (t.get("CreditCardPayment") or {}).get("CCAccountRef")


# Where each kind of record names the account the money moved through. Returns the dict itself, so it can be changed in place.
RECORDED_PLACES = (("Purchase", lambda t: t.setdefault("AccountRef", {})), ("BillPayment", _bill_payment_place),
                   ("RefundReceipt", lambda t: t.setdefault("DepositToAccountRef", {})), ("Payment", lambda t: t.setdefault("DepositToAccountRef", {})),
                   ("Deposit", lambda t: t.setdefault("DepositToAccountRef", {})), ("SalesReceipt", lambda t: t.setdefault("DepositToAccountRef", {})))
RECORDED_PAYMENTS = (   # (kind of record, direction as the bank account saw it, where its bank account is named)
    ("Purchase", "out", lambda t: t.get("AccountRef")),
    ("BillPayment", "out", lambda t: (t.get("CheckPayment") or {}).get("BankAccountRef") or (t.get("CreditCardPayment") or {}).get("CCAccountRef")),
    ("RefundReceipt", "out", _deposit_to),
    ("Payment", "in", _deposit_to), ("Deposit", "in", _deposit_to), ("SalesReceipt", "in", _deposit_to))


class QboError(Exception):
    pass


def http(method, url, headers, body=None):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def fault_text(raw):
    """QuickBooks' own words for a refusal, shortened. Never includes a token."""
    try:
        data = json.loads(raw)
    except ValueError:
        return " ".join(raw.decode("utf-8", "replace").split())[:200] if isinstance(raw, bytes) else ""
    fault = {k.lower(): v for k, v in data.items()}.get("fault") or {}
    first = ({k.lower(): v for k, v in fault.items()}.get("error") or [{}])[0]
    first = {k.lower(): v for k, v in first.items()}
    return str(first.get("detail") or first.get("message") or "")[:200]


class Qbo:
    def __init__(self, client_id, client_secret, redirect_uri, transport=http, clock=time.time):
        self.client_id, self.client_secret, self.redirect_uri = client_id, client_secret, redirect_uri
        self.transport, self.clock = transport, clock
        self.states = {}       # state -> (person name, expiry)
        self.connection = None  # one sandbox company at a time in this build

    # -- sign-in with Intuit ------------------------------------------------
    def authorize_url(self, person_name):
        state = secrets.token_urlsafe(24)
        self.states[state] = (person_name, self.clock() + STATE_SECONDS)
        query = urllib.parse.urlencode(dict(client_id=self.client_id, response_type="code", scope=SCOPE,
                                            redirect_uri=self.redirect_uri, state=state))
        return AUTHORIZE + "?" + query

    def finish(self, state, code, realm_id):
        """The browser came back from Intuit. The state proves it is the sign-in this service started."""
        person, expiry = self.states.pop(state, (None, 0))
        if not person or self.clock() > expiry:
            raise QboError("this sign-in link is unknown, already used or expired; start again from the page")
        if not code or not realm_id:
            raise QboError("Intuit did not return a company; the connection was not approved")
        tokens = self._token(dict(grant_type="authorization_code", code=code, redirect_uri=self.redirect_uri))
        self.connection = dict(realm_id=str(realm_id), connected_by=person, connected_at=int(self.clock()), **tokens)
        return person

    def _token(self, form):
        basic = base64.b64encode(("%s:%s" % (self.client_id, self.client_secret)).encode()).decode()
        status, raw = self.transport("POST", TOKEN, {"Authorization": "Basic " + basic, "Accept": "application/json",
                                     "Content-Type": "application/x-www-form-urlencoded"}, urllib.parse.urlencode(form).encode())
        if status != 200:
            raise QboError("Intuit refused the sign-in (HTTP %s)" % status)
        data = json.loads(raw)
        return dict(access_token=data["access_token"], refresh_token=data["refresh_token"],
                    expires_at=self.clock() + int(data.get("expires_in", 3600)) - 60)

    # -- reads ------------------------------------------------------------
    def _request(self, path, params=None):
        c = self.connection
        if not c:
            raise QboError("no QuickBooks sandbox company is connected")
        if self.clock() >= c["expires_at"]:
            c.update(self._token(dict(grant_type="refresh_token", refresh_token=c["refresh_token"])))
        query = urllib.parse.urlencode(dict(params or {}, minorversion=MINOR_VERSION))
        url = "%s/v3/company/%s/%s?%s" % (API, c["realm_id"], path, query)
        return self.transport("GET", url, {"Authorization": "Bearer " + c["access_token"], "Accept": "application/json"})

    def _get(self, path, params=None):
        status, raw = self._request(path, params)
        if status != 200:
            raise QboError("QuickBooks answered HTTP %s for %s" % (status, path.split("/")[0]))
        return json.loads(raw)

    def _post(self, path, payload):
        c = self.connection
        if not c:
            raise QboError("no QuickBooks sandbox company is connected")
        if self.clock() >= c["expires_at"]:
            c.update(self._token(dict(grant_type="refresh_token", refresh_token=c["refresh_token"])))
        url = "%s/v3/company/%s/%s?minorversion=%s" % (API, c["realm_id"], path, MINOR_VERSION)
        status, raw = self.transport("POST", url, {"Authorization": "Bearer " + c["access_token"], "Accept": "application/json",
                                                   "Content-Type": "application/json"}, json.dumps(payload).encode())
        if status != 200:
            raise QboError("QuickBooks refused the change (HTTP %s): %s" % (status, fault_text(raw)))
        return json.loads(raw)

    def query(self, statement):
        return self._get("query", {"query": statement}).get("QueryResponse", {})

    def summary(self):
        """What the sandbox company holds, as proof the connection reads the books. No tokens."""
        c = self.connection
        if not c:
            return dict(connected=False)
        info = self._get("companyinfo/" + c["realm_id"])["CompanyInfo"]
        count = lambda entity: self.query("select count(*) from " + entity).get("totalCount", 0)
        purchases = self.query("select * from Purchase orderby TxnDate desc maxresults 5").get("Purchase", [])
        recent = [dict(date=p.get("TxnDate"), amount=p.get("TotalAmt"), payee=(p.get("EntityRef") or {}).get("name"),
                       paid_from=(p.get("AccountRef") or {}).get("name"),
                       category=next((l.get("AccountBasedExpenseLineDetail", {}).get("AccountRef", {}).get("name")
                                      for l in p.get("Line", []) if l.get("AccountBasedExpenseLineDetail")), None))
                  for p in purchases]
        return dict(connected=True, environment="sandbox", company=info.get("CompanyName"), realm_id=c["realm_id"],
                    connected_by=c["connected_by"], accounts=count("Account"), vendors=count("Vendor"),
                    customers=count("Customer"), purchases=count("Purchase"), bills=count("Bill"),
                    invoices=count("Invoice"), recent_purchases=recent)


    def clearing(self, name=CLEARING):
        """What sits in the clearing account. Reads only.

        Bank rules post each bank line against the clearing account: money out as an expense
        (or a transfer), money in as a deposit, with the clearing account as the category.
        For each line this lists payments of the same amount already recorded in the same
        bank account ("recorded": probably the same money a second time; "best_fit" marks the
        one this line would take when each payment goes to one line only) and the payment
        already recorded in the clearing account that cancels it ("cleared_by").
        The agent proposes; a person decides.
        """
        found = self.query("select * from Account where Name = '%s'" % name.replace("'", "\\'")).get("Account", [])
        if not found:
            return dict(found=False, name=name)
        account = found[0]
        every = self.query("select * from Account maxresults 1000").get("Account", [])
        kinds = {a["Id"]: a.get("AccountType") for a in every}
        card = next((a for a in every if a.get("Name") == CARD_CLEARING and a.get("AccountType") == "Credit Card"), None)
        clearing_ids = {account["Id"]} | ({card["Id"]} if card else set())      # rules post bank lines to one and card lines to the other
        cents = lambda amount: int(round(float(amount or 0) * 100))
        day = lambda text: date.fromisoformat(text[:10])
        raw = {entity: self.query("select * from %s maxresults 1000" % entity).get(entity, []) for entity, _, _ in RECORDED_PAYMENTS}
        lines, own = [], set()

        def add(line_id, when, amount, direction, bank, record, held_in, memo, **more):
            kind = kinds.get(bank.get("value"))
            lines.append(dict(id=line_id, date=when, amount_cents=cents(amount), direction=direction, bank_account=bank.get("name"),
                              bank_account_id=bank.get("value"), bank_account_type=kind,
                              movable=kind == "Bank" or (kind == "Credit Card" and bool(card)),
                              record_type=record[0], record_id=str(record[1]), clearing_id=held_in, pair=pair_of(memo), **more))

        def posted_by_rule(entity, t, detail, party):
            """The parts of one record that a rule booked against the clearing account, as one line."""
            parts = [l for l in t.get("Line", []) if ((l.get(detail) or {}).get("AccountRef") or {}).get("value") in clearing_ids]
            if not parts:
                return None
            own.add((entity, t.get("Id")))
            return dict(amount=sum(float(l.get("Amount") or 0) for l in parts), payee=(party(t, parts[0]) or {}).get("name"),
                        held_in=parts[0][detail]["AccountRef"]["value"],
                        note=next((l.get("Description") for l in parts if l.get("Description")), None) or without_pair(t.get("PrivateNote")))

        between = []                                    # transfers a person recorded between two of the company's own accounts
        for t in self.query("select * from Transfer maxresults 1000").get("Transfer", []):
            source, target = t.get("FromAccountRef") or {}, t.get("ToAccountRef") or {}
            held = clearing_ids & {source.get("value"), target.get("value")}
            if not held:
                between.append(dict(id=t.get("Id"), date=t.get("TxnDate"), amount_cents=cents(t.get("Amount")), source=source, target=target))
            if len(held) != 1:
                continue
            direction = "out" if target.get("value") in clearing_ids else "in"     # as the bank account saw it
            add(t["Id"], t.get("TxnDate"), t.get("Amount"), direction, source if direction == "out" else target, ("Transfer", t["Id"]), min(held), t.get("PrivateNote"),
                note=without_pair(t.get("PrivateNote")), payee=None, posted_as="transfer")
        for t in raw["Purchase"]:
            got = posted_by_rule("Purchase", t, "AccountBasedExpenseLineDetail", lambda t, part: t.get("EntityRef"))
            if got:
                add("P%s" % t.get("Id"), t.get("TxnDate"), got["amount"], "out", t.get("AccountRef") or {}, ("Purchase", t.get("Id")), got["held_in"], t.get("PrivateNote"),
                    note=got["note"], payee=got["payee"], posted_as="expense")
        for t in raw["Deposit"]:
            got = posted_by_rule("Deposit", t, "DepositLineDetail", lambda t, part: part["DepositLineDetail"].get("Entity"))
            if got:
                add("D%s" % t.get("Id"), t.get("TxnDate"), got["amount"], "in", t.get("DepositToAccountRef") or {}, ("Deposit", t.get("Id")), got["held_in"], t.get("PrivateNote"),
                    note=got["note"], payee=got["payee"], posted_as="deposit")
        recorded = [dict(type=entity, id=t.get("Id"), number=t.get("DocNumber"), date=t.get("TxnDate"), direction=direction,
                         amount_cents=cents(t.get("TotalAmt")), bank_account_id=(bank(t) or {}).get("value"),
                         payee=((t.get("EntityRef") or t.get("VendorRef") or t.get("CustomerRef") or {}).get("name")))
                    for entity, direction, bank in RECORDED_PAYMENTS for t in raw[entity] if (entity, t.get("Id")) not in own]

        def near(line, in_account):
            return sorted((dict(type=r["type"], id=r["id"], number=r["number"], date=r["date"], payee=r["payee"],
                                days_apart=abs((day(r["date"]) - day(line["date"])).days))
                           for r in recorded if r["direction"] == line["direction"] and r["amount_cents"] == line["amount_cents"]
                           and r["bank_account_id"] in in_account and r["date"] and line["date"]
                           and abs((day(r["date"]) - day(line["date"])).days) <= MATCH_DAYS), key=lambda r: (r["days_apart"], r["type"], r["id"]))

        def one_each(candidates):
            """Give each recorded payment to one line only, nearest dates first. candidates: {line id: [payments]}."""
            pairs = sorted((c["days_apart"], line_id, c["type"], c["id"]) for line_id, found in candidates.items() for c in found)
            given, used = {}, set()
            for _, line_id, kind, txn in pairs:
                if line_id not in given and (kind, txn) not in used:
                    given[line_id] = (kind, txn)
                    used.add((kind, txn))
            return given

        # A payment already sitting in the clearing account cancels one line, not every line of that amount.
        # A charge recorded on a card can only sit in a card account, so a card line is cancelled from the card clearing account.
        home = lambda l: (account["Id"], card["Id"]) if card and l["bank_account_type"] == "Credit Card" else (account["Id"],)
        # The two bank lines of one transfer between the company's own accounts cancel each other in the clearing account
        # once an approved pairing has put each record's number in the other's memo.
        by_record = {(l["record_type"], l["record_id"]): l for l in lines}
        for line in lines:
            other = by_record.get(line["pair"]) if line["pair"] else None
            mutual = (other is not None and other is not line and other["pair"] == (line["record_type"], line["record_id"])
                      and other["direction"] != line["direction"] and other["amount_cents"] == line["amount_cents"] and other["clearing_id"] == line["clearing_id"])
            line["paired_with"] = other["id"] if mutual else None
        in_clearing = {l["id"]: near(l, home(l)) for l in lines if not l["paired_with"]}
        cancels = one_each(in_clearing)
        for line in lines:
            if line["paired_with"]:
                other = by_record[line["pair"]]
                line["cleared_by"] = [dict(type=other["record_type"], id=other["record_id"], number=None, date=other["date"], payee=None, pair=True, line_id=other["id"],
                                           bank_account=other["bank_account"], days_apart=abs((day(other["date"]) - day(line["date"])).days))]
            else:
                line["cleared_by"] = [c for c in in_clearing[line["id"]] if (c["type"], c["id"]) == cancels.get(line["id"])]
            side = "source" if line["direction"] == "out" else "target"
            line["recorded_transfers"] = [dict(id=t["id"], date=t["date"], from_account=t["source"].get("name"), to_account=t["target"].get("name"))
                                          for t in between if t["amount_cents"] == line["amount_cents"] and t[side].get("value") == line["bank_account_id"]
                                          and t["date"] and line["date"] and abs((day(t["date"]) - day(line["date"])).days) <= MATCH_DAYS]
        open_lines = {l["id"]: near(l, (l["bank_account_id"],)) for l in lines if not l["cleared_by"]}
        best = one_each(open_lines)
        for line in lines:
            line["recorded"] = [dict(c, best_fit=(c["type"], c["id"]) == best.get(line["id"])) for c in open_lines.get(line["id"], [])]
        lines.sort(key=lambda l: (l["date"] or "", l["id"]), reverse=True)
        return dict(found=True, id=account["Id"], name=account["Name"], type=account.get("AccountType"),
                    balance_cents=cents(account.get("CurrentBalance")), lines=lines,
                    card=dict(id=card["Id"], name=card["Name"], balance_cents=cents(card.get("CurrentBalance"))) if card else None)

    def move_to_clearing(self, line_id, kind, txn_id, name=CLEARING):
        """Change one recorded payment's bank account to the clearing account, and read it back.

        Allowed only for a payment that clearing() paired with the named clearing line. A payment
        recorded in a bank account moves to the bank clearing account. A charge or a bill payment
        recorded on a credit card moves to the card clearing account (D-045), which must exist.
        Nothing else in the record changes and nothing is deleted.
        """
        before = self.clearing(name)
        if not before.get("found"):
            raise QboError("no account named %s in this company" % name)
        line = next((l for l in before["lines"] if l["id"] == str(line_id)), None)
        if not line:
            raise QboError("no clearing line %s" % line_id)
        if not any(r["type"] == kind and r["id"] == str(txn_id) for r in line["recorded"]):
            raise QboError("%s %s is not a recorded payment paired with that line" % (kind, txn_id))
        on_card = line["bank_account_type"] == "Credit Card"
        if on_card and not before["card"]:
            raise QboError("this line is on a credit card and this company has no credit card account named %s to move its payment to" % CARD_CLEARING)
        if line["bank_account_type"] != "Bank" and not on_card:
            raise QboError("payments move from bank and credit card accounts only; this one is in a %s account" % line["bank_account_type"])
        target = before["card"] if on_card else before
        place = dict(RECORDED_PLACES)[kind]
        record = self._get("%s/%s" % (kind.lower(), txn_id))[kind]
        if (place(record) or {}).get("value") != line["bank_account_id"]:
            raise QboError("%s %s is no longer recorded in %s" % (kind, txn_id, line["bank_account"]))
        if on_card and (kind not in ("Purchase", "BillPayment") or record.get("Credit")):
            raise QboError("%s %s is not a card charge or a bill paid by card" % (kind, txn_id))
        place(record).clear()
        place(record).update(value=target["id"], name=target["name"])
        self._post(kind.lower(), record)
        now = self._get("%s/%s" % (kind.lower(), txn_id))[kind]
        moved = (place(now) or {}).get("value") == target["id"] and int(round(float(now.get("TotalAmt") or 0) * 100)) == line["amount_cents"]
        after = self.clearing(name)
        result = dict(moved=moved, kind=kind, id=str(txn_id), number=now.get("DocNumber"), from_account=line["bank_account"], to_account=target["name"],
                      balance_before_cents=before["balance_cents"], balance_after_cents=after["balance_cents"])
        if on_card:
            result.update(card_balance_before_cents=before["card"]["balance_cents"], card_balance_after_cents=(after.get("card") or {}).get("balance_cents"))
        return result

    def pair_transfer(self, line_id, other_id, name=CLEARING):
        """Mark two clearing lines as the two sides of one transfer between the company's own accounts, and read it back.

        The rules already booked money out of one bank account and into another through the clearing account, so the
        books are right as they stand; the only change is a note on each of the two records naming the other. Refused
        unless the lines are open, of the same amount, in opposite directions, in two different bank accounts, held in
        the same clearing account and at most PAIR_DAYS apart. Nothing is deleted.
        """
        before = self.clearing(name)
        if not before.get("found"):
            raise QboError("no account named %s in this company" % name)
        found = {l["id"]: l for l in before["lines"]}
        a, b = found.get(str(line_id)), found.get(str(other_id))
        if not a or not b or a is b:
            raise QboError("no two clearing lines %s and %s" % (line_id, other_id))
        if not (a["paired_with"] == b["id"] and b["paired_with"] == a["id"]):
            if a["cleared_by"] or b["cleared_by"]:
                raise QboError("one of these lines is already cleared")
            if a["direction"] == b["direction"] or a["amount_cents"] != b["amount_cents"]:
                raise QboError("a transfer is the same amount going out of one account and into another")
            if a["bank_account_id"] == b["bank_account_id"] or a["bank_account_type"] != "Bank" or b["bank_account_type"] != "Bank":
                raise QboError("this build pairs transfers between two different bank accounts only")
            if a["clearing_id"] != b["clearing_id"]:
                raise QboError("the two lines sit in different clearing accounts, so they do not cancel")
            if abs((date.fromisoformat(a["date"][:10]) - date.fromisoformat(b["date"][:10])).days) > PAIR_DAYS:
                raise QboError("the two lines are more than %d days apart" % PAIR_DAYS)
            for line, other in ((a, b), (b, a)):
                kind, wanted = line["record_type"], (other["record_type"], other["record_id"])
                record = self._get("%s/%s" % (kind.lower(), line["record_id"]))[kind]
                named = pair_of(record.get("PrivateNote"))
                if named == wanted:
                    continue                                 # an earlier try got this far
                if named:
                    raise QboError("%s %s is already marked as one side of another transfer" % (kind, line["record_id"]))
                mark = PAIR_NOTE % wanted
                record["PrivateNote"] = "%s | %s" % (record["PrivateNote"], mark) if record.get("PrivateNote") else mark
                self._post(kind.lower(), record)
        after = {l["id"]: l for l in self.clearing(name)["lines"]}
        paired = (after.get(a["id"]) or {}).get("paired_with") == b["id"] and (after.get(b["id"]) or {}).get("paired_with") == a["id"]
        return dict(paired=paired, line=a["id"], other=b["id"], accounts=[a["bank_account"], b["bank_account"]], amount_cents=a["amount_cents"])

    def probe(self):
        """Ask the sandbox which kinds of record this connection can read. Reads only.

        The first group is activity already recorded in the books. The second is every name a
        bank feed's unreviewed ("For Review") lines could plausibly go by; none is documented by
        Intuit, so each is expected to be refused, and the refusal is the evidence.
        """
        def ask(kind, name, path, params):
            status, raw = self._request(path, params)
            try:
                data = json.loads(raw)
            except ValueError:
                data = {}
            if status == 200:
                return dict(kind=kind, name=name, readable=True, count=data.get("QueryResponse", {}).get("totalCount"))
            fault = {k.lower(): v for k, v in data.items()}.get("fault") or {}
            first = ({k.lower(): v for k, v in fault.items()}.get("error") or [{}])[0]
            first = {k.lower(): v for k, v in first.items()}
            said = first.get("detail") or first.get("message") or ""
            return dict(kind=kind, name=name, readable=False, status=status, said=str(said)[:160])
        count = lambda kind, entity: ask(kind, entity, "query", {"query": "select count(*) from " + entity})
        return ([count("recorded", e) for e in RECORDED] + [count("bank_feed", e) for e in FEED_NAMES]
                + [ask("bank_feed", path, path, None) for path in FEED_PATHS])


def from_environment(environ):
    if not environ.get("INTUIT_CLIENT_ID") or not environ.get("INTUIT_CLIENT_SECRET"):
        return None
    base = (environ.get("PUBLIC_URL") or environ.get("RENDER_EXTERNAL_URL") or "http://127.0.0.1:8770").rstrip("/")
    return Qbo(environ["INTUIT_CLIENT_ID"], environ["INTUIT_CLIENT_SECRET"], base + "/qbo/callback")
