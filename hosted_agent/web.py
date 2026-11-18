"""The review page and its API. Every request names a person; the page shows
one client at a time; the roster shows names and counts only."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import labs, qbo, review
from .ledger import Books, LedgerError
from .qbo_ledger import QboLedger
from .runner import run_client

PAGE = Path(__file__).parent / "page.html"


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, ledger, brain, people, qbo=None, labs=None):
        """people: {token: {"name": ..., "role": "owner" | "reviewer"}}"""
        self.store, self.brain, self.people, self.qbo, self.labs = store, brain, people, qbo, labs
        self.ledger = Books(ledger) if qbo else ledger     # with QuickBooks keys, the sandbox company's books sit beside the fictional ones
        super().__init__(address, Handler)

    def adopt_sandbox(self, person_name):
        """The connected sandbox company becomes a client of its own, in prepare-only mode, with its own ledger."""
        realm = self.qbo.connection["realm_id"]
        books = QboLedger(self.qbo)
        self.ledger.add(realm, books)
        if not self.store.one("SELECT 1 FROM clients WHERE realm_id=?", (realm,)):
            self.store.add_client("qbo-" + realm, books.company(realm)["name"], realm, actor=person_name)

    def person(self, token):
        for known, person in self.people.items():
            if token and secrets.compare_digest(known, token):
                return person
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "AccountingAgent"

    def log_message(self, *args):
        pass

    def send(self, status, body, kind="application/json", headers=()):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def who(self):
        token = ""
        for part in self.headers.get("Cookie", "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == "agent_session":
                token = value
        bearer = self.headers.get("Authorization", "")
        if bearer.startswith("Bearer "):
            token = bearer[7:]
        return self.server.person(token)

    def do_GET(self):
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        if url.path == "/healthz":
            return self.send(200, {"ok": True})
        if url.path == "/" and "token" in query:
            if not self.server.person(query["token"][0]):
                return self.send(403, b"Unknown sign-in link.", "text/plain")
            cookie = "agent_session=%s; Path=/; HttpOnly; SameSite=Strict" % query["token"][0]
            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", cookie)
            self.end_headers()
            return
        if url.path == "/qbo/callback":
            return self.qbo_callback(query)
        person = self.who()
        if not person:
            return self.send(401, b"Sign in with the link you were given.", "text/plain")
        s = self.server
        try:
            if url.path == "/qbo/connect":
                review.allow(person, "mode")
                if not s.qbo:
                    return self.send(404, b"QuickBooks keys are not set on this service.", "text/plain")
                self.send_response(303)
                self.send_header("Location", s.qbo.authorize_url(person["name"]))
                self.end_headers()
                return
            if url.path == "/api/qbo":
                if not s.qbo:
                    return self.send(200, {"configured": False})
                try:
                    return self.send(200, dict(configured=True, redirect_uri=s.qbo.redirect_uri, **s.qbo.summary()))
                except qbo.QboError as problem:
                    return self.send(200, dict(configured=True, connected=False, error=str(problem)))
            if url.path == "/api/qbo/clearing":
                review.allow(person, "mode")
                if not s.qbo:
                    return self.send(404, {"error": "QuickBooks keys are not set on this service."})
                try:
                    return self.send(200, s.qbo.clearing())
                except qbo.QboError as problem:
                    return self.send(200, {"error": str(problem)})
            if url.path == "/api/qbo/probe":
                review.allow(person, "mode")
                if not s.qbo:
                    return self.send(404, {"error": "QuickBooks keys are not set on this service."})
                try:
                    return self.send(200, {"results": s.qbo.probe()})
                except qbo.QboError as problem:
                    return self.send(200, {"error": str(problem)})
            if url.path == "/api/labs/look":
                review.allow(person, "mode")
                if not s.labs:
                    return self.send(404, {"error": "not available on this service"})
                return self.send(200, {"steps": s.labs.look(), "registered": bool(s.labs.registered)})
            if url.path == "/":
                return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if url.path == "/api/roster":
                brain = dict(name=s.brain.name, calls=getattr(s.brain, "calls", 0), last_error=getattr(s.brain, "last_error", None))
                return self.send(200, {"person": person, "clients": review.roster(s.store), "brain": brain})
            if url.path == "/api/state":
                state = review.state(s.store, query["client"][0])
                try:
                    state["accounts"] = [a["name"] for a in s.ledger.accounts(state["client"]["realm_id"])]
                except LedgerError as problem:
                    state["accounts"], state["books_error"] = [], str(problem)
                return self.send(200, state)
        except review.Refused as no:
            return self.send(403, str(no).encode(), "text/plain")
        except (KeyError, IndexError):
            return self.send(404, {"error": "not found"})
        self.send(404, {"error": "not found"})

    def qbo_callback(self, query):
        """Intuit sends the browser back here. The one-time state, not a cookie, proves who started it."""
        s, first = self.server, lambda name: (query.get(name) or [""])[0]
        if not s.qbo:
            return self.send(404, b"QuickBooks keys are not set on this service.", "text/plain")
        try:
            person = s.qbo.finish(first("state"), first("code"), first("realmId"))
            s.store.audit("-", person, "qbo_sandbox_connected", {"realm_id": s.qbo.connection["realm_id"]})
            s.adopt_sandbox(person)
            message = "QuickBooks sandbox connected. Returning to the agent."
        except (qbo.QboError, LedgerError) as problem:
            message = "QuickBooks was not connected: %s" % problem
        page = '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="2;url=/"><p style="font:16px system-ui;padding:24px">%s</p>' % message
        self.send(200, page.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        person, s = self.who(), self.server
        if not person:
            return self.send(401, {"error": "sign in first"})
        if self.headers.get("X-Requested-With") != "accounting-agent":
            return self.send(403, {"error": "request did not come from the review page"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or 0) or b"{}")
            path = urlsplit(self.path).path
            if path == "/api/decide":
                results = {}
                for proposal_id in body["ids"]:
                    try:
                        results[proposal_id] = review.decide(s.store, s.ledger, person, int(proposal_id), body["verdict"],
                                                             body.get("final_action"), body.get("note", ""))
                    except review.Refused as no:
                        results[proposal_id] = "refused: " + str(no)
                return self.send(200, {"results": results})
            if path == "/api/standing/grant":
                sid = review.grant_standing(s.store, person, body["client"], body["item_class"], body["class_key"],
                                            int(body["max_amount_cents"]), body.get("override_reason", ""))
                review.reroute(s.store, s.ledger, body["client"], post=False)
                return self.send(200, {"standing": sid})
            if path == "/api/standing/end":
                review.end_standing(s.store, person, int(body["id"]), body.get("reason", ""))
                return self.send(200, {"ok": True})
            if path == "/api/mode":
                review.set_mode(s.store, person, body["client"], body["mode"], s.ledger)
                return self.send(200, {"ok": True})
            if path == "/api/qbo/move":
                review.allow(person, "mode")
                if not s.qbo:
                    return self.send(404, {"error": "QuickBooks keys are not set on this service."})
                try:
                    result = s.qbo.move_to_clearing(str(body["line"]), str(body["type"]), str(body["id"]))
                except qbo.QboError as problem:
                    s.store.audit("-", person["name"], "sandbox_move_to_clearing_refused", {"type": str(body["type"]), "id": str(body["id"]), "why": str(problem)})
                    return self.send(200, {"error": str(problem)})
                s.store.audit("-", person["name"], "sandbox_moved_to_clearing", result)
                return self.send(200, result)
            if path == "/api/labs/register":
                review.allow(person, "mode")
                if not s.labs:
                    return self.send(404, {"error": "not available on this service"})
                try:
                    result = s.labs.register()
                except labs.LabsError as problem:
                    result = dict(accepted=False, status=None, said=str(problem))
                s.store.audit("-", person["name"], "intuit_connector_registration_asked", {"accepted": result["accepted"], "status": result["status"]})
                return self.send(200, result)
            if path == "/api/run":
                review.allow(person, "mode")
                return self.send(200, run_client(s.store, s.ledger, s.brain, body["client"]))
        except review.Refused as no:
            return self.send(403, {"error": str(no)})
        except (KeyError, ValueError, TypeError) as bad:
            return self.send(400, {"error": "bad request: %s" % bad})
        self.send(404, {"error": "not found"})
