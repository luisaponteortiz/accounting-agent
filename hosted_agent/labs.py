"""A first look at Intuit's own QuickBooks connector server (remote MCP, beta).

Intuit's public Accounting API cannot read a bank feed's unreviewed lines
(see qbo.probe). Intuit's connector server lists bank feed tools. This module
answers one question and nothing more: will that server accept this agent as
a client? It has two steps, kept apart on purpose.

look()      reads the server's public sign-in settings. No sign-in, no
            company, nothing created.
register()  asks Intuit to register this agent as a client. It creates a
            client record at Intuit and nothing else: no sign-in happens and
            no company is touched. Only a person starts it.

Neither step can reach a company's books: there is no sign-in in this build.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

MCP = "https://mcp-nttf.quickbooks.intuit.com/mcp"
RESOURCE_SETTINGS = "https://mcp-nttf.quickbooks.intuit.com/.well-known/oauth-protected-resource"
HOSTS = ("mcp-nttf.quickbooks.intuit.com", "oauth.platform.intuit.com", "accounts.intuit.com")
CLIENT_NAME = "Accounting agent (development build)"


class LabsError(Exception):
    pass


def http(method, url, headers, body=None):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def short(raw, limit=300):
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    return " ".join(text.split())[:limit]


class Labs:
    def __init__(self, redirect_uri, transport=http):
        self.redirect_uri, self.transport = redirect_uri, transport
        self.settings = None       # the authorization server's published settings, after look()
        self.registered = None     # what Intuit answered to register(); the client id stays here

    def _call(self, method, url, headers, body=None):
        if urllib.parse.urlsplit(url).hostname not in HOSTS or not url.startswith("https://"):
            raise LabsError("refused to contact %s: not one of Intuit's three hosts for this connector" % short(url, 80))
        return self.transport(method, url, headers, body)

    def _json(self, url):
        status, _, raw = self._call("GET", url, {"Accept": "application/json"})
        if status != 200:
            raise LabsError("HTTP %s from %s" % (status, urllib.parse.urlsplit(url).hostname))
        return json.loads(raw)

    def look(self):
        steps = []

        def step(name, work):
            try:
                steps.append(dict(step=name, ok=True, said=work()))
            except (LabsError, ValueError, KeyError, IndexError, OSError) as problem:
                steps.append(dict(step=name, ok=False, said=short(str(problem))))
            return steps[-1]["ok"]

        found = {}

        def resource():
            found["resource"] = self._json(RESOURCE_SETTINGS)
            found["issuer"] = found["resource"]["authorization_servers"][0]
            return "sign-in is handled by %s; %d permissions are offered" % (found["issuer"], len(found["resource"].get("scopes_supported", [])))

        def issuer():
            parts = urllib.parse.urlsplit(found["issuer"])
            data = self._json("%s://%s/.well-known/oauth-authorization-server%s" % (parts.scheme, parts.netloc, parts.path))
            self.settings = data
            return "registration %s; sign-in methods %s; client types %s" % (
                "is offered" if data.get("registration_endpoint") else "is NOT offered",
                ", ".join(data.get("grant_types_supported", [])) or "not stated",
                ", ".join(data.get("token_endpoint_auth_methods_supported", [])) or "not stated")

        def knock():
            hello = dict(jsonrpc="2.0", id=1, method="initialize", params=dict(protocolVersion="2025-06-18", capabilities={},
                         clientInfo=dict(name=CLIENT_NAME, version="0")))
            status, headers, raw = self._call("POST", MCP, {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                                              json.dumps(hello).encode())
            challenge = next((v for k, v in headers.items() if k.lower() == "www-authenticate"), "")
            return "HTTP %s without a sign-in; the server asks for: %s" % (status, short(challenge) or short(raw) or "nothing stated")

        if step("Read the connector's public sign-in settings", resource):
            step("Read Intuit's sign-in service settings", issuer)
        step("Knock on the connector without signing in", knock)
        return steps

    def register(self):
        if not self.settings:
            self.look()
        endpoint = (self.settings or {}).get("registration_endpoint")
        if not endpoint:
            raise LabsError("Intuit's sign-in service does not offer registration")
        ask = dict(client_name=CLIENT_NAME, redirect_uris=[self.redirect_uri], grant_types=["authorization_code", "refresh_token"],
                   response_types=["code"], token_endpoint_auth_method="none")
        status, _, raw = self._call("POST", endpoint, {"Content-Type": "application/json", "Accept": "application/json"}, json.dumps(ask).encode())
        try:
            data = json.loads(raw)
        except ValueError:
            data = {}
        accepted = status in (200, 201) and bool(data.get("client_id"))
        if accepted:
            self.registered = data
        return dict(accepted=accepted, status=status,
                    said="Intuit registered this agent as a client." if accepted else short(data.get("error_description") or data.get("error") or raw))
