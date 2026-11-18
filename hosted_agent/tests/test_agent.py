"""Review tests for the hosted agent. Each one states a control and tries to break it."""
import unittest

from hosted_agent import demo_books
from hosted_agent.brain import BaselineBrain
from hosted_agent.ledger import FakeLedger, LedgerError
from hosted_agent.review import Refused, decide, end_standing, grant_standing, record, roster, set_mode, state
from hosted_agent.runner import observe, run_client
from hosted_agent.store import Store

OWNER = dict(name="Owner (test)", role="owner")
REVIEWER = dict(name="Reviewer (test)", role="reviewer")
POWER = ("recurring_vendor", "City Power and Light | Utilities")


class Case(unittest.TestCase):
    def setUp(self):
        self.ledger = FakeLedger(demo_books.companies())
        self.store = Store()
        self.brain = BaselineBrain()
        self.store.add_client("cafe", "Harbor Light Cafe LLC (fictional)", "9001", spot_check_percent=0)
        self.store.add_client("outfitters", "Granite Ridge Outfitters Inc (fictional)", "9002", spot_check_percent=0)

    def tearDown(self):
        self.store.close()

    def run_cafe(self):
        return run_client(self.store, self.ledger, self.brain, "cafe")

    def waiting(self, client="cafe"):
        return {p["item_key"]: p for p in self.store.proposals(client, "waiting")}

    def status(self, feed_id, realm="9001"):
        return self.ledger.read_back(realm, feed_id)["status"]


class Classification(Case):
    def test_each_kind_of_line_is_told_apart(self):
        self.run_cafe()
        got = {k: p["item_class"] for k, p in self.waiting().items()}
        self.assertEqual(got, {
            "F001": "recurring_vendor", "F002": "recurring_vendor", "F003": "recurring_vendor",
            "F004": "bill_payment_match", "F005": "own_transfer", "F006": "own_transfer", "F007": "bank_fee",
            "F008": "unknown", "F009": "vendor_mixed_accounts", "F010": "person_payment",
            "F011": "recurring_vendor", "F012": "invoice_payment_match", "F013": "unknown", "F014": "recurring_vendor"})

    def test_proposals_carry_their_evidence(self):
        self.run_cafe()
        p = self.waiting()["F001"]
        self.assertEqual(p["action"]["account"], "Utilities")
        self.assertEqual(p["evidence"]["times_seen"], 3)
        self.assertEqual(self.waiting()["F004"]["action"], dict(kind="match", txn_type="bill", txn_id="B100"))


class PrepareOnly(Case):
    def test_prepare_only_writes_nothing_to_the_books(self):
        result = self.run_cafe()
        self.assertEqual(self.ledger.writes, 0)
        self.assertEqual(result["auto_posted"], 0)
        self.assertEqual(result["new"], 14)
        decide(self.store, self.ledger, REVIEWER, self.waiting()["F001"]["id"], "approve")
        self.assertEqual(self.ledger.writes, 0)
        self.assertEqual(self.store.proposal(1)["status"], "approved_not_posted")

    def test_a_second_run_proposes_nothing_twice(self):
        self.run_cafe()
        again = self.run_cafe()
        self.assertEqual(again["new"], 0)
        self.assertEqual(len(self.store.proposals("cafe")), 14)


class CompanyCheck(Case):
    def test_wrong_company_blocks_the_run_before_anything_is_read(self):
        self.store.run("UPDATE clients SET name='Some Other Company' WHERE client_id='cafe'")
        result = self.run_cafe()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.store.proposals("cafe"), [])

    def test_company_is_checked_again_before_a_posting(self):
        set_mode(self.store, OWNER, "cafe", "post_approved")
        self.run_cafe()
        self.ledger.companies["9001"]["name"] = "Renamed Underneath Us"
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, REVIEWER, self.waiting()["F001"]["id"], "approve")
        self.assertEqual(self.ledger.writes, 0)
        self.assertEqual(self.waiting()["F001"]["status"], "waiting")


class ApprovedPosting(Case):
    def setUp(self):
        super().setUp()
        set_mode(self.store, OWNER, "cafe", "post_approved")
        self.run_cafe()

    def test_without_standing_approval_nothing_posts_unattended(self):
        self.assertEqual(self.ledger.writes, 0)
        self.assertEqual(len(self.waiting()), 14)

    def test_approve_posts_the_proposal_and_reads_it_back(self):
        self.assertEqual(decide(self.store, self.ledger, REVIEWER, self.waiting()["F001"]["id"], "approve"), "posted")
        back = self.ledger.read_back("9001", "F001")
        self.assertEqual((back["status"], back["posted"]["account"]), ("categorized", "Utilities"))
        posting = self.store.one("SELECT * FROM postings")
        self.assertEqual((posting["verified"], posting["how"], posting["actor"]), (1, "approved", "Reviewer (test)"))

    def test_change_posts_the_reviewers_treatment(self):
        fix = dict(kind="categorize", account="Repairs and Maintenance", vendor="OmniMart", memo="")
        decide(self.store, self.ledger, REVIEWER, self.waiting()["F009"]["id"], "change", fix)
        self.assertEqual(self.ledger.read_back("9001", "F009")["posted"]["account"], "Repairs and Maintenance")

    def test_reject_posts_nothing_and_needs_a_reason(self):
        pid = self.waiting()["F010"]["id"]
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, REVIEWER, pid, "reject")
        decide(self.store, self.ledger, REVIEWER, pid, "reject", note="ask the client what this was for")
        self.assertEqual((self.ledger.writes, self.status("F010")), (0, "pending"))

    def test_an_item_with_no_proposal_cannot_be_approved(self):
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, REVIEWER, self.waiting()["F008"]["id"], "approve")

    def test_closed_period_and_opening_balance_equity_never_post(self):
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, REVIEWER, self.waiting()["F011"]["id"], "approve")
        obe = dict(kind="categorize", account="Opening Balance Equity", vendor=None, memo="")
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, OWNER, self.waiting()["F013"]["id"], "change", obe)
        self.assertEqual(self.ledger.writes, 0)
        self.assertEqual(self.store.rows("SELECT * FROM decisions"), [])

    def test_the_agent_cannot_decide_or_grant(self):
        agent = dict(name="agent", role="owner")
        with self.assertRaises(Refused):
            decide(self.store, self.ledger, agent, self.waiting()["F001"]["id"], "approve")
        with self.assertRaises(Refused):
            grant_standing(self.store, agent, "cafe", *POWER, 50000, "because")
        with self.assertRaises(Refused):
            grant_standing(self.store, REVIEWER, "cafe", *POWER, 50000, "because")

    def test_a_failed_read_back_is_not_called_posted(self):
        class Lying(FakeLedger):
            def read_back(self, realm_id, feed_id):
                back = super().read_back(realm_id, feed_id)
                if back["posted"]:
                    back["posted"]["account"] = "Rent"
                return back
        liar = Lying(demo_books.companies())
        self.assertEqual(decide(self.store, liar, REVIEWER, self.waiting()["F001"]["id"], "approve"), "failed")
        p = self.waiting()["F001"]
        self.assertEqual((p["status"], p["queue"]), ("waiting", "exception"))
        self.assertIn("read-back", p["reasons"][0])


class StandingApproval(Case):
    def earn(self, n=5):
        """A reviewer agrees with the agent n times on City Power, in the books of earlier months."""
        company = self.ledger.companies["9001"]
        for i in range(n):
            company["feed"].append(dict(id="E%d" % i, date=demo_books._d(5 + i), amount_cents=-40000 - i,
                                        description="CITY POWER & LIGHT ACH 51%d" % i, bank_account="Operating Checking", status="pending"))
        set_mode(self.store, OWNER, "cafe", "post_approved")
        self.run_cafe()
        for i in range(n):
            decide(self.store, self.ledger, REVIEWER, self.waiting()["E%d" % i]["id"], "approve")

    def test_a_grant_needs_a_record_or_a_stated_reason(self):
        with self.assertRaises(Refused):
            grant_standing(self.store, OWNER, "cafe", *POWER, 50000)
        self.earn(4)
        with self.assertRaises(Refused):
            grant_standing(self.store, OWNER, "cafe", *POWER, 50000)
        self.assertTrue(grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "utility bill, same every month"))

    def test_five_agreements_make_a_class_eligible_and_grantable(self):
        self.earn(5)
        found = [c for c in record(self.store, "cafe") if c["class_key"] == POWER[1]][0]
        self.assertEqual((found["streak"], found["eligible"]), (5, True))
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000)
        self.assertFalse([c for c in record(self.store, "cafe") if c["class_key"] == POWER[1]][0]["eligible"])

    def test_classes_that_need_judgment_can_never_be_granted(self):
        for item_class in ("unknown", "person_payment", "vendor_mixed_accounts", "possible_duplicate"):
            with self.assertRaises(Refused):
                grant_standing(self.store, OWNER, "cafe", item_class, "x", 50000, "please")

    def test_only_the_granted_class_posts_unattended(self):
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        set_mode(self.store, OWNER, "cafe", "post_standing")
        result = self.run_cafe()
        self.assertEqual(result["auto_posted"], 1)                 # F001 only
        self.assertEqual(self.status("F001"), "categorized")
        self.assertEqual(self.status("F002"), "pending")           # other recurring vendor: not granted
        self.assertEqual(self.status("F011"), "pending")           # same vendor, closed period
        self.assertIn("closed period", self.waiting()["F011"]["reasons"][0])
        posting = self.store.one("SELECT * FROM postings")
        self.assertEqual((posting["how"], posting["actor"], posting["verified"]), ("standing", "agent", 1))

    def test_amount_limits_hold(self):
        grant_standing(self.store, OWNER, "cafe", *POWER, 30000, "test")                      # below F001's 419.80
        grant_standing(self.store, OWNER, "cafe", "recurring_vendor", "Harbor Properties | Rent", 400000, "test")
        set_mode(self.store, OWNER, "cafe", "post_standing")
        self.run_cafe()
        self.assertEqual(self.ledger.writes, 0)
        self.assertIn("standing approval's amount limit", self.waiting()["F001"]["reasons"][0])
        self.assertIn("client's unattended limit", self.waiting()["F003"]["reasons"][0])     # rent is over the client cap

    def test_a_standing_approval_needs_post_standing_mode(self):
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        set_mode(self.store, OWNER, "cafe", "post_approved")
        self.run_cafe()
        self.assertEqual(self.ledger.writes, 0)

    def test_an_approval_for_one_client_does_nothing_for_another(self):
        water = ("recurring_vendor", "Granite Valley Water | Utilities")       # a class that exists at the other client
        grant_standing(self.store, OWNER, "cafe", *water, 50000, "test")
        for client in ("cafe", "outfitters"):
            set_mode(self.store, OWNER, client, "post_standing")
        result = run_client(self.store, self.ledger, self.brain, "outfitters")
        self.assertEqual(self.waiting("outfitters")["G001"]["item_class"], "recurring_vendor")
        self.assertEqual((result["auto_posted"], self.status("G001", "9002"), self.ledger.writes), (0, "pending", 0))
        grant_standing(self.store, OWNER, "outfitters", *water, 50000, "test")
        self.assertEqual(run_client(self.store, self.ledger, self.brain, "outfitters")["auto_posted"], 1)

    def test_the_posting_step_itself_refuses_hard_stops(self):
        from hosted_agent.runner import Blocked, execute
        set_mode(self.store, OWNER, "cafe", "post_standing")
        self.run_cafe()
        closed = self.waiting()["F011"]
        with self.assertRaises(Blocked):
            execute(self.store, self.ledger, closed["id"], closed["action"], "standing", "agent")
        obe = dict(kind="categorize", account="Opening Balance Equity", vendor=None, memo="")
        with self.assertRaises(Blocked):
            execute(self.store, self.ledger, self.waiting()["F001"]["id"], obe, "approved", "Owner (test)")
        self.assertEqual(self.ledger.writes, 0)

    def test_spot_checks_route_to_a_person_and_disagreement_ends_the_approval(self):
        self.store.run("UPDATE clients SET spot_check_percent=100 WHERE client_id='cafe'")
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        set_mode(self.store, OWNER, "cafe", "post_standing")
        self.run_cafe()
        p = self.waiting()["F001"]
        self.assertEqual((p["queue"], self.ledger.writes), ("spot_check", 0))
        fix = dict(kind="categorize", account="Rent", vendor="City Power and Light", memo="")
        decide(self.store, self.ledger, REVIEWER, p["id"], "change", fix)
        self.assertEqual(self.store.active_standing("cafe"), [])
        self.assertEqual(self.store.one("SELECT ended_by FROM standing_approvals")["ended_by"], "system")

    def test_waiting_items_follow_a_later_grant_and_post_on_the_next_run(self):
        self.run_cafe()                                                 # prepare-only: everything waits
        self.assertEqual(self.waiting()["F001"]["queue"], "prepared")
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        set_mode(self.store, OWNER, "cafe", "post_standing", self.ledger)
        self.assertEqual(self.ledger.writes, 0)                         # a person's click never posts by itself
        self.assertIn("next run", self.waiting()["F001"]["reasons"][0])
        self.assertIn("no standing approval", self.waiting()["F002"]["reasons"][0])
        result = self.run_cafe()
        self.assertEqual((result["auto_posted"], self.status("F001"), self.status("F002")), (1, "categorized", "pending"))

    def test_a_failed_posting_is_never_retried_unattended(self):
        class Lying(FakeLedger):
            def read_back(self, realm_id, feed_id):
                back = super().read_back(realm_id, feed_id)
                if back["posted"]:
                    back["posted"]["account"] = "Rent"
                return back
        liar = Lying(demo_books.companies())
        grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        set_mode(self.store, OWNER, "cafe", "post_standing")
        first = run_client(self.store, liar, self.brain, "cafe")
        self.assertEqual((first["auto_posted"], first["failed"], liar.writes), (0, 1, 1))
        again = run_client(self.store, liar, self.brain, "cafe")
        self.assertEqual((again["auto_posted"], liar.writes), (0, 1))
        self.assertEqual(self.waiting()["F001"]["queue"], "exception")

    def test_an_owner_can_end_an_approval(self):
        sid = grant_standing(self.store, OWNER, "cafe", *POWER, 50000, "test")
        with self.assertRaises(Refused):
            end_standing(self.store, REVIEWER, sid, "no")
        end_standing(self.store, OWNER, sid, "vendor changed its billing")
        self.assertEqual(self.store.active_standing("cafe"), [])


class Shadow(Case):
    def test_work_done_directly_in_the_books_is_compared_with_the_proposal(self):
        self.run_cafe()
        self.ledger.categorize("9001", "F001", "Utilities", "City Power and Light", "")      # as proposed
        self.ledger.categorize("9001", "F002", "Office Supplies", "Ledgerly Software", "")   # not as proposed
        self.assertEqual(observe(self.store, self.ledger, "cafe"), 2)
        got = {p["item_key"]: p["status"] for p in self.store.proposals("cafe")}
        self.assertEqual((got["F001"], got["F002"]), ("observed_same", "observed_different"))
        by_key = {c["class_key"]: c for c in record(self.store, "cafe")}
        self.assertEqual(by_key[POWER[1]]["agreed"], 1)
        self.assertEqual(by_key["Ledgerly Software | Software Subscriptions"]["streak"], 0)


class Separation(Case):
    def test_one_clients_page_never_shows_another_clients_items(self):
        self.run_cafe()
        run_client(self.store, self.ledger, self.brain, "outfitters")
        cafe, other = state(self.store, "cafe"), state(self.store, "outfitters")
        self.assertTrue(all(p["item_key"].startswith("F") for p in cafe["waiting"]))
        self.assertTrue(all(p["item_key"].startswith("G") for p in other["waiting"]))
        self.assertEqual(len(other["waiting"]), 5)

    def test_the_roster_holds_names_and_counts_only(self):
        self.run_cafe()
        text = repr(roster(self.store))
        self.assertIn("Harbor Light Cafe", text)
        for leak in ("CITY POWER", "ZELLE", "amount_cents", "41980"):
            self.assertNotIn(leak, text)

    def test_the_ledger_has_no_current_company(self):
        with self.assertRaises(TypeError):
            self.ledger.pending_feed()
        with self.assertRaises(LedgerError):
            self.ledger.categorize("9002", "F001", "Utilities", None, "")   # the cafe's line, the other realm


class Audit(Case):
    def test_the_audit_chain_detects_a_changed_row(self):
        self.run_cafe()
        self.assertTrue(self.store.verify_audit())
        self.store.run("UPDATE audit SET payload='{}' WHERE id=2")
        self.assertFalse(self.store.verify_audit())


if __name__ == "__main__":
    unittest.main()
