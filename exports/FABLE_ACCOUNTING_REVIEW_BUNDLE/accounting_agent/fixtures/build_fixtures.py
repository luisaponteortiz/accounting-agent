"""Reproducible fictional teaching data; never executed by the accounting runtime."""
import json
from pathlib import Path
from decimal import Decimal


def packet(batch_id, sources):
    return {"synthetic": True, "organization_id": "demo_org", "client_id": "bird_bowl_demo", "external_company_id": "fixture_realm_001", "batch_id": batch_id, "sources": sources}


def source(kind, key, data):
    return {"kind": kind, "key": key, "data": data}


def transaction(key, date, vendor, amount, **changes):
    data = {"source_id": key, "source_system": "fixture", "account_id": "demo_card_001", "date": date, "description": vendor, "amount": amount, "currency": "USD", "status": "posted", "activity": "purchase"}
    data.update(changes)
    return source("transaction", data["account_id"] + ":" + key, data)


def receipt(tx, amount=None):
    t = tx["data"]
    return source("receipt", "receipt-" + t["source_id"], {"transaction_source_id": t["source_id"], "account_id": t["account_id"], "date": t["date"], "vendor": t["description"], "amount": amount or t["amount"], "currency": t["currency"], "content": "Fictional structured receipt for " + t["source_id"] + "; not an authentic document."})


def main():
    txs = [
        transaction("TX-001", "2026-11-03", "ACME PAPER DEMO", "42.50"),
        transaction("TX-002", "2026-11-04", "METRO REPAIR DEMO", "180.00"),
        transaction("TX-003", "2026-11-05", "UNKNOWN MARKET DEMO", "65.00"),
        transaction("TX-004", "2026-11-06", "ACME PAPER DEMO", "90.00"),
        transaction("TX-005", "2026-11-06", "ACME PAPER DEMO", "90.00"),
        transaction("TX-006", "2026-11-07", "ACME PAPER DEMO", "-42.50", activity="credit"),
        transaction("TX-007", "2026-11-08", "ACME PAPER DEMO", "10.00", status="pending"),
        transaction("TX-008", "2026-10-31", "ACME PAPER DEMO", "25.00"),
        transaction("TX-009", "2026-11-09", "ACME PAPER DEMO", "80.00"),
        transaction("TX-010", "2026-11-10", "METRO REPAIR DEMO", "35.00", requires_split=True),
        transaction("TX-011", "2026-11-11", "ACME PAPER DEMO", "55.00", currency="EUR"),
        transaction("TX-012", "2026-11-12", "CARD PAYMENT DEMO", "300.00", activity="payment"),
    ]
    receipts = [receipt(t, "79.99" if t["data"]["source_id"] == "TX-009" else None) for t in txs if t["data"]["source_id"] != "TX-002"]
    counted = [t["data"] for t in txs if t["data"]["status"] == "posted" and t["data"]["currency"] == "USD" and t["data"]["date"].startswith("2026-11")]
    control = source("statement_control", "demo-card-control", {"account_id": "demo_card_001", "currency": "USD", "period_start": "2026-11-01", "period_end": "2026-11-30", "posted_count": len(counted), "posted_total": str(sum((Decimal(t["amount"]) for t in counted), Decimal("0.00"))), "content": "Fictional statement control, not a complete real card statement."})
    support = source("document", "journal-support-001", {"document_type": "journal_support", "content": "Fictional approved-purchase support; accounting treatment still requires human review."})
    tb = source("document", "trial-balance-placeholder", {"document_type": "trial_balance", "content": "Fictional trial-balance placeholder; no actual client balances or report verified."})
    def journal(key, credit):
        return source("journal", key, {"date": "2026-11-13", "currency": "USD", "memo": "Fictional preparation example only", "lines": [{"account_id": "DEMO_OFFICE_SUPPLIES", "debit": "25.00", "credit": "0.00"}, {"account_id": "DEMO_CARD_LIABILITY", "debit": "0.00", "credit": credit}], "supporting_keys": ["journal-support-001"]})
    root = Path(__file__).parent
    (root / "teaching.json").write_text(json.dumps(packet("teaching-v1", txs + receipts + [control, support, tb, journal("J-001", "25.00"), journal("J-002", "24.99")]), indent=2) + "\n")
    (root / "late_receipt.json").write_text(json.dumps(packet("late-receipt-v1", [receipt(txs[1])]), indent=2) + "\n")


if __name__ == "__main__":
    main()
