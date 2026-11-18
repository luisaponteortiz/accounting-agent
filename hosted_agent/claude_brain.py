"""Claude behind the same `propose` door as the baseline.

Division of labour: lines the company's own history settles (recurring
vendors, exact bill and invoice matches, own transfers, bank fees, duplicates)
never reach the model. Claude is asked only about the lines that would
otherwise arrive at a person with no proposal, and what it returns is always
reviewed by a person: the class "model_suggestion" can never be covered by a
standing approval. Its job is to make the exception queue faster to clear, not
to post.

One request carries one company's data only.
"""
import json

from .brain import BaselineBrain, proposal
from .ledger import OPENING_BALANCE_EQUITY

ASK_ABOUT = {"unknown", "vendor_seen_few_times", "vendor_mixed_accounts"}
DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM = """You are the preparer for a bookkeeping firm. You are shown one line from a client's bank feed and what that client's books already say. Propose how to categorize it, for a reviewer who will approve, change or reject your proposal.

Rules of the firm:
- Use only an account from the chart you are given, by its exact name. Never Opening Balance Equity. Never a bank account.
- Follow how this client's books have treated the same payee before. If the books show the payee under more than one account, say what distinguishes the cases and choose only if this line clearly fits one.
- If you cannot tell what the money was for from what you are shown, do not guess. Set decision to "needs_person" and write the one question the reviewer should get answered, and who would know (the client, the bank record, a receipt).
- A payment to an individual, a loan, payroll, tax, an owner's personal spending, or anything that looks like a capital purchase always needs a person.
- Give the payee as the business name only, without store or reference numbers.
- Confidence is your honest chance of being right: 0.9 means you would be surprised to be wrong.
- Keep the reasoning to two sentences a busy reviewer can check against the evidence."""


def schema(accounts):
    return {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["categorize", "needs_person"]},
            "account": {"type": "string", "enum": accounts + [""]},
            "payee": {"type": "string"},
            "confidence": {"type": "number"},
            "reasoning": {"type": "string"},
            "question_for_reviewer": {"type": "string"},
        },
        "required": ["decision", "account", "payee", "confidence", "reasoning", "question_for_reviewer"],
        "additionalProperties": False,
    }


def evidence_for(line, ctx):
    """What the model is shown: this company's chart and how its books treated payees. No other client's data exists in ctx."""
    payees = {}
    for txn in ctx.history:
        if txn.get("kind") == "categorize" and txn.get("vendor"):
            seen = payees.setdefault(txn["vendor"], {"bank_text": txn["description"], "accounts": {}})
            seen["accounts"][txn["account"]] = seen["accounts"].get(txn["account"], 0) + 1
    return {
        "bank_line": {k: line[k] for k in ("date", "description", "bank_account")} | {"amount": line["amount_cents"] / 100},
        "chart_of_accounts": ctx.chart,
        "payees_in_the_books": payees,
    }


class ClaudeBrain:
    def __init__(self, client, model=DEFAULT_MODEL, baseline=None):
        self.client, self.model, self.baseline = client, model, baseline or BaselineBrain()
        self.name = "claude:" + model
        self.calls, self.last_error = 0, None

    def propose(self, line, ctx):
        base = self.baseline.propose(line, ctx)
        if base["item_class"] not in ASK_ABOUT:
            return base
        usable = [a["name"] for a in ctx.chart if a["type"] != "Bank" and a["name"] != OPENING_BALANCE_EQUITY]
        try:
            answer = self.ask(line, ctx, usable)
            self.last_error = None
        except Exception as problem:  # the run goes on with the baseline's result; the reviewer sees why
            self.last_error = "%s: %s" % (type(problem).__name__, str(problem)[:200])
            base["evidence"]["model_unavailable"] = type(problem).__name__
            return base
        told = dict(base["evidence"], model=self.model, reasoning=answer["reasoning"][:600])
        if answer["question_for_reviewer"].strip():
            told["question_for_reviewer"] = answer["question_for_reviewer"][:400]
        payee = answer["payee"].strip()[:80] or None
        if answer["decision"] != "categorize" or answer["account"] not in usable:
            return proposal("unknown", base["class_key"], None, 0.0, **told)
        confidence = max(0.0, min(1.0, float(answer["confidence"])))
        action = dict(kind="categorize", account=answer["account"], vendor=payee, memo="")
        return proposal("model_suggestion", "%s | %s" % (payee, answer["account"]), action, confidence, **told)

    def ask(self, line, ctx, usable):
        self.calls += 1
        response = self.client.with_options(timeout=90.0, max_retries=1).messages.create(
            model=self.model,
            max_tokens=4000,
            system=SYSTEM,
            messages=[{"role": "user", "content": json.dumps(evidence_for(line, ctx), indent=1)}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema(usable)}},
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("the model declined this request")
        text = next(block.text for block in response.content if block.type == "text")
        return json.loads(text)


def from_environment(environ):
    """Claude when a key is present and not switched off; otherwise the baseline."""
    if not environ.get("ANTHROPIC_API_KEY") or environ.get("AGENT_BRAIN") == "baseline":
        return BaselineBrain()
    import anthropic
    return ClaudeBrain(anthropic.Anthropic(), environ.get("AGENT_MODEL", DEFAULT_MODEL))
