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
MATCH_DAYS = 21
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

        Bank rules post each bank line against the clearing account, as a transfer or as an
        expense whose category is the clearing account. For each line this lists payments of
        the same amount already recorded in the same bank account ("recorded": probably the
        same money a second time) and payments already recorded in the clearing account
        itself ("cleared_by": they cancel the line). The agent proposes; a person decides.
        """
        found = self.query("select * from Account where Name = '%s'" % name.replace("'", "\\'")).get("Account", [])
        if not found:
            return dict(found=False, name=name)
        account = found[0]
        kinds = {a["Id"]: a.get("AccountType") for a in self.query("select * from Account maxresults 1000").get("Account", [])}
        cents = lambda amount: int(round(float(amount or 0) * 100))
        day = lambda text: date.fromisoformat(text[:10])
        raw = {entity: self.query("select * from %s maxresults 1000" % entity).get(entity, []) for entity, _, _ in RECORDED_PAYMENTS}
        lines, own = [], set()

        def add(line_id, when, amount, direction, bank, **more):
            lines.append(dict(id=line_id, date=when, amount_cents=cents(amount), direction=direction, bank_account=bank.get("name"),
                              bank_account_id=bank.get("value"), bank_account_type=kinds.get(bank.get("value")), **more))

        for t in self.query("select * from Transfer maxresults 1000").get("Transfer", []):
            source, target = t.get("FromAccountRef") or {}, t.get("ToAccountRef") or {}
            if account["Id"] not in (source.get("value"), target.get("value")):
                continue
            direction = "out" if target.get("value") == account["Id"] else "in"     # as the bank account saw it
            add(t["Id"], t.get("TxnDate"), t.get("Amount"), direction, source if direction == "out" else target,
                note=t.get("PrivateNote"), payee=None, posted_as="transfer")
        for t in raw["Purchase"]:
            for part in t.get("Line", []):
                if ((part.get("AccountBasedExpenseLineDetail") or {}).get("AccountRef") or {}).get("value") == account["Id"]:
                    own.add(("Purchase", t.get("Id")))
                    add("P%s" % t.get("Id"), t.get("TxnDate"), part.get("Amount"), "out", t.get("AccountRef") or {},
                        note=part.get("Description") or t.get("PrivateNote"), payee=(t.get("EntityRef") or {}).get("name"), posted_as="expense")
        recorded = [dict(type=entity, id=t.get("Id"), number=t.get("DocNumber"), date=t.get("TxnDate"), direction=direction,
                         amount_cents=cents(t.get("TotalAmt")), bank_account_id=(bank(t) or {}).get("value"),
                         payee=((t.get("EntityRef") or t.get("VendorRef") or t.get("CustomerRef") or {}).get("name")))
                    for entity, direction, bank in RECORDED_PAYMENTS for t in raw[entity] if (entity, t.get("Id")) not in own]
        for line in lines:
            def near(in_account):
                return sorted((dict(type=r["type"], id=r["id"], number=r["number"], date=r["date"], payee=r["payee"],
                                    days_apart=abs((day(r["date"]) - day(line["date"])).days))
                               for r in recorded if r["direction"] == line["direction"] and r["amount_cents"] == line["amount_cents"]
                               and r["bank_account_id"] == in_account and r["date"] and line["date"]
                               and abs((day(r["date"]) - day(line["date"])).days) <= MATCH_DAYS), key=lambda r: r["days_apart"])
            line["recorded"], line["cleared_by"] = near(line["bank_account_id"]), near(account["Id"])
        lines.sort(key=lambda l: (l["date"] or "", l["id"]), reverse=True)
        return dict(found=True, id=account["Id"], name=account["Name"], type=account.get("AccountType"),
                    balance_cents=cents(account.get("CurrentBalance")), lines=lines)

    def move_to_clearing(self, line_id, kind, txn_id, name=CLEARING):
        """Change one recorded payment's bank account to the clearing account, and read it back.

        Allowed only for a payment that clearing() paired with the named clearing line, and only
        when that line came from a bank account (not a credit card). Nothing is deleted.
        """
        before = self.clearing(name)
        if not before.get("found"):
            raise QboError("no account named %s in this company" % name)
        line = next((l for l in before["lines"] if l["id"] == str(line_id)), None)
        if not line:
            raise QboError("no clearing line %s" % line_id)
        if not any(r["type"] == kind and r["id"] == str(txn_id) for r in line["recorded"]):
            raise QboError("%s %s is not a recorded payment paired with that line" % (kind, txn_id))
        if line["bank_account_type"] != "Bank":
            raise QboError("this first build moves payments recorded in bank accounts only; this one is in a %s account" % line["bank_account_type"])
        place = dict(RECORDED_PLACES)[kind]
        record = self._get("%s/%s" % (kind.lower(), txn_id))[kind]
        if (place(record) or {}).get("value") != line["bank_account_id"]:
            raise QboError("%s %s is no longer recorded in %s" % (kind, txn_id, line["bank_account"]))
        place(record).clear()
        place(record).update(value=before["id"], name=before["name"])
        self._post(kind.lower(), record)
        now = self._get("%s/%s" % (kind.lower(), txn_id))[kind]
        moved = (place(now) or {}).get("value") == before["id"] and int(round(float(now.get("TotalAmt") or 0) * 100)) == line["amount_cents"]
        after = self.clearing(name)
        return dict(moved=moved, kind=kind, id=str(txn_id), number=now.get("DocNumber"), from_account=line["bank_account"], to_account=before["name"],
                    balance_before_cents=before["balance_cents"], balance_after_cents=after["balance_cents"])

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
