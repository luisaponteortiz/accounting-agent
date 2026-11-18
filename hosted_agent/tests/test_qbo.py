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
        statement = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["query"][0]
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

    def test_without_keys_there_is_no_connection_object(self):
        self.assertIsNone(qbo.from_environment({}))
        made = qbo.from_environment({"INTUIT_CLIENT_ID": "a", "INTUIT_CLIENT_SECRET": "b", "RENDER_EXTERNAL_URL": "https://x.onrender.com/"})
        self.assertEqual(made.redirect_uri, "https://x.onrender.com/qbo/callback")


if __name__ == "__main__":
    unittest.main()
