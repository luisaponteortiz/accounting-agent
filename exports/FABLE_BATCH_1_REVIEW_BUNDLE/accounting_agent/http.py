"""Loopback-only demo UI; explicitly unsuitable for hosted use."""
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from urllib.parse import urlsplit
from .core import ControlError, canonical, require_keys
from .demo import actor, load

WEB = Path(__file__).parent / "web"


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, os, background=True):
        if address[0] != "127.0.0.1":
            raise ControlError("Local demo may bind only to 127.0.0.1", 403)
        self.os = os
        self.tokens = {secrets.token_urlsafe(32): actor(role) for role in ("preparer", "reviewer")}
        self.stop_event = Event()
        self.worker_thread = None
        self.worker_error = False
        super().__init__(address, Handler)
        if background:
            self.worker_thread = Thread(target=self.work, daemon=True)
            self.worker_thread.start()

    def work(self):
        while not self.stop_event.is_set():
            try:
                self.os.work_once(actor("worker"))
            except Exception:
                self.worker_error = True
                break
            self.stop_event.wait(0.1)

    def server_close(self):
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, fmt, *args):
        pass

    def send(self, status, value, content_type="application/json", download=False):
        data = canonical(value).encode() if content_type == "application/json" else value
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="synthetic-accounting-review.json"')
        self.end_headers()
        self.wfile.write(data)

    def boundary(self):
        port = self.server.server_port
        hosts = {"127.0.0.1:" + str(port), "localhost:" + str(port)}
        host = self.headers.get("Host", "")
        if host not in hosts:
            raise ControlError("Host denied", 403)
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + host:
            raise ControlError("Cross-origin request denied", 403)
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise ControlError("Cross-site request denied", 403)

    def identity(self):
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        who = self.server.tokens.get(token)
        if who is None:
            raise ControlError("Local demo session required", 401)
        return who

    def do_GET(self):
        self.handle_request(False)

    def do_POST(self):
        self.handle_request(True)

    def handle_request(self, mutate):
        try:
            self.boundary()
            path = urlsplit(self.path).path
            if urlsplit(self.path).query:
                raise ControlError("Query scope overrides are not supported")
            if not mutate and path in ("/", "/app.js", "/style.css"):
                name, kind = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}[path]
                self.send(200, (WEB / name).read_bytes(), kind)
                return
            if not mutate and path == "/health":
                self.send(200, {"application": "degraded" if self.server.worker_error else "ready", "worker_ready": bool(self.server.worker_thread and self.server.worker_thread.is_alive()), "environment": "local", "mode": "demo", "ledger": "unconnected", "models": "disabled", "hosting_ready": False})
                return
            if not mutate and path == "/api/session":
                self.send(200, {"synthetic": True, "sessions": [{"token": t, "role": a.role} for t, a in self.server.tokens.items()]})
                return
            who = self.identity()
            if not mutate and path == "/api/state":
                self.send(200, self.server.os.state(who))
                return
            if not mutate and path == "/api/export":
                self.send(200, self.server.os.export(who), download=True)
                return
            if not mutate:
                raise ControlError("Accounting-only route not found", 404)
            if self.headers.get("Content-Type") != "application/json":
                raise ControlError("JSON content type required", 415)
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024 * 1024:
                raise ControlError("Request size limit", 413)
            body = json.loads(self.rfile.read(length))
            if path == "/api/run":
                require_keys(body, {"workflow"}, {"period_id"})
                result = {"run_id": self.server.os.enqueue(who, body["workflow"], body.get("period_id"))}
            elif path == "/api/periods/open":
                require_keys(body,{"period_id","start","end","reason"})
                result={"period_id":self.server.os.open_period(who,**body)}
            elif path in ("/api/periods/lock","/api/periods/reopen"):
                require_keys(body,{"period_id","reason"})
                operation=self.server.os.lock_period if path.endswith('/lock') else self.server.os.reopen_period
                operation(who,**body);result={"saved":True}
            elif path == "/api/intake":
                result = self.server.os.intake(who, body)
            elif path == "/api/demo/late-receipt":
                require_keys(body, set())
                result = self.server.os.intake(who, load("fixtures/late_receipt.json"))
            elif path == "/api/review":
                require_keys(body, {"artifact_id", "artifact_hash", "fingerprint", "decision", "reason"})
                self.server.os.review(who, **body)
                result = {"saved": True, "authority": "preparation_only"}
            elif path == "/api/mandates":
                require_keys(body, {"workflows", "starts", "ends", "interval_seconds", "max_occurrences"})
                result = {"mandate_id": self.server.os.create_mandate(who, **body)}
            elif path == "/api/mandates/revoke":
                require_keys(body, {"mandate_id"})
                self.server.os.revoke_mandate(who, body["mandate_id"])
                result = {"revoked": True}
            elif path == "/api/simulate-event":
                require_keys(body, {"now"})
                result = {"run_ids": self.server.os.tick(who, body["now"])}
            else:
                raise ControlError("Accounting-only route not found", 404)
            self.send(200, result)
        except ControlError as exc:
            self.send(exc.status, {"error": str(exc)})
        except (ValueError, TypeError, KeyError, AttributeError):
            self.send(400, {"error": "Invalid request shape or value"})
        except Exception:
            self.send(500, {"error": "Internal error; preserve evidence and contact technical support"})
