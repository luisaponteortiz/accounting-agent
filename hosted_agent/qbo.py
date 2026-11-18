"""Connection to a QuickBooks Online SANDBOX company. Read-only in this build.

Endpoints are Intuit's published ones (discovery document
developer.api.intuit.com/.well-known/openid_sandbox_configuration). The API
host is the sandbox host and nothing else: this module has no way to reach a
real company's books. Tokens stay in this process and are never logged, sent
to the page, or written to the audit trail.
"""
import base64
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

AUTHORIZE = "https://appcenter.intuit.com/connect/oauth2"
TOKEN = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API = "https://sandbox-quickbooks.api.intuit.com"   # sandbox only, on purpose
SCOPE = "com.intuit.quickbooks.accounting"
MINOR_VERSION = "75"
STATE_SECONDS = 600


class QboError(Exception):
    pass


def http(method, url, headers, body=None):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


class Qbo:
    def __init__(self, client_id, client_secret, redirect_uri, transport=http, clock=time.time):
        self.client_id, self.client_secret, self.redirect_uri = client_id, client_secret, redirect_uri
        self.transport, self.clock = transport, clock
        self.states = {}       # state -> (person name, expiry)
        self.connection = None  # one sandbox company at a time in this build

    # -- sign-in with Intuit ------------------------------------------------
    def authorize_url(self, person_name):
        state = secrets.token_urlsafe(24)
        self.states[state] = (person_name, self.clock() + STATE_SECONDS)
        query = urllib.parse.urlencode(dict(client_id=self.client_id, response_type="code", scope=SCOPE,
                                            redirect_uri=self.redirect_uri, state=state))
        return AUTHORIZE + "?" + query

    def finish(self, state, code, realm_id):
        """The browser came back from Intuit. The state proves it is the sign-in this service started."""
        person, expiry = self.states.pop(state, (None, 0))
        if not person or self.clock() > expiry:
            raise QboError("this sign-in link is unknown, already used or expired; start again from the page")
        if not code or not realm_id:
            raise QboError("Intuit did not return a company; the connection was not approved")
        tokens = self._token(dict(grant_type="authorization_code", code=code, redirect_uri=self.redirect_uri))
        self.connection = dict(realm_id=str(realm_id), connected_by=person, connected_at=int(self.clock()), **tokens)
        return person

    def _token(self, form):
        basic = base64.b64encode(("%s:%s" % (self.client_id, self.client_secret)).encode()).decode()
        status, raw = self.transport("POST", TOKEN, {"Authorization": "Basic " + basic, "Accept": "application/json",
                                     "Content-Type": "application/x-www-form-urlencoded"}, urllib.parse.urlencode(form).encode())
        if status != 200:
            raise QboError("Intuit refused the sign-in (HTTP %s)" % status)
        data = json.loads(raw)
        return dict(access_token=data["access_token"], refresh_token=data["refresh_token"],
                    expires_at=self.clock() + int(data.get("expires_in", 3600)) - 60)

    # -- reads ------------------------------------------------------------
    def _get(self, path, params=None):
        c = self.connection
        if not c:
            raise QboError("no QuickBooks sandbox company is connected")
        if self.clock() >= c["expires_at"]:
            c.update(self._token(dict(grant_type="refresh_token", refresh_token=c["refresh_token"])))
        query = urllib.parse.urlencode(dict(params or {}, minorversion=MINOR_VERSION))
        url = "%s/v3/company/%s/%s?%s" % (API, c["realm_id"], path, query)
        status, raw = self.transport("GET", url, {"Authorization": "Bearer " + c["access_token"], "Accept": "application/json"})
        if status != 200:
            raise QboError("QuickBooks answered HTTP %s for %s" % (status, path.split("/")[0]))
        return json.loads(raw)

    def query(self, statement):
        return self._get("query", {"query": statement}).get("QueryResponse", {})

    def summary(self):
        """What the sandbox company holds, as proof the connection reads the books. No tokens."""
        c = self.connection
        if not c:
            return dict(connected=False)
        info = self._get("companyinfo/" + c["realm_id"])["CompanyInfo"]
        count = lambda entity: self.query("select count(*) from " + entity).get("totalCount", 0)
        purchases = self.query("select * from Purchase orderby TxnDate desc maxresults 5").get("Purchase", [])
        recent = [dict(date=p.get("TxnDate"), amount=p.get("TotalAmt"), payee=(p.get("EntityRef") or {}).get("name"),
                       paid_from=(p.get("AccountRef") or {}).get("name"),
                       category=next((l.get("AccountBasedExpenseLineDetail", {}).get("AccountRef", {}).get("name")
                                      for l in p.get("Line", []) if l.get("AccountBasedExpenseLineDetail")), None))
                  for p in purchases]
        return dict(connected=True, environment="sandbox", company=info.get("CompanyName"), realm_id=c["realm_id"],
                    connected_by=c["connected_by"], accounts=count("Account"), vendors=count("Vendor"),
                    customers=count("Customer"), purchases=count("Purchase"), bills=count("Bill"),
                    invoices=count("Invoice"), recent_purchases=recent)


def from_environment(environ):
    if not environ.get("INTUIT_CLIENT_ID") or not environ.get("INTUIT_CLIENT_SECRET"):
        return None
    base = (environ.get("PUBLIC_URL") or environ.get("RENDER_EXTERNAL_URL") or "http://127.0.0.1:8770").rstrip("/")
    return Qbo(environ["INTUIT_CLIENT_ID"], environ["INTUIT_CLIENT_SECRET"], base + "/qbo/callback")
