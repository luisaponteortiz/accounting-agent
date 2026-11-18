"""The Ledger methods over a QuickBooks SANDBOX company, worked through its clearing account.

Bank rules in the company post every bank line against one clearing account
(D-042). Here each such line is the agent's bank feed line. Clearing it means
one of four things, each a change to an existing record or a new payment
record, never a deletion:

categorize   the line's own record gets its real category and payee in place
             of the clearing account
match        an open bill or invoice of the same amount is paid from, or into,
             the clearing account
move         a payment that was already recorded in the bank account is moved
             to the clearing account (D-043)
transfer     not built for QuickBooks yet

Every call names the company and is refused unless it is the connected one.
The connection underneath (qbo.py) can reach only Intuit's sandbox host.
"""
from datetime import date

from .ledger import LedgerError
from .qbo import CLEARING, QboError

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
LINE_RECORDS = {"P": ("Purchase", "AccountBasedExpenseLineDetail"), "D": ("Deposit", "DepositLineDetail")}
OPEN_ITEMS = {"bill": ("Bill", "BillPayment"), "invoice": ("Invoice", "Payment")}
cents = lambda amount: int(round(float(amount or 0) * 100))


def guarded(method):
    """A refusal from QuickBooks reaches the agent as a refusal from the ledger."""
    def call(self, realm_id, *args, **kwargs):
        if not self.q.connection or str(realm_id) != self.q.connection["realm_id"]:
            raise LedgerError("QuickBooks is not connected to company %s" % realm_id)
        try:
            return method(self, str(realm_id), *args, **kwargs)
        except QboError as problem:
            raise LedgerError(str(problem))
    return call


class QboLedger:
    def __init__(self, qbo, clearing=CLEARING, today=date.today, add_payees=False):
        """add_payees: when a person approves a payee the books do not have, add it. Off unless the owner decides so."""
        self.q, self.clearing, self.today, self.add_payees = qbo, clearing, today, add_payees

    # -- helpers -----------------------------------------------------------
    def _lines(self):
        got = self.q.clearing(self.clearing)
        if not got.get("found"):
            raise LedgerError("this company has no account named %s" % self.clearing)
        return got

    def _item(self, line):
        signed = -line["amount_cents"] if line["direction"] == "out" else line["amount_cents"]
        return dict(id=line["id"], date=line["date"], amount_cents=signed, description=line["note"] or "", bank_account=line["bank_account"],
                    status="pending", payee=line["payee"], posted_as=line["posted_as"], bank_account_type=line["bank_account_type"],
                    recorded=line["recorded"])

    def _pending(self, feed_id):
        got = self._lines()
        line = next((l for l in got["lines"] if l["id"] == str(feed_id)), None)
        if not line:
            raise LedgerError("no clearing line %s" % feed_id)
        if line["cleared_by"]:
            raise LedgerError("clearing line %s is already cleared" % feed_id)
        return got, line

    def _all(self, entity):
        return self.q.query("select * from %s maxresults 1000" % entity).get(entity, [])

    def _account(self, name):
        found = [a for a in self._all("Account") if name in (a.get("FullyQualifiedName"), a.get("Name"))]
        if not found or name == self.clearing:
            raise LedgerError("no account named %s" % name)
        return found[0]

    def _party(self, name, entities, add=None):
        """The payee as the books hold it. add: the kind to create when the books have none (a person approved it and the option is on)."""
        name = " ".join(name.split())
        for entity in entities:
            for row in self._all(entity):
                if " ".join((row.get("DisplayName") or "").split()).lower() == name.lower():
                    return dict(value=row["Id"], name=row["DisplayName"], type=entity)
        if not add:
            raise LedgerError("no %s named %s in this company; add it in QuickBooks or choose an existing one" % (" or ".join(e.lower() for e in entities), name))
        if not name or ":" in name or len(name) > 100:
            raise LedgerError("%r cannot be a payee name in QuickBooks" % name)
        made = self.q._post(add.lower(), {"DisplayName": name})[add]
        return dict(value=made["Id"], name=made["DisplayName"], type=add)

    def _record_of(self, feed_id):
        """The record behind a clearing line that a rule posted as an expense or a deposit."""
        kind, detail = LINE_RECORDS.get(str(feed_id)[:1], (None, None))
        if not kind:
            raise LedgerError("line %s was posted as a transfer, which cannot carry a category; post it with an expense or deposit rule" % feed_id)
        return kind, detail, self.q._get("%s/%s" % (kind.lower(), str(feed_id)[1:]))[kind]

    # -- reads -------------------------------------------------------------
    @guarded
    def company(self, realm_id):
        info = self.q._get("companyinfo/" + realm_id)["CompanyInfo"]
        closed = ((self.q._get("preferences").get("Preferences") or {}).get("AccountingInfoPrefs") or {}).get("BookCloseDate") or ""
        today = self.today()
        month = MONTHS.index(info.get("FiscalYearStartMonth") or "January") + 1
        start = date(today.year if today.month >= month else today.year - 1, month, 1)
        return dict(realm_id=realm_id, name=info.get("CompanyName"), closed_through=closed[:10], fiscal_year_start=start.isoformat(), today=today.isoformat())

    @guarded
    def accounts(self, realm_id):
        return [{"name": a.get("FullyQualifiedName") or a.get("Name"), "type": a.get("AccountType")} for a in self._all("Account") if a.get("Name") != self.clearing]

    @guarded
    def bank_accounts(self, realm_id):
        return [a.get("FullyQualifiedName") or a.get("Name") for a in self._all("Account") if a.get("AccountType") == "Bank" and a.get("Name") != self.clearing]

    @guarded
    def pending_feed(self, realm_id):
        return [self._item(l) for l in self._lines()["lines"] if not l["cleared_by"]]

    @guarded
    def history(self, realm_id):
        """How the books treated payees before: recorded expenses and deposits that carry a category of their own."""
        clearing = next((a["Id"] for a in self._all("Account") if a.get("Name") == self.clearing), None)
        out = []
        for kind, detail, sign, party in (("Purchase", "AccountBasedExpenseLineDetail", -1, lambda t, d: t.get("EntityRef")),
                                          ("Deposit", "DepositLineDetail", 1, lambda t, d: d.get("Entity"))):
            for t in self._all(kind):
                part = next((l for l in t.get("Line", []) if (l.get(detail) or {}).get("AccountRef")), None)
                bank = t.get("AccountRef") if kind == "Purchase" else t.get("DepositToAccountRef")
                if not part or part[detail]["AccountRef"].get("value") == clearing or (bank or {}).get("value") == clearing:
                    continue
                vendor = (party(t, part[detail]) or {}).get("name")
                out.append(dict(id="%s %s" % (kind, t.get("Id")), date=t.get("TxnDate"), amount_cents=sign * cents(t.get("TotalAmt")), bank_account=(bank or {}).get("name"),
                                description=part.get("Description") or t.get("PrivateNote") or vendor or "", feed_id=None, source="books",
                                account=part[detail]["AccountRef"].get("name"), vendor=vendor, memo=t.get("PrivateNote") or "", kind="categorize"))
        return out

    def _open(self, entity, party):
        return [dict(id=t["Id"], number=t.get("DocNumber"), amount_cents=cents(t.get("Balance")), due=t.get("DueDate"), status="open",
                     **{party: (t.get(party.capitalize() + "Ref") or {}).get("name") or ""})
                for t in self.q.query("select * from %s where Balance > '0' maxresults 1000" % entity).get(entity, []) if cents(t.get("Balance")) > 0]

    @guarded
    def open_bills(self, realm_id):
        return self._open("Bill", "vendor")

    @guarded
    def open_invoices(self, realm_id):
        return self._open("Invoice", "customer")

    @guarded
    def read_back(self, realm_id, feed_id):
        """Where a line stands now, read from QuickBooks, in the terms the agent's check uses."""
        line = next((l for l in self._lines()["lines"] if l["id"] == str(feed_id)), None)
        if line and not line["cleared_by"]:
            return dict(self._item(line), posted=None)
        if line:                                             # a payment in the clearing account cancels it
            by = line["cleared_by"][0]
            record = self.q._get("%s/%s" % (by["type"].lower(), by["id"]))[by["type"]]
            linked = next((x for l in record.get("Line", []) for x in l.get("LinkedTxn", []) if x.get("TxnType") in ("Bill", "Invoice")), {})
            item = self._item(line)
            return dict(item, status="matched", posted=dict(id="%s %s" % (by["type"], by["id"]), date=item["date"], amount_cents=item["amount_cents"], kind="move",
                        moved_type=by["type"], moved_id=by["id"], matched_type=(linked.get("TxnType") or "").lower() or None, matched_id=linked.get("TxnId"),
                        account=None, vendor=by.get("payee")))
        kind, detail, record = self._record_of(feed_id)     # no longer in the clearing account: it has a category of its own
        part = next((l for l in record.get("Line", []) if (l.get(detail) or {}).get("AccountRef")), {})
        party = record.get("EntityRef") if kind == "Purchase" else (part.get(detail) or {}).get("Entity")
        bank = record.get("AccountRef") if kind == "Purchase" else record.get("DepositToAccountRef")
        signed = (-1 if kind == "Purchase" else 1) * cents(record.get("TotalAmt"))
        return dict(id=str(feed_id), date=record.get("TxnDate"), amount_cents=signed, description=part.get("Description") or "", bank_account=(bank or {}).get("name"),
                    status="categorized", posted=dict(id="%s %s" % (kind, record.get("Id")), date=record.get("TxnDate"), amount_cents=signed, kind="categorize",
                    account=((part.get(detail) or {}).get("AccountRef") or {}).get("name"), vendor=(party or {}).get("name")))

    # -- writes: change a record or add a payment, never delete --------------
    @guarded
    def categorize(self, realm_id, feed_id, account, vendor, memo, by_person=False):
        got, line = self._pending(feed_id)
        target = self._account(account)
        kind, detail, record = self._record_of(feed_id)
        parts = [l for l in record.get("Line", []) if ((l.get(detail) or {}).get("AccountRef") or {}).get("value") == got["id"]]
        if not parts:
            raise LedgerError("%s %s is no longer booked against %s" % (kind, record.get("Id"), self.clearing))
        add = ("Vendor" if kind == "Purchase" else "Customer") if self.add_payees and by_person else None   # never on a standing approval
        party = self._party(vendor, ("Vendor",) if kind == "Purchase" else ("Customer", "Vendor"), add) if vendor else None
        for part in parts:
            part[detail]["AccountRef"] = dict(value=target["Id"], name=target.get("FullyQualifiedName") or target.get("Name"))
            if party and kind == "Deposit":
                part[detail]["Entity"] = dict(party, type=party["type"].upper())
        if party and kind == "Purchase":
            record["EntityRef"] = party
        if memo and not record.get("PrivateNote"):
            record["PrivateNote"] = memo
        self.q._post(kind.lower(), record)
        return "%s %s" % (kind, record.get("Id"))

    @guarded
    def match(self, realm_id, feed_id, txn_type, txn_id):
        got, line = self._pending(feed_id)
        entity, payment = OPEN_ITEMS.get(txn_type, (None, None))
        if not entity:
            raise LedgerError("cannot match to a %s" % txn_type)
        if line["direction"] != ("out" if txn_type == "bill" else "in"):
            raise LedgerError("a %s cannot be paid by money going %s" % (txn_type, line["direction"]))
        if line["bank_account_type"] != "Bank":
            raise LedgerError("this build pays open items for bank account lines only; this one is in a %s account" % line["bank_account_type"])
        try:
            found = [self.q._get("%s/%s" % (entity.lower(), txn_id))[entity]]
        except QboError:
            found = []
        if not found or cents(found[0].get("Balance")) <= 0:
            raise LedgerError("no open %s %s" % (txn_type, txn_id))
        if cents(found[0].get("Balance")) != line["amount_cents"]:
            raise LedgerError("amount of %s %s differs from the bank line" % (txn_type, txn_id))
        amount, clearing = line["amount_cents"] / 100, dict(value=got["id"], name=got["name"])
        new = dict(TotalAmt=amount, TxnDate=line["date"], PrivateNote="Paid per bank line dated %s" % line["date"],
                   Line=[dict(Amount=amount, LinkedTxn=[dict(TxnId=found[0]["Id"], TxnType=entity)])])
        if txn_type == "bill":
            new.update(VendorRef=found[0]["VendorRef"], PayType="Check", CheckPayment=dict(BankAccountRef=clearing, PrintStatus="NotSet"))
        else:
            new.update(CustomerRef=found[0]["CustomerRef"], DepositToAccountRef=clearing)
        made = self.q._post(payment.lower(), new)[payment]
        return "%s %s" % (payment, made["Id"])

    @guarded
    def move(self, realm_id, feed_id, txn_type, txn_id):
        result = self.q.move_to_clearing(feed_id, txn_type, txn_id, self.clearing)
        if not result["moved"]:
            raise LedgerError("QuickBooks accepted the change but %s %s did not read back as moved" % (txn_type, txn_id))
        return "%s %s" % (txn_type, txn_id)

    @guarded
    def transfer(self, realm_id, feed_id, other_account):
        raise LedgerError("transfers between the company's own accounts are not built for QuickBooks yet; handle this one in the books")
