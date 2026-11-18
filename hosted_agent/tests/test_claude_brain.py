"""Review tests for the model-backed brain, with a stand-in for the API client. No network, no key."""
import json
import unittest
from types import SimpleNamespace

from hosted_agent import demo_books
from hosted_agent.claude_brain import ClaudeBrain, from_environment
from hosted_agent.brain import BaselineBrain
from hosted_agent.ledger import FakeLedger
from hosted_agent.review import Refused, grant_standing, set_mode
from hosted_agent.runner import run_client
from hosted_agent.store import Store

OWNER = dict(name="Owner (test)", role="owner")


class StandIn:
    """Answers like the Messages API. `answer` is a dict, a function of the request, or an exception."""

    def __init__(self, answer):
        self.answer, self.requests = answer, []
        self.messages = self

    def with_options(self, **options):
        return self

    def create(self, **request):
        self.requests.append(request)
        answer = self.answer(request) if callable(self.answer) else self.answer
        if isinstance(answer, Exception):
            raise answer
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=json.dumps(answer))])


def says(decision="categorize", account="Office Supplies", payee="BrightSign Studio", confidence=0.95, question=""):
    return dict(decision=decision, account=account, payee=payee, confidence=confidence,
                reasoning="A sign maker; the books put small shop purchases in this account.", question_for_reviewer=question)


class Case(unittest.TestCase):
    def setUp(self):
        self.ledger, self.store = FakeLedger(demo_books.companies()), Store()
        self.store.add_client("cafe", "Harbor Light Cafe LLC (fictional)", "9001", mode="post_standing", spot_check_percent=0)
        self.store.add_client("outfitters", "Granite Ridge Outfitters Inc (fictional)", "9002")

    def tearDown(self):
        self.store.close()

    def run_with(self, answer, client="cafe"):
        self.api = StandIn(answer)
        self.brain = ClaudeBrain(self.api)
        result = run_client(self.store, self.ledger, self.brain, client)
        return result, {p["item_key"]: p for p in self.store.proposals(client)}

    def test_the_model_is_asked_only_about_lines_the_books_cannot_settle(self):
        _, got = self.run_with(says())
        self.assertEqual(len(self.api.requests), 3)                      # F008, F009, F013 of 14 lines
        asked = sorted(json.loads(r["messages"][0]["content"])["bank_line"]["description"] for r in self.api.requests)
        self.assertEqual(asked, ["BRIGHTSIGN STUDIO", "MOBILE DEPOSIT", "OMNIMART ONLINE 90417"])
        shown = {b["description"]: (b["amount"], b["direction"]) for b in (json.loads(r["messages"][0]["content"])["bank_line"] for r in self.api.requests)}
        self.assertEqual((shown["MOBILE DEPOSIT"], shown["BRIGHTSIGN STUDIO"]), ((512.34, "money in"), (239.99, "money out")))   # the direction is said in words, not left to a sign
        self.assertEqual(got["F001"]["item_class"], "recurring_vendor")
        self.assertEqual(got["F010"]["item_class"], "person_payment")     # a payment to a person never reaches the model

    def test_a_model_suggestion_always_goes_to_a_person(self):
        result, got = self.run_with(says(confidence=1.0))
        p = got["F008"]
        self.assertEqual((p["item_class"], p["status"], p["queue"]), ("model_suggestion", "waiting", "exception"))
        self.assertEqual(p["action"]["account"], "Office Supplies")
        self.assertIn("class always reviewed", p["reasons"][0])
        self.assertEqual((result["auto_posted"], self.ledger.writes), (0, 0))
        with self.assertRaises(Refused):
            grant_standing(self.store, OWNER, "cafe", "model_suggestion", p["class_key"], 99999, "trust the model")

    def test_an_account_outside_the_chart_or_forbidden_is_not_a_proposal(self):
        for account in ("Made Up Account", "Opening Balance Equity", "Operating Checking", ""):
            self.tearDown()
            self.setUp()
            _, got = self.run_with(says(account=account))
            self.assertEqual((got["F008"]["item_class"], got["F008"]["action"]), ("unknown", None), account)

    def test_the_schema_offered_to_the_model_excludes_bank_and_opening_balance_equity(self):
        self.run_with(says())
        offered = self.api.requests[0]["output_config"]["format"]["schema"]["properties"]["account"]["enum"]
        self.assertIn("Utilities", offered)
        for forbidden in ("Opening Balance Equity", "Operating Checking", "Savings"):
            self.assertNotIn(forbidden, offered)

    def test_needs_person_keeps_the_question_for_the_reviewer(self):
        _, got = self.run_with(says(decision="needs_person", account="", question="Ask the client what this deposit was."))
        self.assertEqual(got["F013"]["action"], None)
        self.assertEqual(got["F013"]["evidence"]["question_for_reviewer"], "Ask the client what this deposit was.")

    def test_when_the_model_fails_the_run_finishes_on_the_baseline(self):
        result, got = self.run_with(RuntimeError("no credit left"))
        self.assertEqual((result["status"], result["new"]), ("finished", 14))
        self.assertEqual(got["F008"]["item_class"], "unknown")
        self.assertEqual(got["F008"]["evidence"]["model_unavailable"], "RuntimeError")
        self.assertIn("no credit left", self.brain.last_error)

    def test_a_request_carries_one_companys_data_only(self):
        self.run_with(says(), client="outfitters")
        sent = json.dumps(self.api.requests)
        self.assertIn("Granite Valley Water", sent)
        for other in ("Harbor", "Ledgerly", "OmniMart", "Northside", "CardSwipe"):
            self.assertNotIn(other, sent)

    def test_without_a_key_the_baseline_is_used(self):
        self.assertIsInstance(from_environment({}), BaselineBrain)
        self.assertIsInstance(from_environment({"ANTHROPIC_API_KEY": "x", "AGENT_BRAIN": "baseline"}), BaselineBrain)


if __name__ == "__main__":
    unittest.main()
