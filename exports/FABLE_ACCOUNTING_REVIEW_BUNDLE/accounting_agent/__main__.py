import argparse
import json
import signal
import sys
from pathlib import Path
from .core import ControlError
from .demo import SCOPE, actor, seed
from .service import AccountingOS


def main():
    parser = argparse.ArgumentParser(description="General Accounting Agent OS — local synthetic execution")
    parser.add_argument("command", choices=("setup", "demo", "drain", "inspect", "export", "backup"))
    parser.add_argument("--db", default="data/accounting_demo.sqlite3")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output", default="exports/synthetic-review-package.json")
    args = parser.parse_args()
    os = AccountingOS(args.db, [SCOPE])
    if args.command in ("setup", "demo"):
        ids = seed(os)
        print("Synthetic workflows queued:", ids)
    if args.command == "demo":
        from .http import DemoServer
        server = DemoServer(("127.0.0.1", args.port), os)
        def stop(signum, frame):
            raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM, stop)
        print("Accounting Agent OS: http://127.0.0.1:%s — FICTIONAL LOCAL DEMO" % server.server_port, flush=True)
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    elif args.command == "drain":
        print("Committed/attempted steps:", os.drain(actor("worker")))
    elif args.command == "inspect":
        state = os.state(actor())
        print(json.dumps({"scope": state["scope"], "generation": state["generation"], "runs": [{"id": r["id"], "workflow": r["workflow"], "status": r["status"], "current": r["current"]} for r in state["runs"]], "artifacts": len(state["artifacts"]), "audit_integrity": os.verify_audit(actor()), "external": state["external"]}, indent=2))
    elif args.command == "export":
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(os.export(actor()), indent=2) + "\n")
        print(path.resolve())
    elif args.command == "backup":
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        os.store.backup(path)
        print("Local SQLite backup:", path.resolve())


if __name__ == "__main__":
    try:
        main()
    except ControlError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
