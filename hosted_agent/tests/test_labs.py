"""Review tests for the first look at Intuit's connector server, with a stand-in for Intuit. No network."""
import json
import unittest

from hosted_agent import labs

ISSUER = "https://oauth.platform.intuit.com/v1/assets/42"


class Intuit:
    def __init__(self, registration="https://accounts.intuit.com/oauth/register/42", answer=(201, {"client_id": "CLIENT-ID-1"})):
        self.calls, self.registration, self.answer = [], registration, answer

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        if url == labs.RESOURCE_SETTINGS:
            return 200, {}, json.dumps(dict(resource="https://mcp-nttf.quickbooks.intuit.com", authorization_servers=[ISSUER], scopes_supported=["a", "b"])).encode()
        if url == "https://oauth.platform.intuit.com/.well-known/oauth-authorization-server/v1/assets/42":
            data = dict(issuer=ISSUER, grant_types_supported=["authorization_code", "refresh_token"], token_endpoint_auth_methods_supported=["none"])
            if self.registration:
                data["registration_endpoint"] = self.registration
            return 200, {}, json.dumps(data).encode()
        if url == labs.MCP:
            return 401, {"WWW-Authenticate": 'Bearer resource_metadata="x", scope="s1 s2"'}, b""
        if url == self.registration:
            return self.answer[0], {}, json.dumps(self.answer[1]).encode()
        return 404, {}, b"not found"


class LabsCase(unittest.TestCase):
    def make(self, **kw):
        self.intuit = Intuit(**kw)
        return labs.Labs("https://agent.example/labs/callback", transport=self.intuit)

    def test_looking_reads_public_settings_and_creates_nothing(self):
        steps = self.make().look()
        self.assertEqual([s["ok"] for s in steps], [True, True, True])
        self.assertIn("registration is offered", steps[1]["said"])
        self.assertIn('HTTP 401', steps[2]["said"])
        self.assertIn('scope="s1 s2"', steps[2]["said"])
        self.assertFalse(any(self.intuit.registration == c[1] for c in self.intuit.calls))     # looking never registers
        self.assertFalse(any("Authorization" in c[2] for c in self.intuit.calls))               # and never carries a sign-in

    def test_registering_asks_for_one_public_client_with_our_callback(self):
        connector = self.make()
        got = connector.register()
        self.assertEqual((got["accepted"], got["status"]), (True, 201))
        self.assertNotIn("CLIENT-ID-1", json.dumps(got))                                        # the id stays on the server
        sent = json.loads([c for c in self.intuit.calls if c[1] == self.intuit.registration][0][3])
        self.assertEqual((sent["redirect_uris"], sent["token_endpoint_auth_method"]), (["https://agent.example/labs/callback"], "none"))

    def test_a_refusal_is_reported_as_intuit_worded_it(self):
        got = self.make(answer=(403, {"error": "access_denied", "error_description": "client registration is restricted"})).register()
        self.assertEqual((got["accepted"], got["status"], got["said"]), (False, 403, "client registration is restricted"))

    def test_without_a_registration_address_nothing_is_asked(self):
        connector = self.make(registration=None)
        with self.assertRaises(labs.LabsError):
            connector.register()

    def test_settings_cannot_send_the_agent_to_another_host(self):
        connector = self.make(registration="https://elsewhere.example/register")
        with self.assertRaises(labs.LabsError):
            connector.register()
        self.assertFalse(any("elsewhere.example" in c[1] for c in self.intuit.calls))


if __name__ == "__main__":
    unittest.main()
