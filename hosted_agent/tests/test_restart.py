"""Review tests for what the service keeps across a restart: its records and the QuickBooks sandbox connection. No network."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hosted_agent import demo_books, qbo
from hosted_agent.brain import BaselineBrain
from hosted_agent.ledger import FakeLedger
from hosted_agent.store import Store
from hosted_agent.tests.test_qbo import Intuit
from hosted_agent.web import SANDBOX, ReviewServer

PEOPLE = {"owner-token": dict(name="Owner (test)", role="owner")}
REALM = "123"
ROOT = Path(__file__).resolve().parents[2]


class RestartCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "agent.db")
        self.intuit, self.time = Intuit(), [1000.0]

    def start(self):
        """The service as it comes up: the store on the same file, a new connection object, a new server."""
        store = Store(self.path)
        q = qbo.Qbo("the-id", "the-secret", "https://agent.example/qbo/callback", transport=self.intuit, clock=lambda: self.time[0])
        server = ReviewServer(("127.0.0.1", 0), store, FakeLedger(demo_books.companies()), BaselineBrain(), PEOPLE, q)
        self.addCleanup(store.close)
        self.addCleanup(server.server_close)
        return store, q, server

    def connect(self, q, server):
        state = q.authorize_url("Owner (test)").split("state=")[1].split("&")[0]
        server.adopt_sandbox(q.finish(state, "code", REALM))

    def test_the_connection_and_the_client_come_back_without_a_new_sign_in(self):
        store, q, server = self.start()
        self.assertIsNone(q.connection)                                   # nothing kept yet
        self.connect(q, server)
        sent = len(self.intuit.calls)
        again, q2, server2 = self.start()
        self.assertEqual(self.intuit.calls[sent:], [])                    # coming back up sends nothing to Intuit
        self.assertEqual((q2.connection["realm_id"], q2.connection["connected_by"], q2.connection["refresh_token"]), (REALM, "Owner (test)", "REFRESH-1"))
        self.assertEqual([c["client_id"] for c in again.clients() if c["realm_id"] == REALM], ["qbo-" + REALM])    # the same client, once
        self.assertTrue(server2.ledger.pending_feed(REALM))               # and its books answer through the kept connection
        self.assertEqual(self.intuit.issued, 1)                           # with the tokens it already had
        events = [r["event"] for r in again.rows("SELECT event FROM audit ORDER BY id")]
        self.assertIn("qbo_sandbox_restored", events)

    def test_a_refreshed_token_is_the_one_kept(self):
        store, q, server = self.start()
        self.connect(q, server)
        self.time[0] += 7200                                              # the access token has run out
        q.query("select * from Account")
        self.assertEqual((self.intuit.issued, store.connection(SANDBOX)["refresh_token"], store.connection(SANDBOX)["access_token"]), (2, "REFRESH-2", "ACCESS-2"))
        again, q2, server2 = self.start()
        self.assertEqual(q2.connection["refresh_token"], "REFRESH-2")     # a restart never goes back to a token Intuit has replaced
        q2._post("purchase", dict(next(r for r in self.intuit.records["Purchase"] if r["Id"] == "20")))
        self.assertEqual(self.intuit.issued, 2)                           # still valid: no further refresh

    def test_a_kept_connection_that_is_unusable_never_stops_the_service(self):
        store, q, server = self.start()
        self.connect(q, server)
        kept = store.connection(SANDBOX)
        for broken in (dict(kept, refresh_token=""), {k: v for k, v in kept.items() if k != "realm_id"}, ["not", "a", "connection"]):
            store.save_connection(SANDBOX, broken)
            again, q2, server2 = self.start()
            self.assertIsNone(q2.connection)
            self.assertEqual(again.rows("SELECT event FROM audit ORDER BY id DESC LIMIT 1")[0]["event"], "qbo_sandbox_not_restored")
            with self.assertRaises(qbo.QboError):
                q2.query("select * from Account")
        self.connect(q2, server2)                                         # signing in again from the page replaces it
        self.assertEqual(again.connection(SANDBOX)["realm_id"], REALM)

    def test_the_tokens_stay_out_of_the_audit_chain_and_out_of_what_the_page_reads(self):
        store, q, server = self.start()
        self.connect(q, server)
        self.time[0] += 7200
        told = json.dumps(q.summary())
        store, q, server = self.start()                                   # and once more after a restart
        told += json.dumps(q.summary()) + json.dumps(store.rows("SELECT * FROM audit")) + json.dumps(store.clients()) + json.dumps(store.rows("SELECT * FROM runs"))
        self.assertIn("qbo_sandbox_restored", told)
        for secret in ("ACCESS-", "REFRESH-", "the-secret"):
            self.assertNotIn(secret, told)
        self.assertEqual(set(store.connection(SANDBOX)), {"realm_id", "connected_by", "connected_at", "access_token", "refresh_token", "expires_at"})

    def test_without_quickbooks_keys_nothing_is_kept_or_restored(self):
        store = Store(self.path)
        self.addCleanup(store.close)
        store.save_connection(SANDBOX, dict(realm_id=REALM))
        server = ReviewServer(("127.0.0.1", 0), store, FakeLedger(demo_books.companies()), BaselineBrain(), PEOPLE)
        self.addCleanup(server.server_close)
        self.assertIsNone(server.qbo)
        self.assertEqual(store.rows("SELECT event FROM audit"), [])

    def test_the_service_keeps_its_records_in_the_file_named_by_AGENT_DB(self):
        path = os.path.join(self.folder.name, "kept", "agent.db")         # the folder does not exist yet
        env = dict(os.environ, AGENT_DB=path)
        env.pop("ANTHROPIC_API_KEY", None)
        runs = [subprocess.run([sys.executable, "-m", "hosted_agent", "run"], cwd=ROOT, env=env, capture_output=True, text=True) for _ in range(2)]
        self.assertEqual([r.returncode for r in runs], [0, 0], runs[-1].stderr)
        first, second = ([json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")] for r in runs)
        self.assertEqual(([r["new"] for r in first], [r["new"] for r in second], [r["read"] for r in second]), ([14, 5], [0, 0], [14, 5]))   # the second start knows what the first prepared
        self.assertIn("kept in a file on disk", runs[0].stdout)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)      # readable by the service's own user only
        memory = subprocess.run([sys.executable, "-m", "hosted_agent", "run"], cwd=ROOT, env={k: v for k, v in env.items() if k != "AGENT_DB"}, capture_output=True, text=True)
        self.assertIn("in memory only", memory.stdout)


if __name__ == "__main__":
    unittest.main()
