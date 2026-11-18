"""python -m hosted_agent demo            fictional companies, with the review page (in memory unless AGENT_DB or --db names a file)
   python -m hosted_agent run --db FILE   one unattended pass over every client (the scheduled job)"""
import argparse
import json
import os
import secrets

from . import demo_books
from . import labs, qbo
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


DEMO_CLIENTS = ("cafe", "outfitters")


def seed_demo(store):
    for company, client_id in zip(demo_books.companies(), DEMO_CLIENTS):
        if not store.one("SELECT 1 FROM clients WHERE client_id=?", (client_id,)):
            store.add_client(client_id, company["name"], company["realm_id"])


def main():
    parser = argparse.ArgumentParser(prog="hosted_agent", description="Hosted accounting agent, development build")
    parser.add_argument("command", choices=("demo", "run"))
    parser.add_argument("--db", default=os.environ.get("AGENT_DB") or ":memory:")   # a file on a disk keeps everything across restarts
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8770")))
    args = parser.parse_args()
    if args.db != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    store, ledger, brain = Store(args.db), FakeLedger(demo_books.companies()), from_environment(os.environ)
    if args.db != ":memory:":
        os.chmod(args.db, 0o600)            # the file holds the kept QuickBooks connection: this service's user only
    print("Brain: %s" % brain.name, flush=True)
    print("Records: %s" % ("kept in a file on disk" if args.db != ":memory:" else "in memory only, lost at restart"), flush=True)
    seed_demo(store)
    for client_id in DEMO_CLIENTS:      # a kept sandbox company is not run here: its books are reached only once the page's server is up
        print(json.dumps(dict(client=client_id, **run_client(store, ledger, brain, client_id))), flush=True)
    if getattr(brain, "calls", 0):
        print("Model calls: %s. Last error: %s" % (brain.calls, brain.last_error), flush=True)
    if args.command == "run":
        return
    people, made_up = people_from_env()
    public = (os.environ.get("PUBLIC_URL") or os.environ.get("RENDER_EXTERNAL_URL") or "http://127.0.0.1:%s" % args.port).rstrip("/")
    server = ReviewServer((args.host, args.port), store, ledger, brain, people, qbo.from_environment(os.environ),
                          labs.Labs(public + "/labs/callback"))
    print("QuickBooks sandbox keys: %s" % ("set" if server.qbo else "not set"), flush=True)
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
