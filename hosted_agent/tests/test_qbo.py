"""Review tests for the QuickBooks sandbox connection, with a stand-in for Intuit. No network."""
import json
import unittest
import urllib.parse

from hosted_agent import qbo


class Intuit:
    """A stand-in for Intuit: a token service and one small company whose recorded payments can be changed."""
    def __init__(self):
        self.calls, self.token_status, self.issued, self.refuse_change, self.ignore_change, self.closed = [], 200, 0, False, False, None
        self.accounts = [{"Id": "35", "Name": "Checking", "AccountType": "Bank"}, {"Id": "36", "Name": "Savings", "AccountType": "Bank"},
                         {"Id": "41", "Name": "Mastercard", "AccountType": "Credit Card"},
                         {"Id": "60", "Name": "Supplies", "AccountType": "Expense"}, {"Id": "61", "Name": "Legal", "AccountType": "Expense"},
                         {"Id": "62", "Name": "Utilities", "AccountType": "Expense"},
                         {"Id": "63", "Name": "Decks and Patios", "FullyQualifiedName": "Job Expenses:Decks and Patios", "AccountType": "Expense"},
                         {"Id": "70", "Name": "Opening Balance Equity", "AccountType": "Equity"},
                         {"Id": "91", "Name": "Card Feed Clearing", "AccountType": "Credit Card", "CurrentBalance": 0},
                         {"Id": "90", "Name": "Bank Feed Clearing", "AccountType": "Bank", "CurrentBalance": 377.22}]
        self.transfers = [
            {"Id": "T1", "TxnDate": "2026-10-21", "Amount": 114.09, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}, "PrivateNote": "PG E"},
            {"Id": "T2", "TxnDate": "2026-10-04", "Amount": 24.38, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}},
            {"Id": "T3", "TxnDate": "2026-10-05", "Amount": 500.0, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "36", "name": "Savings"}},
            {"Id": "T4", "TxnDate": "2026-10-10", "Amount": 34.0, "FromAccountRef": {"value": "41", "name": "Mastercard"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}},
            {"Id": "T5", "TxnDate": "2026-10-20", "Amount": 75.0, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}},
            {"Id": "T6", "TxnDate": "2026-10-22", "Amount": 75.0, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}}]
        self.records = {
            "BillPayment": [
                {"Id": "B6", "SyncToken": "0", "DocNumber": "6", "TxnDate": "2026-10-21", "TotalAmt": 114.09, "VendorRef": {"name": "PG&E"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}},
                 "Line": [{"Amount": 114.09, "LinkedTxn": [{"TxnId": "200", "TxnType": "Bill"}]}]},
                {"Id": "B7", "SyncToken": "0", "DocNumber": "7", "TxnDate": "2026-10-21", "TotalAmt": 114.09, "VendorRef": {"name": "Other Utility"}, "CheckPayment": {"BankAccountRef": {"value": "36", "name": "Savings"}}},
                {"Id": "B8", "SyncToken": "0", "DocNumber": "8", "TxnDate": "2026-08-01", "TotalAmt": 114.09, "VendorRef": {"name": "PG&E"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}}},
                {"Id": "B10", "SyncToken": "0", "DocNumber": "10", "TxnDate": "2026-10-28", "TotalAmt": 114.09, "VendorRef": {"name": "PG&E"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}}},
                {"Id": "B3", "SyncToken": "0", "DocNumber": "3", "TxnDate": "2026-10-20", "TotalAmt": 75.0, "VendorRef": {"name": "Books by Bessie"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}}},
                {"Id": "B9", "SyncToken": "0", "DocNumber": "9", "TxnDate": "2026-10-10", "TotalAmt": 34.0, "VendorRef": {"name": "Card Vendor"}, "PayType": "CreditCard", "CreditCardPayment": {"CCAccountRef": {"value": "41", "name": "Mastercard"}}}],
            "Purchase": [
                {"Id": "75", "SyncToken": "2", "TxnDate": "2026-11-01", "TotalAmt": 228.75, "PaymentType": "Check", "EntityRef": {"name": "Hicks Hardware"}, "AccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 228.75, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "60", "name": "Supplies"}}}]},
                {"Id": "20", "SyncToken": "0", "TxnDate": "2026-11-03", "TotalAmt": 228.75, "PaymentType": "Cash", "AccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 228.75, "Description": "HICKS HARDWARE 0443", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]},
                {"Id": "76", "SyncToken": "0", "DocNumber": "76", "TxnDate": "2026-10-22", "TotalAmt": 75.0, "PaymentType": "Check", "EntityRef": {"name": "Pam Seitz"}, "AccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 75.0, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "61", "name": "Legal"}}}]},
                {"Id": "21", "SyncToken": "0", "TxnDate": "2026-11-14", "TotalAmt": 419.8, "PaymentType": "Cash", "AccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 419.8, "Description": "CITY POWER & LIGHT ACH 4502", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]},
                {"Id": "22", "SyncToken": "0", "TxnDate": "2026-11-15", "TotalAmt": 642.1, "PaymentType": "Cash", "AccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 642.1, "Description": "NORTHSIDE PRODUCE CO", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]}] + [
                {"Id": "H%d" % month, "SyncToken": "0", "TxnDate": "2026-%02d-12" % month, "TotalAmt": 412.5, "PaymentType": "Check", "EntityRef": {"value": "V1", "name": "City Power and Light"},
                 "AccountRef": {"value": "35", "name": "Checking"}, "Line": [{"Amount": 412.5, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "62", "name": "Utilities"}}}]} for month in (8, 9, 10)],
            "Bill": [{"Id": "B100", "DocNumber": "100", "VendorRef": {"value": "V2", "name": "Northside Produce Co"}, "TotalAmt": 642.1, "Balance": 642.1, "DueDate": "2026-11-16"},
                     {"Id": "B101", "DocNumber": "101", "VendorRef": {"value": "V2", "name": "Northside Produce Co"}, "TotalAmt": 380.0, "Balance": 380.0, "DueDate": "2026-11-27"},
                     {"Id": "B099", "DocNumber": "99", "VendorRef": {"value": "V2", "name": "Northside Produce Co"}, "TotalAmt": 50.0, "Balance": 0}],
            "Invoice": [{"Id": "I200", "DocNumber": "200", "CustomerRef": {"value": "C1", "name": "Bayview Catering"}, "TotalAmt": 1840.0, "Balance": 1840.0, "DueDate": "2026-11-12"},
                        {"Id": "I201", "DocNumber": "201", "CustomerRef": {"value": "C1", "name": "Bayview Catering"}, "TotalAmt": 642.1, "Balance": 642.1, "DueDate": "2026-11-20"}],
            "Vendor": [{"Id": "V1", "DisplayName": "City Power and Light"}, {"Id": "V2", "DisplayName": "Northside Produce Co"}],
            "Customer": [{"Id": "C1", "DisplayName": "Bayview Catering"}],
            "Deposit": [
                {"Id": "30", "SyncToken": "0", "TxnDate": "2026-10-22", "TotalAmt": 868.15, "DepositToAccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 868.15, "Description": "DEPOSIT 1022", "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]},
                {"Id": "31", "SyncToken": "1", "TxnDate": "2026-10-21", "TotalAmt": 868.15, "DepositToAccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 868.15, "LinkedTxn": [{"TxnId": "300", "TxnType": "Payment"}]}]},
                {"Id": "32", "SyncToken": "0", "TxnDate": "2026-11-17", "TotalAmt": 200.0, "DepositToAccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 200.0, "Description": "A RENTAL", "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}, "Entity": {"name": "A Rental"}}}]},
                {"Id": "33", "SyncToken": "0", "TxnDate": "2026-11-16", "TotalAmt": 1840.0, "DepositToAccountRef": {"value": "35", "name": "Checking"},
                 "Line": [{"Amount": 1840.0, "Description": "DEPOSIT BAYVIEW CATERING", "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]}],
            "Payment": [
                {"Id": "40", "SyncToken": "0", "TxnDate": "2026-11-16", "TotalAmt": 200.0, "CustomerRef": {"name": "A Rental Customer"}, "DepositToAccountRef": {"value": "35", "name": "Checking"}}]}
        self.records["Transfer"] = self.transfers          # the same list: a transfer can be read and changed by its number too

    def add_transfer_lines(self, amount=500.0, out_date="2026-10-06", in_date="2026-10-07"):
        """What the two rules post when money moves from Checking to Savings: an expense and a deposit, both against clearing."""
        self.records["Purchase"].append({"Id": "24", "SyncToken": "0", "TxnDate": out_date, "TotalAmt": amount, "PaymentType": "Cash", "AccountRef": {"value": "35", "name": "Checking"},
                                         "Line": [{"Amount": amount, "Description": "ONLINE TRANSFER TO SAV 7781", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})
        self.records["Deposit"].append({"Id": "34", "SyncToken": "0", "TxnDate": in_date, "TotalAmt": amount, "PrivateNote": "Bank memo", "DepositToAccountRef": {"value": "36", "name": "Savings"},
                                        "Line": [{"Amount": amount, "Description": "ONLINE TRANSFER FROM CHK 4502", "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})

    def reply(self, status, data):
        return status, json.dumps(data).encode()

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        if url == qbo.TOKEN:
            self.issued += 1
            return self.reply(self.token_status, dict(access_token="ACCESS-%d" % self.issued, refresh_token="REFRESH-%d" % self.issued, expires_in=3600))
        if "/companyinfo/" in url:
            return self.reply(200, {"CompanyInfo": {"CompanyName": "Sandbox Company_US_1", "FiscalYearStartMonth": "January"}})
        parts = urllib.parse.urlsplit(url)
        tail = parts.path.split("/v3/company/")[-1].split("/")[1:]          # what follows the company number
        kind = next((k for k in self.records if tail and k.lower() == tail[0]), None)
        if kind and method == "GET" and len(tail) == 2:
            hit = [r for r in self.records[kind] if r["Id"] == tail[1]]
            return self.reply(200, {kind: hit[0]}) if hit else self.reply(400, {"Fault": {"Error": [{"Message": "Object Not Found"}]}})
        if tail == ["preferences"]:
            return self.reply(200, {"Preferences": {"AccountingInfoPrefs": {"BookCloseDate": self.closed} if self.closed else {}}})
        if kind and method == "POST" and "Id" not in json.loads(body):         # a new record
            sent = json.loads(body)
            if self.refuse_change:
                return self.reply(400, {"Fault": {"Error": [{"Message": "Business Validation Error", "Detail": "The change was refused."}]}})
            made = dict(sent, Id="N%d" % (len(self.records[kind]) + 1), SyncToken="0")
            self.records[kind].append(made)
            for part in sent.get("Line", []):
                for link in part.get("LinkedTxn", []):
                    paid = next(r for r in self.records[link["TxnType"]] if r["Id"] == link["TxnId"])
                    paid["Balance"] = round(paid["Balance"] - part["Amount"], 2)
            return self.reply(200, {kind: made})
        if kind and method == "POST":
            sent = json.loads(body)
            held = next(r for r in self.records[kind] if r["Id"] == sent["Id"])
            if self.refuse_change or sent.get("SyncToken") != held.get("SyncToken"):
                return self.reply(400, {"Fault": {"Error": [{"Message": "Stale Object Error", "Detail": "You and another user were working on the same thing.", "code": "5010"}], "type": "ValidationFault"}})
            if not self.ignore_change:
                place = dict(qbo.RECORDED_PLACES).get(kind, lambda t: None)
                if (place(sent) or {}).get("value") == "90" and (place(held) or {}).get("value") != "90":
                    sign = 1 if kind in ("Payment", "Deposit", "SalesReceipt") else -1      # money in adds to the clearing account
                    self.accounts[-1]["CurrentBalance"] = round(self.accounts[-1]["CurrentBalance"] + sign * held["TotalAmt"], 2)
                held.clear()
                held.update(sent, SyncToken=str(int(sent.get("SyncToken") or 0) + 1))
            return self.reply(200, {kind: held})
        asked = urllib.parse.parse_qs(parts.query)
        if "query" not in asked:
            return 404, b"<html>Not Found</html>"
        statement = asked["query"][0]
        if statement.split()[-1] in qbo.FEED_NAMES:
            return self.reply(400, {"Fault": {"Error": [{"Message": "Error parsing query", "Detail": "QueryParserError: Invalid entity", "code": "4000"}], "type": "ValidationFault"}})
        if "count(*)" in statement:
            return self.reply(200, {"QueryResponse": {"totalCount": 7}})
        if statement.startswith("select * from Account where Name"):
            return self.reply(200, {"QueryResponse": {"Account": [a for a in self.accounts if "'%s'" % a["Name"] in statement]}})
        if statement.startswith("select * from Account"):
            return self.reply(200, {"QueryResponse": {"Account": self.accounts}})
        if statement.startswith("select * from Transfer"):
            return self.reply(200, {"QueryResponse": {"Transfer": self.transfers}})
        entity = statement.split()[3]
        return self.reply(200, {"QueryResponse": {entity: self.records[entity]} if entity in self.records else {}})


class QboCase(unittest.TestCase):
    def setUp(self):
        self.now = [1000.0]
        self.intuit = Intuit()
        self.q = qbo.Qbo("the-id", "the-secret", "https://agent.example/qbo/callback", transport=self.intuit, clock=lambda: self.now[0])

    def start(self):
        url = self.q.authorize_url("Owner (test)")
        return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)

    def test_the_sign_in_link_asks_only_for_accounting_and_names_our_callback(self):
        sent = self.start()
        self.assertEqual((sent["scope"], sent["redirect_uri"], sent["response_type"]),
                         ([qbo.SCOPE], ["https://agent.example/qbo/callback"], ["code"]))
        self.assertNotIn("the-secret", json.dumps(sent))

    def test_only_the_sandbox_host_can_be_reached(self):
        self.assertEqual(qbo.API, "https://sandbox-quickbooks.api.intuit.com")
        self.q.finish(self.start()["state"][0], "code", "123")
        self.q.summary()
        hosts = {urllib.parse.urlsplit(c[1]).netloc for c in self.intuit.calls}
        self.assertEqual(hosts, {"oauth.platform.intuit.com", "sandbox-quickbooks.api.intuit.com"})

    def test_a_callback_needs_the_state_this_service_issued_and_only_once(self):
        with self.assertRaises(qbo.QboError):
            self.q.finish("made-up-state", "code", "123")
        state = self.start()["state"][0]
        self.assertEqual(self.q.finish(state, "code", "123"), "Owner (test)")
        with self.assertRaises(qbo.QboError):
            self.q.finish(state, "code", "123")

    def test_a_stale_state_or_a_refused_sign_in_connects_nothing(self):
        state = self.start()["state"][0]
        self.now[0] += qbo.STATE_SECONDS + 1
        with self.assertRaises(qbo.QboError):
            self.q.finish(state, "code", "123")
        self.intuit.token_status = 400
        with self.assertRaises(qbo.QboError):
            self.q.finish(self.start()["state"][0], "code", "123")
        with self.assertRaises(qbo.QboError):
            self.q.finish(self.start()["state"][0], "", "")
        self.assertIsNone(self.q.connection)

    def test_the_summary_reads_the_books_and_never_carries_a_token(self):
        self.q.finish(self.start()["state"][0], "code", "123")
        got = self.q.summary()
        self.assertEqual((got["company"], got["realm_id"], got["accounts"], got["environment"]), ("Sandbox Company_US_1", "123", 7, "sandbox"))
        self.assertEqual(got["recent_purchases"][0]["category"], "Supplies")
        text = json.dumps(got)
        for secret in ("ACCESS-", "REFRESH-", "the-secret"):
            self.assertNotIn(secret, text)
        self.assertTrue(all(c[0] in ("GET", "POST") and (c[0] == "GET" or c[1] == qbo.TOKEN) for c in self.intuit.calls))  # nothing written to the books

    def test_an_expired_access_token_is_refreshed_before_a_read(self):
        self.q.finish(self.start()["state"][0], "code", "123")
        self.now[0] += 4000
        self.q.summary()
        refresh = [c for c in self.intuit.calls if c[1] == qbo.TOKEN][-1]
        self.assertIn(b"grant_type=refresh_token", refresh[3])
        self.assertIn("Bearer ACCESS-2", [c[2].get("Authorization") for c in self.intuit.calls if "/companyinfo/" in c[1]])

    def test_the_bank_feed_test_only_reads_and_reports_each_refusal(self):
        with self.assertRaises(qbo.QboError):
            self.q.probe()                                   # nothing connected, nothing asked
        self.q.finish(self.start()["state"][0], "code", "123")
        before = len(self.intuit.calls)
        got = self.q.probe()
        recorded = [r for r in got if r["kind"] == "recorded"]
        feed = [r for r in got if r["kind"] == "bank_feed"]
        self.assertEqual([r["name"] for r in recorded], list(qbo.RECORDED))
        self.assertTrue(all(r["readable"] and r["count"] == 7 for r in recorded))
        self.assertEqual(len(feed), len(qbo.FEED_NAMES) + len(qbo.FEED_PATHS))
        self.assertFalse(any(r["readable"] for r in feed))
        self.assertEqual((feed[0]["status"], feed[0]["said"]), (400, "QueryParserError: Invalid entity"))
        self.assertEqual(feed[-1]["status"], 404)
        asked = self.intuit.calls[before:]
        self.assertTrue(all(c[0] == "GET" and c[1].startswith(qbo.API + "/v3/company/123/") for c in asked))
        self.assertNotIn("ACCESS-", json.dumps(got))

    def connect(self):
        self.q.finish(self.start()["state"][0], "code", "123")
        return len(self.intuit.calls)

    def line(self, got, line_id):
        return next(l for l in got["lines"] if l["id"] == line_id)

    def test_the_clearing_read_pairs_a_line_only_with_the_same_money_in_the_same_bank_account(self):
        before = self.connect()
        got = self.q.clearing()
        self.assertEqual((got["found"], got["id"], got["type"], got["balance_cents"]), (True, "90", "Bank", 37722))
        self.assertEqual(sorted(l["id"] for l in got["lines"]), ["D30", "D32", "D33", "P20", "P21", "P22", "T1", "T2", "T4", "T5", "T6"])   # the Checking to Savings transfer is not a clearing line
        paid, plain = self.line(got, "T1"), self.line(got, "T2")
        self.assertEqual((paid["amount_cents"], paid["direction"], paid["bank_account"], paid["bank_account_type"], paid["note"], paid["posted_as"]),
                         (11409, "out", "Checking", "Bank", "PG E", "transfer"))
        self.assertEqual([(r["type"], r["number"], r["days_apart"], r["best_fit"]) for r in paid["recorded"]],
                         [("BillPayment", "6", 0, True), ("BillPayment", "10", 7, False)])   # not the Savings one, not the August one; the nearest date is the best fit
        self.assertEqual((plain["note"], plain["recorded"], plain["cleared_by"]), (None, [], []))
        self.assertTrue(all(c[0] == "GET" for c in self.intuit.calls[before:]))
        self.assertFalse(self.q.clearing("No Such Account")["found"])

    def test_a_line_posted_by_an_expense_rule_keeps_the_bank_text_and_is_never_paired_with_itself(self):
        self.connect()
        line = self.line(self.q.clearing(), "P20")
        self.assertEqual((line["posted_as"], line["note"], line["payee"], line["amount_cents"], line["bank_account"]),
                         ("expense", "HICKS HARDWARE 0443", None, 22875, "Checking"))
        self.assertEqual([(r["type"], r["id"], r["payee"]) for r in line["recorded"]], [("Purchase", "75", "Hicks Hardware")])   # not Purchase 20, which is the line itself

    def test_moving_a_recorded_payment_changes_only_its_bank_account_and_reads_it_back(self):
        before = self.connect()
        kept = json.loads(json.dumps(self.intuit.records["BillPayment"][0]))
        got = self.q.move_to_clearing("T1", "BillPayment", "B6")
        self.assertEqual((got["moved"], got["kind"], got["id"], got["number"], got["from_account"], got["to_account"]),
                         (True, "BillPayment", "B6", "6", "Checking", "Bank Feed Clearing"))
        self.assertEqual((got["balance_before_cents"], got["balance_after_cents"]), (37722, 26313))
        writes = [c for c in self.intuit.calls[before:] if c[0] != "GET"]
        self.assertEqual([(c[0], c[1].split("/company/123/")[1].split("?")[0]) for c in writes], [("POST", "billpayment")])   # one change, nothing deleted
        self.assertNotIn("operation=delete", writes[0][1])
        sent, now = json.loads(writes[0][3]), self.intuit.records["BillPayment"][0]
        self.assertEqual(sent["SyncToken"], "0")
        kept["CheckPayment"]["BankAccountRef"] = {"value": "90", "name": "Bank Feed Clearing"}
        self.assertEqual(sent, kept)                                                 # every other field went back as it was read
        self.assertEqual(now["CheckPayment"]["BankAccountRef"]["value"], "90")
        line = self.line(self.q.clearing(), "T1")
        self.assertEqual(([r["id"] for r in line["recorded"]], [r["id"] for r in line["cleared_by"]]), ([], ["B6"]))
        with self.assertRaises(qbo.QboError):                                        # already moved: no longer a recorded pair of that line
            self.q.move_to_clearing("T1", "BillPayment", "B6")

    def test_a_purchase_can_be_moved_too(self):
        self.connect()
        got = self.q.move_to_clearing("P20", "Purchase", "75")
        self.assertTrue(got["moved"])
        self.assertEqual(self.intuit.records["Purchase"][0]["AccountRef"], {"value": "90", "name": "Bank Feed Clearing"})
        self.assertEqual(self.intuit.records["Purchase"][0]["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"]["name"], "Supplies")

    def test_money_in_lines_come_from_deposits_a_rule_posted_and_pair_with_recorded_deposits_and_customer_payments(self):
        self.connect()
        got = self.q.clearing()
        banked, rent = self.line(got, "D30"), self.line(got, "D32")
        self.assertEqual((banked["direction"], banked["posted_as"], banked["amount_cents"], banked["note"], banked["bank_account"]), ("in", "deposit", 86815, "DEPOSIT 1022", "Checking"))
        self.assertEqual([(r["type"], r["id"], r["days_apart"], r["best_fit"]) for r in banked["recorded"]], [("Deposit", "31", 1, True)])   # never Deposit 30 or 32, which are lines themselves
        self.assertEqual((rent["payee"], [(r["type"], r["id"]) for r in rent["recorded"]]), ("A Rental", [("Payment", "40")]))
        moved = self.q.move_to_clearing("D30", "Deposit", "31")
        self.assertEqual((moved["moved"], moved["balance_after_cents"] - moved["balance_before_cents"]), (True, 86815))
        self.assertEqual(self.intuit.records["Deposit"][1]["DepositToAccountRef"], {"value": "90", "name": "Bank Feed Clearing"})
        self.assertTrue(self.q.move_to_clearing("D32", "Payment", "40")["moved"])
        after = self.q.clearing()
        self.assertEqual(([r["id"] for r in self.line(after, "D30")["cleared_by"]], [r["id"] for r in self.line(after, "D32")["cleared_by"]]), (["31"], ["40"]))

    def test_when_amounts_repeat_each_recorded_payment_is_the_best_fit_for_one_line_only(self):
        self.connect()
        got = self.q.clearing()
        first, second = self.line(got, "T5"), self.line(got, "T6")       # two $75.00 lines two days apart, two recorded $75.00 payments
        fit = lambda line: [(r["type"], r["id"], r["days_apart"]) for r in line["recorded"] if r["best_fit"]]
        self.assertEqual((len(first["recorded"]), len(second["recorded"])), (2, 2))                     # a person still sees both
        self.assertEqual((fit(first), fit(second)), ([("BillPayment", "B3", 0)], [("Purchase", "76", 0)]))
        self.q.move_to_clearing("T6", "BillPayment", "B3")              # a person may choose the other one
        after = self.q.clearing()
        first, second = self.line(after, "T5"), self.line(after, "T6")
        self.assertEqual(sum(len(l["cleared_by"]) for l in (first, second)), 1)                         # one payment cancels one line, not both
        self.assertEqual(([r["id"] for r in first["cleared_by"]], fit(second)), (["B3"], [("Purchase", "76", 0)]))   # nearest dates first: it cancels the 20th, and the 22nd keeps its own

    def test_only_a_payment_paired_with_the_line_in_a_bank_account_can_be_moved(self):
        before = self.connect()
        for line, kind, txn in (("T1", "BillPayment", "B8"),       # same amount, but months apart
                                ("T1", "BillPayment", "B7"),       # same amount, another bank account
                                ("T2", "BillPayment", "B6"),       # another line
                                ("T9", "BillPayment", "B6"),       # no such line
                                ("T4", "Purchase", "B9"),          # the right number, the wrong kind
                                ("T1", "Invoice", "B6")):          # not a kind of payment
            with self.assertRaises(qbo.QboError, msg=(line, kind, txn)):
                self.q.move_to_clearing(line, kind, txn)
        with self.assertRaises(qbo.QboError):
            self.q.move_to_clearing("T1", "BillPayment", "B6", name="No Such Account")
        self.assertTrue(all(c[0] == "GET" for c in self.intuit.calls[before:]))      # nothing was sent to the books

    def test_a_bill_paid_by_card_moves_to_the_card_clearing_account_when_the_company_has_one(self):
        before = self.connect()
        card_account = next(a for a in self.intuit.accounts if a["Id"] == "91")
        card_account["AccountType"] = "Bank"                                         # an account of that name that is not a credit card does not count
        self.assertEqual((self.line(self.q.clearing(), "T4")["movable"], self.line(self.q.clearing(), "T1")["movable"], self.q.clearing()["card"]), (False, True, None))
        with self.assertRaises(qbo.QboError) as told:
            self.q.move_to_clearing("T4", "BillPayment", "B9")
        self.assertIn("no credit card account named Card Feed Clearing", str(told.exception))
        self.assertTrue(all(c[0] == "GET" for c in self.intuit.calls[before:]))
        card_account["AccountType"] = "Credit Card"
        self.assertTrue(self.line(self.q.clearing(), "T4")["movable"])
        held = next(r for r in self.intuit.records["BillPayment"] if r["Id"] == "B9")
        kept = json.loads(json.dumps(held))
        sent = len(self.intuit.calls)
        result = self.q.move_to_clearing("T4", "BillPayment", "B9")
        self.assertEqual((result["moved"], result["from_account"], result["to_account"]), (True, "Mastercard", "Card Feed Clearing"))
        kept.update(CreditCardPayment={"CCAccountRef": {"value": "91", "name": "Card Feed Clearing"}}, SyncToken="1")
        self.assertEqual(held, kept)                                                 # still a bill paid by card; only the card account changed
        got = self.q.clearing()
        self.assertEqual(([c["id"] for c in self.line(got, "T4")["cleared_by"]], got["card"]["name"]), (["B9"], "Card Feed Clearing"))   # the card line is cancelled
        self.intuit.transfers.append({"Id": "T0", "TxnDate": "2026-10-10", "Amount": 34.0, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}})
        lines = {l["id"]: l for l in self.q.clearing()["lines"]}
        self.assertEqual(([c["id"] for c in lines["T4"]["cleared_by"]], lines["T0"]["cleared_by"]), (["B9"], []))   # a bank line of the same amount is not cancelled from the card account
        self.assertEqual(len([c for c in self.intuit.calls[sent:] if c[0] == "POST" and c[1] != qbo.TOKEN]), 1)

    def test_a_card_charge_moves_but_a_card_refund_does_not(self):
        self.connect()
        charge = {"Id": "77", "SyncToken": "0", "TxnDate": "2026-10-11", "TotalAmt": 34.0, "PaymentType": "CreditCard", "Credit": True, "EntityRef": {"name": "Card Vendor"},
                  "AccountRef": {"value": "41", "name": "Mastercard"}, "Line": [{"Amount": 34.0, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "60", "name": "Supplies"}}}]}
        self.intuit.records["Purchase"].append(charge)
        sent = len(self.intuit.calls)
        with self.assertRaises(qbo.QboError):                                        # a refund on the card is money coming back, not a charge
            self.q.move_to_clearing("T4", "Purchase", "77")
        self.assertTrue(all(c[0] == "GET" for c in self.intuit.calls[sent:]))
        del charge["Credit"]
        self.assertTrue(self.q.move_to_clearing("T4", "Purchase", "77")["moved"])
        self.assertEqual((charge["PaymentType"], charge["AccountRef"], charge["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"]["name"], charge["TotalAmt"]),
                         ("CreditCard", {"value": "91", "name": "Card Feed Clearing"}, "Supplies", 34.0))   # still a card charge, with the category it was given

    def test_a_card_line_that_a_rule_posted_to_the_card_clearing_account_is_a_clearing_line(self):
        self.connect()
        self.intuit.records["Purchase"].append({"Id": "23", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 12.0, "PaymentType": "CreditCard", "AccountRef": {"value": "41", "name": "Mastercard"},
                                                "Line": [{"Amount": 12.0, "Description": "AMZN MKTP", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "91", "name": "Card Feed Clearing"}}}]})
        self.intuit.transfers.append({"Id": "T8", "TxnDate": "2026-11-13", "Amount": 9.0, "FromAccountRef": {"value": "41", "name": "Mastercard"}, "ToAccountRef": {"value": "91", "name": "Card Feed Clearing"}})
        self.intuit.transfers.append({"Id": "T9", "TxnDate": "2026-11-13", "Amount": 5.0, "FromAccountRef": {"value": "90", "name": "Bank Feed Clearing"}, "ToAccountRef": {"value": "91", "name": "Card Feed Clearing"}})
        lines = {l["id"]: l for l in self.q.clearing()["lines"]}
        self.assertEqual((lines["P23"]["bank_account"], lines["P23"]["amount_cents"], lines["P23"]["direction"], lines["P23"]["note"], lines["P23"]["recorded"]), ("Mastercard", 1200, "out", "AMZN MKTP", []))
        self.assertEqual((lines["T8"]["bank_account"], lines["T8"]["direction"]), ("Mastercard", "out"))
        self.assertNotIn("T9", lines)                                                # a transfer between the two clearing accounts is nobody's bank line

    def posts(self, since):
        return [c[1].split("/company/123/")[1].split("?")[0] for c in self.intuit.calls[since:] if c[0] == "POST" and c[1] != qbo.TOKEN]

    def test_the_two_bank_lines_of_one_transfer_are_paired_by_a_note_on_each_record(self):
        self.connect()
        self.intuit.add_transfer_lines()
        got = self.q.clearing()
        out, into = self.line(got, "P24"), self.line(got, "D34")
        self.assertEqual((out["cleared_by"], into["cleared_by"], out["paired_with"], [t["id"] for t in out["recorded_transfers"]], [t["id"] for t in into["recorded_transfers"]]),
                         ([], [], None, ["T3"], ["T3"]))                              # the same transfer was also recorded by hand
        self.assertEqual(self.line(got, "P21")["recorded_transfers"], [])
        purchase, deposit = self.intuit.records["Purchase"][-1], self.intuit.records["Deposit"][-1]
        kept = json.loads(json.dumps([purchase, deposit]))
        sent, balance = len(self.intuit.calls), got["balance_cents"]
        result = self.q.pair_transfer("P24", "D34")
        self.assertEqual((result["paired"], result["accounts"], self.posts(sent)), (True, ["Checking", "Savings"], ["purchase", "deposit"]))
        kept[0].update(PrivateNote="Own-account transfer, other side: Deposit 34", SyncToken="1")
        kept[1].update(PrivateNote="Bank memo | Own-account transfer, other side: Purchase 24", SyncToken="1")
        self.assertEqual([purchase, deposit], kept)                                   # a note on each; account, amount, date and bank text as they were
        got = self.q.clearing()
        out, into = self.line(got, "P24"), self.line(got, "D34")
        self.assertEqual(([(c["type"], c["id"], c["bank_account"]) for c in out["cleared_by"]], [(c["type"], c["id"], c["bank_account"]) for c in into["cleared_by"]]),
                         ([("Deposit", "34", "Savings")], [("Purchase", "24", "Checking")]))
        self.assertEqual((into["note"], got["balance_cents"]), ("ONLINE TRANSFER FROM CHK 4502", balance))   # the clearing balance was already right
        again = len(self.intuit.calls)
        self.assertTrue(self.q.pair_transfer("D34", "P24")["paired"])
        self.assertEqual(self.posts(again), [])                                       # asked twice, written once

    def test_only_two_open_lines_that_are_one_transfer_can_be_paired(self):
        before = self.connect()
        self.intuit.add_transfer_lines()
        more = lambda record_id, account, when, amount=500.0, category="90": self.intuit.records["Deposit"].append(
            {"Id": record_id, "SyncToken": "0", "TxnDate": when, "TotalAmt": amount, "DepositToAccountRef": account,
             "Line": [{"Amount": amount, "DepositLineDetail": {"AccountRef": {"value": category, "name": "a clearing account"}}}]})
        more("35", {"value": "35", "name": "Checking"}, "2026-10-06")                 # into the same account it left
        more("36", {"value": "36", "name": "Savings"}, "2026-10-12")                  # six days later
        more("37", {"value": "41", "name": "Mastercard"}, "2026-10-06")               # a payment to the card: not built
        more("38", {"value": "36", "name": "Savings"}, "2026-10-06", 499.0)           # another amount
        more("39", {"value": "36", "name": "Savings"}, "2026-10-06", category="91")   # held in the other clearing account
        self.intuit.records["Purchase"].append({"Id": "26", "SyncToken": "0", "TxnDate": "2026-10-06", "TotalAmt": 500.0, "PaymentType": "Cash", "AccountRef": {"value": "36", "name": "Savings"},
                                                "Line": [{"Amount": 500.0, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})   # the same amount, also going out
        for a, b in (("P24", "D35"), ("P24", "D36"), ("P24", "D37"), ("P24", "D38"), ("P24", "D39"), ("P24", "P26"), ("P24", "P21"), ("P24", "P24"), ("P24", "D99"), ("T1", "D34")):
            with self.assertRaises(qbo.QboError, msg=(a, b)):
                self.q.pair_transfer(a, b)
        got = self.q.clearing()
        self.assertEqual((self.line(got, "P26")["recorded_transfers"], self.line(got, "D35")["recorded_transfers"]), ([], []))   # T3 left Checking for Savings, not the other way
        self.intuit.records["Purchase"][-2]["PrivateNote"] = "Own-account transfer, other side: Deposit 77"      # record 24 half marked for another transfer
        with self.assertRaises(qbo.QboError):
            self.q.pair_transfer("P24", "D34")
        self.q.move_to_clearing("D30", "Deposit", "31")                               # D30 is now cancelled by a recorded deposit
        self.intuit.records["Purchase"].append({"Id": "25", "SyncToken": "0", "TxnDate": "2026-10-22", "TotalAmt": 868.15, "PaymentType": "Cash", "AccountRef": {"value": "36", "name": "Savings"},
                                                "Line": [{"Amount": 868.15, "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})
        sent = len(self.intuit.calls)
        with self.assertRaises(qbo.QboError):
            self.q.pair_transfer("P25", "D30")                                        # a cleared line is not paired again
        self.assertEqual((self.posts(before), self.posts(sent)), (["deposit"], []))

    def test_a_pairing_note_is_never_read_as_the_banks_text(self):
        self.connect()
        self.intuit.add_transfer_lines()
        purchase, deposit = self.intuit.records["Purchase"][-1], self.intuit.records["Deposit"][-1]
        del purchase["Line"][0]["Description"], deposit["Line"][0]["Description"]       # the bank gave no text on either line
        self.assertTrue(self.q.pair_transfer("P24", "D34")["paired"])
        got = self.q.clearing()
        self.assertEqual((self.line(got, "P24")["note"], self.line(got, "D34")["note"]), (None, "Bank memo"))

    def test_a_pairing_that_stops_half_way_clears_nothing_and_the_next_try_finishes_it(self):
        self.connect()
        self.intuit.transfers.append({"Id": "T10", "SyncToken": "0", "TxnDate": "2026-11-02", "Amount": 60.0, "PrivateNote": "XFER", "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}})
        self.intuit.transfers.append({"Id": "T11", "SyncToken": "0", "TxnDate": "2026-11-03", "Amount": 60.0, "FromAccountRef": {"value": "90", "name": "Bank Feed Clearing"}, "ToAccountRef": {"value": "36", "name": "Savings"}})
        seen = []

        def second_change_refused(method, url, headers, body=None):
            seen.append(method == "POST" and url != qbo.TOKEN)
            self.intuit.refuse_change = sum(seen) == 2
            return self.intuit(method, url, headers, body)
        self.q.transport = second_change_refused
        with self.assertRaises(qbo.QboError):
            self.q.pair_transfer("T10", "T11")
        self.q.transport, self.intuit.refuse_change = self.intuit, False
        got = self.q.clearing()
        first, second = self.line(got, "T10"), self.line(got, "T11")
        self.assertEqual((first["cleared_by"], second["cleared_by"], first["note"], first["paired_with"]), ([], [], "XFER", None))   # one note alone pairs nothing, and is not bank text
        sent = len(self.intuit.calls)
        self.assertTrue(self.q.pair_transfer("T10", "T11")["paired"])
        self.assertEqual((self.posts(sent), self.intuit.transfers[-2]["PrivateNote"], self.intuit.transfers[-1]["PrivateNote"]),
                         (["transfer"], "XFER | Own-account transfer, other side: Transfer T11", "Own-account transfer, other side: Transfer T10"))
        self.intuit.transfers[-1]["Amount"] = 61.0                                    # the two no longer agree: the notes alone do not clear them
        self.assertEqual(self.line(self.q.clearing(), "T10")["cleared_by"], [])

    def test_a_refused_or_unconfirmed_change_is_reported_as_such(self):
        self.connect()
        self.intuit.refuse_change = True
        with self.assertRaises(qbo.QboError) as refused:
            self.q.move_to_clearing("T1", "BillPayment", "B6")
        self.assertIn("You and another user were working on the same thing.", str(refused.exception))
        self.assertNotIn("ACCESS-", str(refused.exception))
        self.assertEqual(self.intuit.records["BillPayment"][0]["CheckPayment"]["BankAccountRef"]["value"], "35")
        self.intuit.refuse_change, self.intuit.ignore_change = False, True          # QuickBooks says yes but the record did not change
        self.assertFalse(self.q.move_to_clearing("T1", "BillPayment", "B6")["moved"])

    def test_without_keys_there_is_no_connection_object(self):
        self.assertIsNone(qbo.from_environment({}))
        made = qbo.from_environment({"INTUIT_CLIENT_ID": "a", "INTUIT_CLIENT_SECRET": "b", "RENDER_EXTERNAL_URL": "https://x.onrender.com/"})
        self.assertEqual(made.redirect_uri, "https://x.onrender.com/qbo/callback")


if __name__ == "__main__":
    unittest.main()
