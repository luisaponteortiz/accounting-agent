"""python -m hosted_agent demo            fictional companies, in memory, with the review page
   python -m hosted_agent run --db FILE   one unattended pass over every client (the scheduled job)"""
import argparse
import json
import os
import secrets

from . import demo_books
from .claude_brain import from_environment
from .ledger import FakeLedger
from .runner import run_client
from .store import Store
from .web import ReviewServer


def people_from_env():
    """AGENT_PEOPLE='{"<long random token>": {"name": "...", "role": "owner"}}'. Without it, demo tokens are made up at start."""
    raw = os.environ.get("AGENT_PEOPLE")
    if raw:
        return json.loads(raw), False
    return {secrets.token_urlsafe(24): dict(name="Demo owner", role="owner"),
            secrets.token_urlsafe(24): dict(name="Demo reviewer", role="reviewer")}, True


def seed_demo(store):
    for company, client_id in zip(demo_books.companies(), ("cafe", "outfitters")):
        if not store.one("SELECT 1 FROM clients WHERE client_id=?", (client_id,)):
            store.add_client(client_id, company["name"], company["realm_id"])


def main():
    parser = argparse.ArgumentParser(prog="hosted_agent", description="Hosted accounting agent, development build")
    parser.add_argument("command", choices=("demo", "run"))
    parser.add_argument("--db", default=":memory:")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8770")))
    args = parser.parse_args()
    store, ledger, brain = Store(args.db), FakeLedger(demo_books.companies()), from_environment(os.environ)
    print("Brain: %s" % brain.name, flush=True)
    seed_demo(store)
    for client in store.clients():
        print(json.dumps(dict(client=client["client_id"], **run_client(store, ledger, brain, client["client_id"]))), flush=True)
    if getattr(brain, "calls", 0):
        print("Model calls: %s. Last error: %s" % (brain.calls, brain.last_error), flush=True)
    if args.command == "run":
        return
    people, made_up = people_from_env()
    server = ReviewServer((args.host, args.port), store, ledger, brain, people)
    print("Review page on port %s. FICTIONAL COMPANIES ONLY." % server.server_port, flush=True)
    if made_up:
        for token, person in people.items():
            print("  %s: http://127.0.0.1:%s/?token=%s" % (person["name"], server.server_port, token), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
