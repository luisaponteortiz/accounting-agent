"""Review tests for the agent working a QuickBooks sandbox company through its clearing account. No network."""
import json
import threading
import unittest
import urllib.request
from datetime import date

from hosted_agent import demo_books, qbo, review
from hosted_agent.brain import BaselineBrain
from hosted_agent.ledger import Books, FakeLedger, LedgerError
from hosted_agent.qbo_ledger import QboLedger
from hosted_agent.runner import run_client
from hosted_agent.store import Store
from hosted_agent.tests.test_qbo import Intuit
from hosted_agent.web import ReviewServer

OWNER = dict(name="Owner (test)", role="owner")
REALM = "123"


class QboLedgerCase(unittest.TestCase):
    def setUp(self):
        self.intuit = Intuit()
        self.q = qbo.Qbo("the-id", "the-secret", "https://agent.example/qbo/callback", transport=self.intuit, clock=lambda: 1000.0)
        self.books = QboLedger(self.q, today=lambda: date(2026, 11, 17))
        self.store = Store()
        self.addCleanup(self.store.close)

    def connect(self, mode="post_approved"):
        state = self.q.authorize_url("Owner (test)").split("state=")[1].split("&")[0]
        self.q.finish(state, "code", REALM)
        self.store.add_client("sandbox", "Sandbox Company_US_1", REALM, mode=mode, spot_check_percent=0)
        return len(self.intuit.calls)

    def run_agent(self):
        result = run_client(self.store, self.books, BaselineBrain(), "sandbox")
        self.assertEqual(result["status"], "finished", result)
        return {p["item_key"]: p for p in self.store.proposals("sandbox")}

    def writes(self, since):
        return [(c[0], c[1].split("/company/%s/" % REALM)[1].split("?")[0]) for c in self.intuit.calls[since:] if c[0] != "GET"]

    def record(self, kind, txn_id):
        return next(r for r in self.intuit.records[kind] if r["Id"] == txn_id)

    def test_every_call_must_name_the_connected_company(self):
        with self.assertRaises(LedgerError):
            self.books.company(REALM)                                   # nothing connected yet
        before = self.connect()
        for call in (lambda: self.books.company("999"), lambda: self.books.pending_feed("999"),
                     lambda: self.books.categorize("999", "P21", "Utilities", None, ""), lambda: self.books.move("999", "T1", "BillPayment", "B6")):
            with self.assertRaises(LedgerError):
                call()
        self.assertEqual(len(self.intuit.calls), before)                # another company's name never reaches QuickBooks

    def test_the_company_check_reads_the_name_the_fiscal_year_and_the_closing_date(self):
        self.connect()
        self.assertEqual(self.books.company(REALM), dict(realm_id=REALM, name="Sandbox Company_US_1", closed_through="", fiscal_year_start="2026-01-01", today="2026-11-17"))
        self.intuit.closed = "2026-10-31"
        self.assertEqual(self.books.company(REALM)["closed_through"], "2026-10-31")

    def test_the_work_list_is_the_uncleared_clearing_lines_and_the_clearing_account_is_never_a_category(self):
        before = self.connect()
        feed = {i["id"]: i for i in self.books.pending_feed(REALM)}
        self.assertEqual((feed["P21"]["amount_cents"], feed["P21"]["description"], feed["P21"]["bank_account"], feed["P21"]["status"]), (-41980, "CITY POWER & LIGHT ACH 4502", "Checking", "pending"))
        self.assertEqual((feed["D33"]["amount_cents"], feed["D33"]["description"]), (184000, "DEPOSIT BAYVIEW CATERING"))
        names = [a["name"] for a in self.books.accounts(REALM)]
        self.assertIn("Job Expenses:Decks and Patios", names)           # sub-accounts go by their full name
        self.assertFalse({"Bank Feed Clearing", "Card Feed Clearing"} & set(names))
        self.assertEqual(self.books.bank_accounts(REALM), ["Checking", "Savings"])
        self.assertEqual([(b["id"], b["vendor"], b["amount_cents"]) for b in self.books.open_bills(REALM)], [("B100", "Northside Produce Co", 64210), ("B101", "Northside Produce Co", 38000)])
        self.assertEqual([(i["id"], i["customer"], i["amount_cents"]) for i in self.books.open_invoices(REALM)], [("I200", "Bayview Catering", 184000), ("I201", "Bayview Catering", 64210)])
        seen = [h for h in self.books.history(REALM) if h["vendor"] == "City Power and Light"]
        self.assertEqual((len(seen), {h["account"] for h in seen}), (3, {"Utilities"}))
        self.assertFalse([h for h in self.books.history(REALM) if h["id"] in ("Purchase 20", "Purchase 21", "Deposit 30")])   # a line waiting in clearing is not history
        self.books.move(REALM, "T1", "BillPayment", "B6")
        self.assertNotIn("T1", [i["id"] for i in self.books.pending_feed(REALM)])
        self.assertEqual(self.writes(before), [("POST", "billpayment")])

    def test_a_run_proposes_a_treatment_for_each_kind_of_clearing_line(self):
        self.connect()
        got = self.run_agent()
        told = {key: (p["item_class"], (p["action"] or {}).get("kind"), p["queue"]) for key, p in got.items()}
        self.assertEqual(told["P21"][:2], ("recurring_vendor", "categorize"))
        self.assertEqual(got["P21"]["action"], dict(kind="categorize", account="Utilities", vendor="City Power and Light", memo="Categorized as in prior months"))
        self.assertEqual((told["P22"][:2], got["P22"]["action"]["txn_id"]), (("bill_payment_match", "match"), "B100"))
        self.assertEqual((told["D33"][:2], got["D33"]["action"]["txn_id"]), (("invoice_payment_match", "match"), "I200"))
        self.assertEqual((told["D30"][:2], got["D30"]["action"]["txn_id"], got["D30"]["confidence"]), (("already_recorded", "move"), "31", 0.97))
        self.assertEqual((told["T1"][:2], got["T1"]["action"]["txn_id"], got["T1"]["confidence"]), (("already_recorded", "move"), "B6", 0.7))   # two candidates: a person looks
        self.assertIn("low confidence", got["T1"]["reasons"])
        self.assertEqual(told["T2"][:2], ("no_bank_text", None))
        self.assertEqual((told["T4"][:2], got["T4"]["action"]["txn_id"], got["T4"]["confidence"]), (("already_recorded", "move"), "B9", 0.97))   # a card line: to the card clearing account (D-045)
        self.assertTrue(all(p["status"] == "waiting" for p in got.values()))   # nothing posts without a person

    def test_an_approved_category_changes_only_the_category_and_payee_and_is_read_back(self):
        before = self.connect()
        got = self.run_agent()
        kept = json.loads(json.dumps(self.record("Purchase", "21")))
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["P21"]["id"], "approve"), "posted")
        self.assertEqual(self.writes(before), [("POST", "purchase")])
        now = self.record("Purchase", "21")
        kept["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"] = {"value": "62", "name": "Utilities"}
        kept.update(EntityRef={"value": "V1", "name": "City Power and Light", "type": "Vendor"}, PrivateNote="Categorized as in prior months", SyncToken="1")
        self.assertEqual(now, kept)                                      # date, amount, bank account and bank text are as they were
        posting = self.store.one("SELECT * FROM postings WHERE proposal_id=?", (got["P21"]["id"],))
        self.assertEqual((posting["verified"], posting["ledger_ref"], posting["actor"]), (1, "Purchase 21", "Owner (test)"))
        self.assertNotIn("P21", [i["id"] for i in self.books.pending_feed(REALM)])

    def test_an_approved_match_pays_the_open_bill_or_invoice_through_the_clearing_account(self):
        before = self.connect()
        got = self.run_agent()
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["P22"]["id"], "approve"), "posted")
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["D33"]["id"], "approve"), "posted")
        self.assertEqual(self.writes(before), [("POST", "billpayment"), ("POST", "payment")])
        paid, received = self.intuit.records["BillPayment"][-1], self.intuit.records["Payment"][-1]
        self.assertEqual((paid["CheckPayment"]["BankAccountRef"]["value"], paid["TotalAmt"], paid["TxnDate"], paid["VendorRef"]["value"], paid["Line"][0]["LinkedTxn"]),
                         ("90", 642.1, "2026-11-15", "V2", [{"TxnId": "B100", "TxnType": "Bill"}]))   # dated the day the money moved
        self.assertEqual((received["DepositToAccountRef"]["value"], received["TotalAmt"], received["TxnDate"], received["Line"][0]["LinkedTxn"]),
                         ("90", 1840.0, "2026-11-16", [{"TxnId": "I200", "TxnType": "Invoice"}]))
        self.assertNotIn("Checking", json.dumps([paid, received]))       # the bank account already has the bank's own line
        self.assertEqual((self.record("Bill", "B100")["Balance"], self.record("Invoice", "I200")["Balance"]), (0, 0))
        self.assertEqual([r["verified"] for r in self.store.rows("SELECT verified FROM postings ORDER BY id")], [1, 1])
        self.assertFalse({"P22", "D33"} & {i["id"] for i in self.books.pending_feed(REALM)})

    def test_an_approved_move_goes_through_the_same_review_and_read_back(self):
        before = self.connect()
        got = self.run_agent()
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["D30"]["id"], "approve"), "posted")
        self.assertEqual((self.writes(before), self.record("Deposit", "31")["DepositToAccountRef"]["value"]), ([("POST", "deposit")], "90"))
        posting = self.store.one("SELECT * FROM postings WHERE proposal_id=?", (got["D30"]["id"],))
        self.assertEqual((posting["verified"], posting["ledger_ref"]), (1, "Deposit 31"))
        sent = len(self.intuit.calls)
        with self.assertRaises(LedgerError):                             # the line is cancelled: it cannot be given a category as well
            self.books.categorize(REALM, "D30", "Utilities", None, "")
        self.assertEqual(self.writes(sent), [])

    def test_a_recorded_card_charge_is_moved_to_the_card_clearing_account_on_approval(self):
        before = self.connect()
        got = self.run_agent()
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["T4"]["id"], "approve"), "posted")
        held = self.record("BillPayment", "B9")
        self.assertEqual((self.writes(before), held["CreditCardPayment"]["CCAccountRef"], held["PayType"]), ([("POST", "billpayment")], {"value": "91", "name": "Card Feed Clearing"}, "CreditCard"))
        posting = self.store.one("SELECT * FROM postings WHERE proposal_id=?", (got["T4"]["id"],))
        self.assertEqual((posting["verified"], posting["ledger_ref"]), (1, "BillPayment B9"))
        self.assertNotIn("T4", [i["id"] for i in self.books.pending_feed(REALM)])

    def test_without_a_card_clearing_account_a_recorded_card_charge_goes_to_a_person_with_the_reason(self):
        before = self.connect()
        next(a for a in self.intuit.accounts if a["Id"] == "91")["Name"] = "Some Other Card"
        got = self.run_agent()
        self.assertEqual((got["T4"]["item_class"], got["T4"]["action"], got["T4"]["queue"]), ("already_recorded", None, "exception"))
        self.assertIn("no clearing account", got["T4"]["evidence"]["why"])
        with self.assertRaises(LedgerError):
            self.books.move(REALM, "T4", "BillPayment", "B9")
        self.assertEqual(self.writes(before), [])

    def test_a_card_line_in_the_card_clearing_account_is_worked_like_any_other(self):
        before = self.connect()
        self.intuit.records["Purchase"].append({"Id": "23", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 12.0, "PaymentType": "CreditCard", "AccountRef": {"value": "41", "name": "Mastercard"},
                                                "Line": [{"Amount": 12.0, "Description": "AMZN MKTP", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "91", "name": "Card Feed Clearing"}}}]})
        feed = {i["id"]: i for i in self.books.pending_feed(REALM)}
        self.assertEqual((feed["P23"]["amount_cents"], feed["P23"]["bank_account"], feed["P23"]["description"]), (-1200, "Mastercard", "AMZN MKTP"))
        self.assertFalse([h for h in self.books.history(REALM) if h["id"] == "Purchase 23"])     # waiting in clearing: not history
        self.assertEqual(self.books.categorize(REALM, "P23", "Supplies", None, ""), "Purchase 23")
        now = self.record("Purchase", "23")
        self.assertEqual((now["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"], now["AccountRef"]["name"], now["PaymentType"]), ({"value": "60", "name": "Supplies"}, "Mastercard", "CreditCard"))
        self.assertEqual((self.writes(before), self.books.read_back(REALM, "P23")["posted"]["account"]), ([("POST", "purchase")], "Supplies"))
        self.assertTrue([h for h in self.books.history(REALM) if h["id"] == "Purchase 23"])

    def test_a_transfer_between_the_companys_own_accounts_is_paired_on_approval(self):
        before = self.connect()
        self.intuit.add_transfer_lines(out_date="2026-11-10", in_date="2026-11-11")
        got = self.run_agent()
        out, into = got["P24"], got["D34"]
        self.assertEqual((out["item_class"], out["class_key"], out["action"], out["confidence"], out["evidence"]["other_side"]),
                         ("own_transfer", "Checking <> Savings", dict(kind="transfer", other_account="Savings"), 0.97, "D34"))
        self.assertEqual((into["item_class"], into["action"]), ("own_transfer", dict(kind="transfer", other_account="Checking")))
        with self.assertRaises(LedgerError):
            self.books.transfer(REALM, "P24", "Mastercard")                 # the other side is in Savings, not in the account named
        self.assertEqual(self.writes(before), [])
        self.assertEqual(review.decide(self.store, self.books, OWNER, out["id"], "approve"), "posted")
        self.assertEqual(self.writes(before), [("POST", "purchase"), ("POST", "deposit")])
        posting = self.store.one("SELECT * FROM postings WHERE proposal_id=?", (out["id"],))
        self.assertEqual((posting["verified"], posting["ledger_ref"]), (1, "Purchase 24"))
        self.assertFalse({"P24", "D34"} & {i["id"] for i in self.books.pending_feed(REALM)})      # one approval clears both lines
        self.assertEqual((self.record("Purchase", "24")["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"]["value"], self.record("Deposit", "34")["DepositToAccountRef"]["name"]), ("90", "Savings"))
        sent = len(self.intuit.calls)
        self.assertEqual(review.decide(self.store, self.books, OWNER, into["id"], "approve"), "posted")   # the other side: already done, nothing more is written
        self.assertEqual((self.writes(sent), self.store.one("SELECT verified, ledger_ref FROM postings WHERE proposal_id=?", (into["id"],))), ([], dict(verified=1, ledger_ref="Deposit 34")))

    def test_the_other_side_of_a_paired_transfer_is_seen_as_done_on_the_next_run(self):
        self.connect()
        self.intuit.add_transfer_lines(out_date="2026-11-10", in_date="2026-11-11")
        got = self.run_agent()
        review.decide(self.store, self.books, OWNER, got["P24"]["id"], "approve")
        before = len(self.intuit.calls)
        self.assertEqual(run_client(self.store, self.books, BaselineBrain(), "sandbox")["observed"], 1)
        self.assertEqual((self.store.proposal(got["D34"]["id"])["status"], self.writes(before)), ("observed_same", []))

    def test_a_likely_transfer_without_the_word_goes_to_a_person_and_says_when_it_was_also_recorded_by_hand(self):
        before = self.connect()
        self.intuit.add_transfer_lines()                                   # 6 and 7 October: transfer T3 of 5 October was recorded by hand
        self.record("Purchase", "24")["Line"][0]["Description"] = ""
        self.record("Deposit", "34")["Line"][0]["Description"] = "MOBILE DEPOSIT"
        self.record("Deposit", "34")["PrivateNote"] = ""
        got = self.run_agent()
        for key, other in (("P24", "Savings"), ("D34", "Checking")):
            p = got[key]
            self.assertEqual((p["item_class"], p["action"], p["confidence"], p["queue"]), ("own_transfer", dict(kind="transfer", other_account=other), 0.7, "exception"), key)
            self.assertIn("low confidence", p["reasons"])
            self.assertIn("recorded transfer T3", p["evidence"]["reasoning"])
            self.assertIn("for a person to remove", p["evidence"]["reasoning"])
        self.assertEqual(self.writes(before), [])                          # the recorded transfer is never deleted or changed by the agent
        self.intuit.transfers[:] = [t for t in self.intuit.transfers if t["Id"] != "T3"]
        self.store.run("DELETE FROM proposals")
        again = self.run_agent()
        self.assertIn("does not say transfer", again["P24"]["evidence"]["reasoning"])
        self.assertEqual(again["P24"]["evidence"]["recorded_transfers"], [])

    def test_a_clear_transfer_that_was_also_recorded_by_hand_goes_to_a_person(self):
        self.connect()
        self.intuit.add_transfer_lines()                                   # the bank text says transfer; T3 of 5 October is the same money recorded by hand
        got = self.run_agent()
        for key in ("P24", "D34"):
            p = got[key]
            self.assertEqual((p["item_class"], p["confidence"], p["queue"]), ("own_transfer", 0.7, "exception"), key)
            self.assertIn("recorded transfer T3", p["evidence"]["reasoning"])

    def test_a_pairing_that_quickbooks_did_not_keep_is_not_reported_as_done(self):
        self.connect()
        self.intuit.add_transfer_lines(out_date="2026-11-10", in_date="2026-11-11")
        self.intuit.ignore_change = True                                   # QuickBooks says yes but the notes are not there
        with self.assertRaises(LedgerError):
            self.books.transfer(REALM, "P24", "Savings")
        self.intuit.ignore_change = False
        self.assertEqual(self.books.transfer(REALM, "P24", "Savings"), "Purchase 24")
        with self.assertRaises(LedgerError):
            self.books.transfer(REALM, "P24", "Mastercard")                 # paired with the Savings line, not with the account named
        self.assertEqual(self.books.read_back(REALM, "D34")["posted"]["account"], "Checking")

    def test_a_payment_to_the_companys_own_card_is_settled_on_approval(self):
        before = self.connect()
        self.intuit.add_card_payment_lines()
        got = self.run_agent()
        out, into = got["P28"], got["D48"]
        self.assertEqual((out["item_class"], out["class_key"], out["action"], out["confidence"], out["evidence"]["other_side"]),
                         ("card_payment", "Checking > Mastercard", dict(kind="transfer", other_account="Mastercard"), 0.97, "D48"))
        self.assertEqual((into["item_class"], into["class_key"], into["action"]), ("card_payment", "Checking > Mastercard", dict(kind="transfer", other_account="Checking")))
        kept = json.loads(json.dumps([self.record("Purchase", "28"), self.record("Deposit", "48")]))
        self.assertEqual(review.decide(self.store, self.books, OWNER, into["id"], "approve"), "posted")       # approved from the card side
        self.assertEqual(self.writes(before), [("POST", "transfer")])
        self.assertEqual([self.record("Purchase", "28"), self.record("Deposit", "48")], kept)
        posting = self.store.one("SELECT * FROM postings WHERE proposal_id=?", (into["id"],))
        self.assertEqual((posting["verified"], posting["ledger_ref"]), (1, "Deposit 48"))
        self.assertFalse({"P28", "D48"} & {i["id"] for i in self.books.pending_feed(REALM)})      # one approval clears both lines
        sent = len(self.intuit.calls)
        self.assertEqual(review.decide(self.store, self.books, OWNER, out["id"], "approve"), "posted")        # the bank side: already done, nothing more is entered
        self.assertEqual(self.writes(sent), [])
        self.assertEqual(self.books.read_back(REALM, "P28")["posted"]["account"], "Mastercard")

    def test_a_likely_card_payment_goes_to_a_person_and_a_charge_is_never_one(self):
        before = self.connect()
        self.intuit.add_card_payment_lines()
        self.record("Purchase", "28")["Line"][0]["Description"] = "ACH DEBIT 4411"
        self.record("Deposit", "48")["Line"][0]["Description"] = ""
        self.intuit.records["Purchase"].append({"Id": "29", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 77.0, "PaymentType": "CreditCard", "AccountRef": {"value": "41", "name": "Mastercard"},
                                                "Line": [{"Amount": 77.0, "Description": "PAYMENT TO A STORE", "AccountBasedExpenseLineDetail": {"AccountRef": {"value": "91", "name": "Card Feed Clearing"}}}]})
        self.intuit.records["Deposit"].append({"Id": "52", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 77.0, "DepositToAccountRef": {"value": "35", "name": "Checking"},
                                               "Line": [{"Amount": 77.0, "Description": "PAYMENT FROM A CUSTOMER", "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})
        got = self.run_agent()
        for key in ("P28", "D48"):
            p = got[key]
            self.assertEqual((p["item_class"], p["confidence"], p["queue"]), ("card_payment", 0.7, "exception"), key)
            self.assertIn("neither bank text says payment", p["evidence"]["reasoning"])
        self.assertNotEqual(got["P29"]["item_class"], "card_payment")       # a charge on the card and money in to the bank are not a card payment
        self.assertNotEqual(got["D52"]["item_class"], "card_payment")
        with self.assertRaises(LedgerError):
            self.books.transfer(REALM, "P29", "Checking")
        self.intuit.records["Deposit"].append({"Id": "53", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 250.0, "DepositToAccountRef": {"value": "41", "name": "Mastercard"},
                                               "Line": [{"Amount": 250.0, "DepositLineDetail": {"AccountRef": {"value": "91", "name": "Card Feed Clearing"}}}]})
        self.store.run("DELETE FROM proposals")
        again = self.run_agent()
        self.assertNotEqual(again["P28"]["item_class"], "card_payment")     # two lines on the card could be the other side: nothing is proposed
        with self.assertRaises(LedgerError):
            self.books.transfer(REALM, "P28", "Mastercard")
        self.assertEqual(self.writes(before), [])

    def test_a_card_payment_whose_lines_sit_in_one_clearing_account_is_only_marked(self):
        before = self.connect()
        self.intuit.add_card_payment_lines(held_in="90")                    # the card line was posted against the bank clearing account
        got = self.run_agent()
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["P28"]["id"], "approve"), "posted")
        self.assertEqual(self.writes(before), [("POST", "purchase"), ("POST", "deposit")])     # a note on each record, no new transfer
        self.assertFalse({"P28", "D48"} & {i["id"] for i in self.books.pending_feed(REALM)})

    def test_a_transfer_with_two_possible_other_sides_is_not_paired(self):
        before = self.connect()
        self.intuit.add_transfer_lines(out_date="2026-11-10", in_date="2026-11-11")
        self.intuit.records["Deposit"].append({"Id": "35", "SyncToken": "0", "TxnDate": "2026-11-12", "TotalAmt": 500.0, "DepositToAccountRef": {"value": "36", "name": "Savings"},
                                               "Line": [{"Amount": 500.0, "DepositLineDetail": {"AccountRef": {"value": "90", "name": "Bank Feed Clearing"}}}]})
        got = self.run_agent()
        self.assertNotEqual(got["P24"]["item_class"], "own_transfer")       # two deposits could be the other side: no proposal of a transfer
        for call in (lambda: self.books.transfer(REALM, "P24", "Savings"), lambda: self.books.transfer(REALM, "P24", "Checking"),
                     lambda: self.books.transfer(REALM, "P24", "Mastercard"), lambda: self.books.transfer(REALM, "P99", "Savings"), lambda: self.books.transfer("999", "P24", "Savings")):
            with self.assertRaises(LedgerError):
                call()
        self.assertEqual(self.writes(before), [])

    def test_a_memo_already_on_the_record_is_kept(self):
        self.connect()
        self.record("Purchase", "21")["PrivateNote"] = "Memo from the bank"
        self.books.categorize(REALM, "P21", "Utilities", "city power and light", "Categorized as in prior months")   # the payee is found whatever its capitals
        now = self.record("Purchase", "21")
        self.assertEqual((now["PrivateNote"], now["EntityRef"]["value"]), ("Memo from the bank", "V1"))

    def test_what_the_books_do_not_support_is_refused_before_anything_is_sent(self):
        before = self.connect()
        refused = (lambda: self.books.categorize(REALM, "P21", "No Such Account", None, ""),
                   lambda: self.books.categorize(REALM, "P21", "Bank Feed Clearing", None, ""),          # back into clearing is no treatment
                   lambda: self.books.categorize(REALM, "P21", "Card Feed Clearing", None, ""),
                   lambda: self.books.match(REALM, "T4", "bill", "B100"),                                # paying an open bill from a card line is not built
                   lambda: self.books.categorize(REALM, "P21", "Utilities", "A Vendor Nobody Added", ""),
                   lambda: self.books.categorize(REALM, "T2", "Utilities", None, ""),                    # posted as a transfer: it has no category to change
                   lambda: self.books.categorize(REALM, "P99", "Utilities", None, ""),
                   lambda: self.books.match(REALM, "P22", "bill", "B101"),                               # another amount
                   lambda: self.books.match(REALM, "P22", "bill", "B099"),                               # already paid
                   lambda: self.books.match(REALM, "P22", "bill", "B777"),
                   lambda: self.books.match(REALM, "P22", "invoice", "I201"),                            # money out cannot pay an invoice, even of the same amount
                   lambda: self.books.match(REALM, "D33", "bill", "B100"),
                   lambda: self.books.transfer(REALM, "P21", "Savings"))                                 # no line in Savings is its other side
        for number, call in enumerate(refused):
            with self.assertRaises(LedgerError, msg=number):
                call()
        self.assertEqual(self.writes(before), [])
        self.intuit.refuse_change = True                                 # QuickBooks itself says no
        with self.assertRaises(LedgerError) as told:
            self.books.categorize(REALM, "P21", "Utilities", None, "")
        self.assertIn("You and another user were working on the same thing.", str(told.exception))
        self.assertEqual(self.record("Purchase", "21")["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"]["value"], "90")

    def test_a_payee_the_books_lack_is_added_only_when_the_option_is_on_and_a_person_approved_it(self):
        before = self.connect()
        got = self.run_agent()
        change = dict(kind="categorize", account="Utilities", vendor="A1 Rental", memo="")
        with self.assertRaises(LedgerError):                              # the option is off unless the owner turns it on
            self.books.categorize(REALM, "P21", "Utilities", "A1 Rental", "", by_person=True)
        self.books.add_payees = True
        with self.assertRaises(LedgerError):                              # on, but nobody approved this item: a standing approval never adds a payee
            self.books.categorize(REALM, "P21", "Utilities", "A1 Rental", "")
        from hosted_agent.runner import execute
        self.assertFalse(execute(self.store, self.books, got["P22"]["id"], change, "standing", "agent"))
        self.assertIn("no vendor named A1 Rental", self.store.proposal(got["P22"]["id"])["reasons"][-1])
        for bad in ("Rentals:A1", "x" * 101, "   "):                     # a name QuickBooks would not take, or no name at all
            with self.assertRaises(LedgerError, msg=bad):
                self.books._party(bad, ("Vendor",), "Vendor")
        with self.assertRaises(LedgerError):
            self.books.categorize(REALM, "P21", "No Such Account", "A1 Rental", "", by_person=True)   # a bad category stops it before a payee is added
        self.assertEqual((self.writes(before), len(self.intuit.records["Vendor"])), ([], 2))
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["P21"]["id"], "change", change), "posted")
        self.assertEqual(self.writes(before), [("POST", "vendor"), ("POST", "purchase")])
        made = self.intuit.records["Vendor"][-1]
        self.assertEqual((made["DisplayName"], set(made) - {"Id", "SyncToken"}), ("A1 Rental", {"DisplayName"}))   # the name and nothing else
        self.assertEqual(self.record("Purchase", "21")["EntityRef"], {"value": made["Id"], "name": "A1 Rental", "type": "Vendor"})
        self.assertEqual(self.store.one("SELECT verified FROM postings WHERE proposal_id=?", (got["P21"]["id"],))["verified"], 1)
        self.books.categorize(REALM, "P22", "Utilities", "a1  RENTAL", "", by_person=True)       # the same payee again: found, not added twice
        self.assertEqual((len(self.intuit.records["Vendor"]), self.record("Purchase", "22")["EntityRef"]["value"]), (3, made["Id"]))
        self.assertFalse([c for c in self.intuit.calls if c[0] == "DELETE" or "operation=delete" in c[1]])

    def test_money_in_from_an_unknown_payer_adds_a_customer_and_a_refused_posting_does_not_add_it_twice(self):
        before = self.connect()
        self.books.add_payees = True
        self.books.categorize(REALM, "D33", "Supplies", "City Power and Light", "", by_person=True)   # a vendor refund: the vendor is in the books, nothing is added
        self.assertEqual(self.writes(before), [("POST", "deposit")])
        customers = len(self.intuit.records["Customer"])
        real = self.intuit.__class__.__call__

        def refuse_the_deposit(method, url, headers, body=None):
            self.intuit.refuse_change = method == "POST" and url.split("?")[0].endswith("/deposit")
            return real(self.intuit, method, url, headers, body)
        self.q.transport = refuse_the_deposit
        with self.assertRaises(LedgerError):                              # the customer is added, then QuickBooks refuses the deposit
            self.books.categorize(REALM, "D30", "Supplies", "Walk-in Customer", "", by_person=True)
        self.q.transport, self.intuit.refuse_change = self.intuit, False
        self.assertEqual(len(self.intuit.records["Customer"]), customers + 1)
        self.books.categorize(REALM, "D30", "Supplies", "Walk-in Customer", "", by_person=True)   # the second try finds the customer it added
        self.assertEqual(len(self.intuit.records["Customer"]), customers + 1)
        entity = self.record("Deposit", "30")["Line"][0]["DepositLineDetail"]["Entity"]
        self.assertEqual((entity["name"], entity["type"], entity["value"]), ("Walk-in Customer", "CUSTOMER", self.intuit.records["Customer"][-1]["Id"]))

    def test_the_firm_rules_still_stop_a_posting(self):
        self.connect(mode="prepare_only")
        got = self.run_agent()
        before = len(self.intuit.calls)
        self.assertEqual(review.decide(self.store, self.books, OWNER, got["P21"]["id"], "approve"), "approved_not_posted")   # prepare only: nothing is sent
        self.assertEqual(self.writes(before), [])
        self.store.run("UPDATE clients SET mode='post_approved' WHERE client_id='sandbox'")
        self.intuit.closed = "2026-11-15"
        with self.assertRaises(review.Refused) as told:
            review.decide(self.store, self.books, OWNER, got["P22"]["id"], "approve")                   # dated in the closed period
        self.assertIn("closed period", str(told.exception))
        with self.assertRaises(review.Refused):
            review.decide(self.store, self.books, OWNER, got["D33"]["id"], "change", dict(kind="categorize", account="Opening Balance Equity", vendor=None, memo=""))
        self.assertEqual(self.writes(before), [])

    def test_a_line_a_person_handled_in_quickbooks_is_observed_not_posted_again(self):
        self.connect()
        got = self.run_agent()
        purchase = self.record("Purchase", "21")                         # a person categorizes it directly, as the agent proposed
        purchase["Line"][0]["AccountBasedExpenseLineDetail"]["AccountRef"] = {"value": "62", "name": "Utilities"}
        purchase["EntityRef"] = {"value": "V1", "name": "City Power and Light"}
        before = len(self.intuit.calls)
        self.assertEqual(run_client(self.store, self.books, BaselineBrain(), "sandbox")["observed"], 1)
        self.assertEqual(self.store.proposal(got["P21"]["id"])["status"], "observed_same")
        self.assertEqual(self.writes(before), [])

    def test_each_company_goes_to_its_own_books(self):
        self.connect()
        fake = FakeLedger(demo_books.companies())
        books = Books(fake)
        books.add(REALM, self.books)
        self.assertEqual((books.company("9001")["name"], books.company(REALM)["name"]), ("Harbor Light Cafe LLC (fictional)", "Sandbox Company_US_1"))
        before = len(self.intuit.calls)
        self.assertTrue(books.pending_feed("9001"))
        self.assertEqual(len(self.intuit.calls), before)                 # the fictional company's work never touches QuickBooks
        with self.assertRaises(LedgerError):
            books.company("555")
        with self.assertRaises(AttributeError):
            books.delete

    def test_connecting_the_sandbox_adds_it_as_a_client_in_prepare_only_mode(self):
        fake = FakeLedger(demo_books.companies())
        server = ReviewServer(("127.0.0.1", 0), self.store, fake, BaselineBrain(), {"owner-token": OWNER}, self.q)
        threading.Thread(target=server.serve_forever, kwargs=dict(poll_interval=0.05), daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        state = self.q.authorize_url("Owner (test)").split("state=")[1].split("&")[0]
        with urllib.request.urlopen("http://127.0.0.1:%s/qbo/callback?state=%s&code=c&realmId=%s" % (server.server_port, state, REALM), timeout=5) as response:
            self.assertIn(b"connected", response.read())
        client = self.store.client("qbo-" + REALM)
        self.assertEqual((client["name"], client["realm_id"], client["mode"]), ("Sandbox Company_US_1", REALM, "prepare_only"))
        request = urllib.request.Request("http://127.0.0.1:%s/api/state?client=qbo-%s" % (server.server_port, REALM), headers={"Authorization": "Bearer owner-token"})
        with urllib.request.urlopen(request, timeout=5) as response:
            state = json.loads(response.read())
        self.assertIn("Utilities", state["accounts"])
        self.assertEqual(state["payees"], ["Bayview Catering", "City Power and Light", "Northside Produce Co"])   # D-044: the page can mark a payee that approving would add
        self.assertTrue(server.ledger.by_realm[REALM].add_payees)
        self.assertEqual((self.books.payees(REALM), server.ledger.payees("9001")), (None, None))   # off by default; the fictional books have no payee list
        server.adopt_sandbox("Owner (test)")                             # connecting again does not add it twice
        self.assertEqual(len([c for c in self.store.clients() if c["realm_id"] == REALM]), 1)


if __name__ == "__main__":
    unittest.main()
