"""Review tests for the QuickBooks sandbox connection, with a stand-in for Intuit. No network."""
import json
import unittest
import urllib.parse

from hosted_agent import qbo


class Intuit:
    def __init__(self):
        self.calls, self.token_status, self.issued = [], 200, 0

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        if url == qbo.TOKEN:
            self.issued += 1
            return self.token_status, json.dumps(dict(access_token="ACCESS-%d" % self.issued, refresh_token="REFRESH-%d" % self.issued, expires_in=3600)).encode()
        if "/companyinfo/" in url:
            return 200, json.dumps({"CompanyInfo": {"CompanyName": "Sandbox Company_US_1"}}).encode()
        asked = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        if "query" not in asked:
            return 404, b"<html>Not Found</html>"
        statement = asked["query"][0]
        if statement.split()[-1] in qbo.FEED_NAMES:
            return 400, json.dumps({"Fault": {"Error": [{"Message": "Error parsing query", "Detail": "QueryParserError: Invalid entity", "code": "4000"}], "type": "ValidationFault"}}).encode()
        if statement.startswith("select * from Account where Name"):
            hit = [{"Id": "90", "Name": "Bank Feed Clearing", "AccountType": "Bank", "CurrentBalance": 138.47}] if "Bank Feed Clearing" in statement else []
            return 200, json.dumps({"QueryResponse": {"Account": hit}}).encode()
        if statement.startswith("select * from Transfer"):
            return 200, json.dumps({"QueryResponse": {"Transfer": [
                {"Id": "T1", "TxnDate": "2026-10-21", "Amount": 114.09, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}, "PrivateNote": "PG E"},
                {"Id": "T2", "TxnDate": "2026-10-04", "Amount": 24.38, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "90", "name": "Bank Feed Clearing"}},
                {"Id": "T3", "TxnDate": "2026-10-05", "Amount": 500.0, "FromAccountRef": {"value": "35", "name": "Checking"}, "ToAccountRef": {"value": "36", "name": "Savings"}}]}}).encode()
        if statement.startswith("select * from BillPayment"):
            return 200, json.dumps({"QueryResponse": {"BillPayment": [
                {"Id": "B6", "DocNumber": "6", "TxnDate": "2026-10-21", "TotalAmt": 114.09, "VendorRef": {"name": "PG&E"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}}},
                {"Id": "B7", "DocNumber": "7", "TxnDate": "2026-10-21", "TotalAmt": 114.09, "VendorRef": {"name": "Other Utility"}, "CheckPayment": {"BankAccountRef": {"value": "36", "name": "Savings"}}},
                {"Id": "B8", "DocNumber": "8", "TxnDate": "2026-08-01", "TotalAmt": 114.09, "VendorRef": {"name": "PG&E"}, "CheckPayment": {"BankAccountRef": {"value": "35", "name": "Checking"}}}]}}).encode()
        if statement.startswith("select * from") and "Purchase" not in statement:
            return 200, json.dumps({"QueryResponse": {}}).encode()
        if "count(*)" in statement:
            return 200, json.dumps({"QueryResponse": {"totalCount": 7}}).encode()
        return 200, json.dumps({"QueryResponse": {"Purchase": [{"TxnDate": "2026-11-01", "TotalAmt": 19.99, "EntityRef": {"name": "Sample Vendor"},
                                "AccountRef": {"name": "Checking"}, "Line": [{"AccountBasedExpenseLineDetail": {"AccountRef": {"name": "Supplies"}}}]}]}}).encode()


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

    def test_the_clearing_read_pairs_a_line_only_with_the_same_money_in_the_same_bank_account(self):
        self.q.finish(self.start()["state"][0], "code", "123")
        before = len(self.intuit.calls)
        got = self.q.clearing()
        self.assertEqual((got["found"], got["type"], got["balance_cents"], len(got["lines"])), (True, "Bank", 13847, 2))   # the Checking to Savings transfer is not a clearing line
        paid, plain = got["lines"]
        self.assertEqual((paid["amount_cents"], paid["direction"], paid["bank_account"], paid["note"]), (11409, "out", "Checking", "PG E"))
        self.assertEqual([(r["type"], r["number"], r["days_apart"]) for r in paid["recorded"]], [("BillPayment", "6", 0)])   # not the Savings one, not the August one
        self.assertEqual((plain["note"], plain["recorded"]), (None, []))
        self.assertTrue(all(c[0] == "GET" for c in self.intuit.calls[before:]))
        self.assertFalse(self.q.clearing("No Such Account")["found"])

    def test_without_keys_there_is_no_connection_object(self):
        self.assertIsNone(qbo.from_environment({}))
        made = qbo.from_environment({"INTUIT_CLIENT_ID": "a", "INTUIT_CLIENT_SECRET": "b", "RENDER_EXTERNAL_URL": "https://x.onrender.com/"})
        self.assertEqual(made.redirect_uri, "https://x.onrender.com/qbo/callback")


if __name__ == "__main__":
    unittest.main()
