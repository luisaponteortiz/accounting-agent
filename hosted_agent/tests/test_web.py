"""Review tests for the page's API: who may do what, over real HTTP on loopback."""
import json
import threading
import unittest
import urllib.error
import urllib.request

from hosted_agent import demo_books
from hosted_agent.brain import BaselineBrain
from hosted_agent.ledger import FakeLedger
from hosted_agent.runner import run_client
from hosted_agent.store import Store
from hosted_agent.web import ReviewServer

PEOPLE = {"owner-token": dict(name="Owner (test)", role="owner"), "reviewer-token": dict(name="Reviewer (test)", role="reviewer")}


class WebCase(unittest.TestCase):
    def setUp(self):
        self.store, self.ledger = Store(), FakeLedger(demo_books.companies())
        self.store.add_client("cafe", "Harbor Light Cafe LLC (fictional)", "9001", mode="post_approved", spot_check_percent=0)
        self.store.add_client("outfitters", "Granite Ridge Outfitters Inc (fictional)", "9002")
        run_client(self.store, self.ledger, BaselineBrain(), "cafe")
        self.server = ReviewServer(("127.0.0.1", 0), self.store, self.ledger, BaselineBrain(), PEOPLE)
        threading.Thread(target=self.server.serve_forever, kwargs=dict(poll_interval=0.05), daemon=True).start()
        self.base = "http://127.0.0.1:%s" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()

    def call(self, path, body=None, token=None, page_header=True):
        request = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None)
        if token:
            request.add_header("Authorization", "Bearer " + token)
        if body is not None and page_header:
            request.add_header("X-Requested-With", "accounting-agent")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as error:
            raw = error.read()
            try:
                return error.code, json.loads(raw)
            except ValueError:
                return error.code, {"text": raw.decode()}

    def first(self, key):
        return [p for p in self.store.proposals("cafe", "waiting") if p["item_key"] == key][0]["id"]

    def test_nothing_is_readable_without_signing_in(self):
        for path in ("/", "/api/roster", "/api/state?client=cafe"):
            self.assertEqual(self.call(path)[0], 401)
        self.assertEqual(self.call("/api/roster", token="wrong")[0], 401)
        self.assertEqual(self.call("/healthz")[0], 200)

    def test_a_reviewer_can_decide_but_cannot_grant_or_change_mode(self):
        status, body = self.call("/api/decide", dict(ids=[self.first("F001")], verdict="approve"), "reviewer-token")
        self.assertEqual((status, list(body["results"].values())), (200, ["posted"]))
        grant = dict(client="cafe", item_class="recurring_vendor", class_key="x", max_amount_cents=1000, override_reason="x")
        self.assertEqual(self.call("/api/standing/grant", grant, "reviewer-token")[0], 403)
        self.assertEqual(self.call("/api/mode", dict(client="cafe", mode="post_standing"), "reviewer-token")[0], 403)
        self.assertEqual(self.call("/api/run", dict(client="cafe"), "reviewer-token")[0], 403)
        self.assertEqual(self.store.client("cafe")["mode"], "post_approved")

    def test_a_write_must_come_from_the_page(self):
        status, _ = self.call("/api/decide", dict(ids=[self.first("F001")], verdict="approve"), "reviewer-token", page_header=False)
        self.assertEqual((status, self.ledger.writes), (403, 0))

    def test_state_is_for_one_client(self):
        status, body = self.call("/api/state?client=outfitters", token="owner-token")
        self.assertEqual((status, body["waiting"]), (200, []))
        self.assertEqual(self.call("/api/state?client=nobody", token="owner-token")[0], 404)

    def test_quickbooks_routes_are_owner_only_and_safe_without_keys(self):
        self.assertEqual(self.call("/api/qbo", token="owner-token"), (200, {"configured": False}))
        self.assertEqual(self.call("/qbo/connect", token="owner-token")[0], 404)       # no keys on this server
        self.assertEqual(self.call("/qbo/connect", token="reviewer-token")[0], 403)
        self.assertEqual(self.call("/qbo/connect")[0], 401)
        self.assertEqual(self.call("/api/qbo/probe", token="owner-token")[0], 404)     # no keys on this server
        self.assertEqual(self.call("/api/qbo/probe", token="reviewer-token")[0], 403)
        self.assertEqual(self.call("/api/qbo/probe")[0], 401)
        self.assertEqual(self.call("/qbo/callback?state=x&code=y&realmId=1")[0], 404)

    def test_a_refusal_is_reported_per_item(self):
        closed = self.first("F011")
        _, body = self.call("/api/decide", dict(ids=[closed], verdict="approve"), "owner-token")
        self.assertIn("refused", body["results"][str(closed)])


if __name__ == "__main__":
    unittest.main()
