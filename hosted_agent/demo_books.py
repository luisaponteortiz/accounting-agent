"""Two fictional companies with three months of history and a bank feed that
holds one of each kind of line the agent has to tell apart. Nothing here is a
real business, person or account."""
from datetime import date, timedelta

TODAY = date(2026, 11, 17)


def _d(days_ago):
    return (TODAY - timedelta(days=days_ago)).isoformat()


def _accounts(extra=()):
    base = [("Operating Checking", "Bank"), ("Savings", "Bank"), ("Accounts Receivable", "Accounts Receivable"),
            ("Accounts Payable", "Accounts Payable"), ("Opening Balance Equity", "Equity"),
            ("Owner Draws", "Equity"), ("Sales", "Income"), ("Utilities", "Expense"),
            ("Software Subscriptions", "Expense"), ("Bank Charges", "Expense"), ("Rent", "Expense"),
            ("Office Supplies", "Expense"), ("Repairs and Maintenance", "Expense"),
            ("Merchant Fees", "Expense"), ("Insurance", "Expense"), ("Ask My Accountant", "Expense")]
    return [{"name": n, "type": t} for n, t in base + list(extra)]


def _history(recurring, months=3):
    """recurring: (description, vendor, account, amount_cents, day_offset)."""
    posted = []
    for m in range(1, months + 1):
        for description, vendor, account, cents, offset in recurring:
            posted.append(dict(id="H%03d" % (len(posted) + 1), date=_d(30 * m + offset), amount_cents=cents,
                               bank_account="Operating Checking", description=description, feed_id=None,
                               source="feed", account=account, vendor=vendor, memo="", kind="categorize"))
    return posted


def cafe():
    recurring = [("CITY POWER & LIGHT ACH 4471", "City Power and Light", "Utilities", -41250, 2),
                 ("LEDGERLY SOFTWARE *SUBSCR", "Ledgerly Software", "Software Subscriptions", -8900, 5),
                 ("HARBOR PROPERTIES RENT", "Harbor Properties", "Rent", -320000, 1),
                 ("CARDSWIPE MERCH FEES", "CardSwipe", "Merchant Fees", -15675, 3)]
    posted = _history(recurring)
    # one vendor the books show under two different accounts
    for i, account in enumerate(["Office Supplies", "Repairs and Maintenance", "Office Supplies"]):
        posted.append(dict(id="HX%d" % i, date=_d(20 + 9 * i), amount_cents=-(5400 + 700 * i),
                           bank_account="Operating Checking", description="OMNIMART ONLINE 88213", feed_id=None,
                           source="feed", account=account, vendor="OmniMart", memo="", kind="categorize"))
    feed = [
        ("F001", _d(3), -41980, "CITY POWER & LIGHT ACH 4502", "Operating Checking"),   # recurring vendor
        ("F002", _d(3), -8900, "LEDGERLY SOFTWARE *SUBSCR", "Operating Checking"),       # recurring vendor
        ("F003", _d(2), -320000, "HARBOR PROPERTIES RENT", "Operating Checking"),         # recurring, over the limit
        ("F004", _d(2), -64210, "NORTHSIDE PRODUCE CO", "Operating Checking"),            # pays an open bill exactly
        ("F005", _d(2), -500000, "ONLINE TRANSFER TO SAV", "Operating Checking"),         # transfer, this side
        ("F006", _d(2), 500000, "ONLINE TRANSFER FROM CHK", "Savings"),                   # transfer, other side
        ("F007", _d(1), -1500, "MONTHLY SERVICE FEE", "Operating Checking"),              # bank fee
        ("F008", _d(1), -23999, "BRIGHTSIGN STUDIO", "Operating Checking"),               # vendor never seen
        ("F009", _d(1), -6800, "OMNIMART ONLINE 90417", "Operating Checking"),            # vendor with mixed accounts
        ("F010", _d(1), -75000, "ZELLE PAYMENT TO J RIVERA", "Operating Checking"),       # payment to a person
        ("F011", _d(60), -41250, "CITY POWER & LIGHT ACH 4390", "Operating Checking"),    # dated in a closed period
        ("F012", _d(1), 184000, "DEPOSIT BAYVIEW CATERING", "Operating Checking"),        # pays an open invoice exactly
        ("F013", _d(1), 51234, "MOBILE DEPOSIT", "Operating Checking"),                   # deposit, source unknown
        ("F014", _d(4), -15675, "CARDSWIPE MERCH FEES", "Operating Checking"),            # recurring vendor
    ]
    return dict(
        realm_id="9001", name="Harbor Light Cafe LLC (fictional)", fiscal_year_start="2026-01-01",
        closed_through=_d(48), today=TODAY.isoformat(), accounts=_accounts(), posted=posted,
        bills=[dict(id="B100", vendor="Northside Produce Co", amount_cents=64210, due=_d(1), status="open"),
               dict(id="B101", vendor="Northside Produce Co", amount_cents=38000, due=_d(-10), status="open")],
        invoices=[dict(id="I200", customer="Bayview Catering", amount_cents=184000, due=_d(5), status="open")],
        feed=[dict(id=i, date=d, amount_cents=c, description=s, bank_account=b, status="pending")
              for i, d, c, s, b in feed])


def outfitters():
    recurring = [("GRANITE VALLEY WATER", "Granite Valley Water", "Utilities", -9340, 4),
                 ("SHIPFAST LABELS", "ShipFast", "Office Supplies", -12050, 6),
                 ("SUMMIT INSURANCE GRP", "Summit Insurance Group", "Insurance", -45500, 2)]
    feed = [
        ("G001", _d(2), -9410, "GRANITE VALLEY WATER", "Operating Checking"),
        ("G002", _d(2), -12050, "SHIPFAST LABELS", "Operating Checking"),
        ("G003", _d(1), -45500, "SUMMIT INSURANCE GRP", "Operating Checking"),
        ("G004", _d(1), -41980, "CITY POWER & LIGHT ACH 4502", "Operating Checking"),  # known to the cafe, new here
        ("G005", _d(1), -2500, "WIRE FEE", "Operating Checking"),
    ]
    return dict(
        realm_id="9002", name="Granite Ridge Outfitters Inc (fictional)", fiscal_year_start="2026-01-01",
        closed_through=_d(48), today=TODAY.isoformat(), accounts=_accounts(), posted=_history(recurring),
        bills=[], invoices=[],
        feed=[dict(id=i, date=d, amount_cents=c, description=s, bank_account=b, status="pending")
              for i, d, c, s, b in feed])


def companies():
    return [cafe(), outfitters()]
