"""The agent's only door to a set of books.

Every call names the company (realm_id). A ledger never has a "current
company": that is how a posting to the wrong client's books is made impossible
by construction instead of by care. FakeLedger holds fictional companies for
development; a QuickBooks implementation will provide the same methods.
"""
import copy


class LedgerError(Exception):
    pass


OPENING_BALANCE_EQUITY = "Opening Balance Equity"


class Books:
    """Several sets of books behind one door. The company named in each call
    chooses the ledger; a company nobody registered goes to the fallback, which
    refuses what it does not hold."""
    METHODS = ("company", "accounts", "bank_accounts", "pending_feed", "history", "open_bills", "open_invoices", "read_back",
               "categorize", "match", "transfer", "move", "payees")

    def __init__(self, fallback):
        self.fallback, self.by_realm = fallback, {}

    def add(self, realm_id, ledger):
        self.by_realm[str(realm_id)] = ledger

    def __getattr__(self, name):
        if name not in Books.METHODS:
            raise AttributeError(name)

        def call(realm_id, *args, **kwargs):
            return getattr(self.by_realm.get(str(realm_id), self.fallback), name)(realm_id, *args, **kwargs)
        return call


class FakeLedger:
    """In-memory fictional books. Amounts are integer cents; money out is negative."""

    def __init__(self, companies):
        self.companies = {str(c["realm_id"]): copy.deepcopy(c) for c in companies}
        self.writes = 0

    def _c(self, realm_id):
        try:
            return self.companies[str(realm_id)]
        except KeyError:
            raise LedgerError("no company with realm_id %s" % realm_id)

    def _line(self, realm_id, feed_id):
        for line in self._c(realm_id)["feed"]:
            if line["id"] == feed_id:
                return line
        raise LedgerError("no bank feed line %s in realm %s" % (feed_id, realm_id))

    # -- reads -----------------------------------------------------------
    def company(self, realm_id):
        c = self._c(realm_id)
        return {k: c[k] for k in ("realm_id", "name", "closed_through", "fiscal_year_start", "today")}

    def accounts(self, realm_id):
        return copy.deepcopy(self._c(realm_id)["accounts"])

    def bank_accounts(self, realm_id):
        return [a["name"] for a in self._c(realm_id)["accounts"] if a["type"] == "Bank"]

    def payees(self, realm_id):
        self._c(realm_id)
        return None                       # these books take any payee name as text; there is no list to add to

    def pending_feed(self, realm_id):
        return [copy.deepcopy(l) for l in self._c(realm_id)["feed"] if l["status"] == "pending"]

    def history(self, realm_id):
        return copy.deepcopy(self._c(realm_id)["posted"])

    def open_bills(self, realm_id):
        return [copy.deepcopy(b) for b in self._c(realm_id)["bills"] if b["status"] == "open"]

    def open_invoices(self, realm_id):
        return [copy.deepcopy(i) for i in self._c(realm_id)["invoices"] if i["status"] == "open"]

    def read_back(self, realm_id, feed_id):
        line = copy.deepcopy(self._line(realm_id, feed_id))
        posted = [t for t in self._c(realm_id)["posted"] if t.get("feed_id") == feed_id]
        line["posted"] = copy.deepcopy(posted[-1]) if posted else None
        return line

    # -- writes: add or change, never delete -------------------------------
    def _post(self, realm_id, line, **fields):
        c = self._c(realm_id)
        if line["status"] != "pending":
            raise LedgerError("bank feed line %s is already %s" % (line["id"], line["status"]))
        self.writes += 1
        txn = dict(id="T%05d" % (len(c["posted"]) + 1), date=line["date"], amount_cents=line["amount_cents"],
                   bank_account=line["bank_account"], description=line["description"], feed_id=line["id"],
                   source="feed", **fields)
        c["posted"].append(txn)
        return txn

    def categorize(self, realm_id, feed_id, account, vendor, memo, by_person=False):
        c, line = self._c(realm_id), self._line(realm_id, feed_id)
        if account not in [a["name"] for a in c["accounts"]]:
            raise LedgerError("no account named %s" % account)
        txn = self._post(realm_id, line, account=account, vendor=vendor, memo=memo, kind="categorize")
        line["status"] = "categorized"
        return txn["id"]

    def match(self, realm_id, feed_id, txn_type, txn_id):
        c, line = self._c(realm_id), self._line(realm_id, feed_id)
        book = c["bills"] if txn_type == "bill" else c["invoices"]
        found = [t for t in book if t["id"] == txn_id and t["status"] == "open"]
        if not found:
            raise LedgerError("no open %s %s" % (txn_type, txn_id))
        if abs(found[0]["amount_cents"]) != abs(line["amount_cents"]):
            raise LedgerError("amount of %s %s differs from the bank line" % (txn_type, txn_id))
        party = found[0].get("vendor") or found[0].get("customer")
        txn = self._post(realm_id, line, account="Accounts Payable" if txn_type == "bill" else "Accounts Receivable",
                         vendor=party, memo="", kind="match", matched_type=txn_type, matched_id=txn_id)
        found[0]["status"] = "paid"
        line["status"] = "matched"
        return txn["id"]

    def move(self, realm_id, feed_id, txn_type, txn_id):
        raise LedgerError("these fictional books have no payments recorded ahead of the bank feed")

    def transfer(self, realm_id, feed_id, other_account):
        line = self._line(realm_id, feed_id)
        if other_account not in self.bank_accounts(realm_id) or other_account == line["bank_account"]:
            raise LedgerError("%s is not another bank account of this company" % other_account)
        txn = self._post(realm_id, line, account=other_account, vendor=None, memo="", kind="transfer")
        line["status"] = "transferred"
        return txn["id"]
