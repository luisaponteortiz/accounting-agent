"""The review page and its API. Every request names a person; the page shows
one client at a time; the roster shows names and counts only."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import review
from .runner import run_client

PAGE = Path(__file__).parent / "page.html"


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, ledger, brain, people):
        """people: {token: {"name": ..., "role": "owner" | "reviewer"}}"""
        self.store, self.ledger, self.brain, self.people = store, ledger, brain, people
        super().__init__(address, Handler)

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
        person = self.who()
        if not person:
            return self.send(401, b"Sign in with the link you were given.", "text/plain")
        s = self.server
        try:
            if url.path == "/":
                return self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if url.path == "/api/roster":
                return self.send(200, {"person": person, "clients": review.roster(s.store)})
            if url.path == "/api/state":
                state = review.state(s.store, query["client"][0])
                state["accounts"] = [a["name"] for a in s.ledger.accounts(state["client"]["realm_id"])]
                return self.send(200, state)
        except (KeyError, IndexError):
            return self.send(404, {"error": "not found"})
        self.send(404, {"error": "not found"})

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
            if path == "/api/run":
                review.allow(person, "mode")
                return self.send(200, run_client(s.store, s.ledger, s.brain, body["client"]))
        except review.Refused as no:
            return self.send(403, {"error": str(no)})
        except (KeyError, ValueError, TypeError) as bad:
            return self.send(400, {"error": "bad request: %s" % bad})
        self.send(404, {"error": "not found"})
