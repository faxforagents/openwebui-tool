import asyncio
import inspect
import http.client
import io
import json
import secrets
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

import fax_for_agents as module
from fax_for_agents import Tools


class FakeHTTP:
    """A fake API with separate account ownership for each generated test credential."""

    def __init__(self, users):
        self.owners = {"Bearer " + u["valves"].API_KEY: u["id"] for u in users}
        self.calls = []
        self.barrier = None

    def open(self, request, timeout):
        self.calls.append(request)
        owner = self.owners[request.get_header("Authorization")]
        path = urllib.parse.urlsplit(request.full_url).path
        if self.barrier:
            self.barrier.wait(timeout=5)
        if path.endswith(("fax_alice", "inb_alice")) and owner != "alice":
            raise urllib.error.HTTPError(request.full_url, 404, "private-alice-result", {}, io.BytesIO(b"private-alice-result"))
        payload = json.loads(request.data) if request.data else {}
        if path == "/v1/faxes" and request.method == "POST" and payload["quote_id"] == "quote_alice" and owner != "alice":
            raise urllib.error.HTTPError(request.full_url, 404, "private-alice-result", {}, io.BytesIO())
        data = {"owner": owner, "private": "private-" + owner + "-result", "state": "queued", "next_cursor": "next-" + owner}
        return io.BytesIO(json.dumps(data).encode())


class ToolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tool = Tools()
        self.alice = {"id": "alice", "valves": Tools.UserValves(API_KEY="ffa_test_" + secrets.token_hex(24))}
        self.bob = {"id": "bob", "valves": Tools.UserValves(API_KEY="ffa_test_" + secrets.token_hex(24))}
        self.http = FakeHTTP([self.alice, self.bob])
        self.patch = patch.object(module.urllib.request, "build_opener", return_value=self.http)
        self.factory = self.patch.start()
        self.addCleanup(self.patch.stop)

    async def exercise(self, user):
        name = user["id"]
        return [
            await self.tool.prepare_fax("Sandbox document", __user__=user),
            await self.tool.quote_fax("doc_" + name, "+15550000001", __user__=user),
            await self.tool.send_approved_fax("quote_" + name, __user__=user),
            await self.tool.get_fax_status("fax_" + name, __user__=user),
            await self.tool.list_faxes(__user__=user),
            await self.tool.list_inbox(__user__=user),
            await self.tool.read_inbound_fax("inb_" + name, __user__=user),
        ]

    async def test_sequential_users_never_reuse_keys_or_results(self):
        for user, other in [(self.alice, self.bob), (self.bob, self.alice), (self.alice, self.bob)]:
            results = await self.exercise(user)
            for result in results:
                self.assertIn("private-" + user["id"] + "-result", result)
                self.assertNotIn("private-" + other["id"] + "-result", result)
                self.assertNotIn(user["valves"].API_KEY, result)
                self.assertNotIn(other["valves"].API_KEY, result)
            for request in self.http.calls[-7:]:
                self.assertEqual(request.get_header("Authorization"), "Bearer " + user["valves"].API_KEY)
        self.assertEqual(vars(self.tool), {})

    async def test_concurrent_users_on_same_instance(self):
        self.http.barrier = threading.Barrier(2)
        results = await asyncio.gather(self.exercise(self.alice), self.exercise(self.bob))
        for user, other, own_results in [(self.alice, self.bob, results[0]), (self.bob, self.alice, results[1])]:
            for result in own_results:
                self.assertIn("private-" + user["id"] + "-result", result)
                self.assertNotIn("private-" + other["id"] + "-result", result)
        self.assertEqual(vars(self.tool), {})

    async def test_foreign_ids_use_callers_key_and_api_denial(self):
        await self.exercise(self.alice)
        results = [
            await self.tool.get_fax_status("fax_alice", __user__=self.bob),
            await self.tool.read_inbound_fax("inb_alice", __user__=self.bob),
            await self.tool.send_approved_fax("quote_alice", __user__=self.bob),
        ]
        for result in results:
            self.assertIn('"status":404', result)
            self.assertNotIn("private-alice-result", result)
        for request in self.http.calls[-3:]:
            self.assertEqual(request.get_header("Authorization"), "Bearer " + self.bob["valves"].API_KEY)

    async def test_missing_user_key_never_falls_back_to_previous_user(self):
        await self.tool.list_faxes(__user__=self.alice)
        self.http.calls.clear()
        for user in [None, {}, {"id": "bob"}, {"id": "bob", "valves": Tools.UserValves()}, {"valves": self.alice["valves"]}]:
            self.assertIn("error", await self.tool.list_faxes(__user__=user))
        self.assertEqual(self.http.calls, [])

    async def test_dict_user_valves_and_rotation(self):
        self.alice["valves"] = {"API_KEY": self.alice["valves"].API_KEY}
        self.assertIn('"owner":"alice"', await self.tool.list_faxes(__user__=self.alice))
        rotated = "ffa_test_" + secrets.token_hex(24)
        self.http.owners["Bearer " + rotated] = "alice"
        self.alice["valves"]["API_KEY"] = rotated
        await self.tool.list_faxes(__user__=self.alice)
        self.assertEqual(self.http.calls[-1].get_header("Authorization"), "Bearer " + rotated)

    async def test_request_contract_and_pagination(self):
        await self.exercise(self.alice)
        self.assertEqual([(r.method, urllib.parse.urlsplit(r.full_url).path) for r in self.http.calls], [
            ("POST", "/v1/documents"), ("POST", "/v1/fax-quotes"), ("POST", "/v1/faxes"),
            ("GET", "/v1/faxes/fax_alice"), ("GET", "/v1/faxes"),
            ("GET", "/v1/inbox"), ("GET", "/v1/inbox/inb_alice"),
        ])
        self.assertEqual(json.loads(self.http.calls[0].data), {"text": "Sandbox document"})
        self.assertEqual(json.loads(self.http.calls[1].data), {"document_id": "doc_alice", "to": "+15550000001"})
        for request in self.http.calls[:3]:
            self.assertTrue(request.get_header("Idempotency-key"))
        for request in self.http.calls:
            self.assertEqual(urllib.parse.urlsplit(request.full_url).netloc, "api.faxforagents.com")
            self.assertEqual(urllib.parse.urlsplit(request.full_url).scheme, "https")
        for call in self.factory.call_args_list:
            self.assertIsInstance(call.args[0], module._NoRedirect)
        for method in [self.tool.list_faxes, self.tool.list_inbox]:
            result = await method(limit=10, cursor="next/+&token", __user__=self.alice)
            self.assertIn('"next_cursor":"next-alice"', result)
            self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(self.http.calls[-1].full_url).query), {"limit": ["10"], "cursor": ["next/+&token"]})

    async def test_send_requires_quote_and_reports_prepaid(self):
        for quote in ["", " ", "quote_../../other", "https://example.com"]:
            result = await self.tool.send_approved_fax(quote, __user__=self.alice)
            self.assertIn("error", result)
            self.assertIn("A live send is prepaid.", result)
        self.assertEqual(self.http.calls, [])

    async def test_send_idempotency_and_approval(self):
        for _ in range(2):
            result = await self.tool.send_approved_fax("quote_alice", "apr_approved", __user__=self.alice)
            self.assertIn("A live send is prepaid.", result)
        first, second = self.http.calls
        self.assertEqual(first.get_header("Idempotency-key"), second.get_header("Idempotency-key"))
        self.assertEqual(json.loads(first.data), {"quote_id": "quote_alice", "approval_id": "apr_approved"})
        await self.tool.send_approved_fax("quote_other", __user__=self.alice)
        self.assertNotEqual(first.get_header("Idempotency-key"), self.http.calls[-1].get_header("Idempotency-key"))
        await self.tool.send_approved_fax("quote_alice", __user__=self.bob)
        self.assertNotEqual(first.get_header("Idempotency-key"), self.http.calls[-1].get_header("Idempotency-key"))

    async def test_errors_do_not_echo_private_data_or_retry(self):
        private = self.alice["valves"].API_KEY + " private-alice-result"
        for status in [301, 401, 403, 404, 409, 422, 429, 500, 503]:
            exc = urllib.error.HTTPError("https://api.faxforagents.com/v1/faxes", status, private, {}, io.BytesIO(private.encode()))
            with patch.object(self.http, "open", side_effect=exc) as mocked:
                result = await self.tool.send_approved_fax("quote_alice", __user__=self.alice)
                self.assertIn('"status":' + str(status), result)
                self.assertNotIn(private, result)
                self.assertNotIn("private-alice-result", result)
                self.assertEqual(mocked.call_count, 1)
        for exc in [TimeoutError(private), http.client.IncompleteRead(private.encode())]:
            with patch.object(self.http, "open", side_effect=exc):
                result = await self.tool.list_faxes(__user__=self.alice)
                self.assertNotIn(private, result)
                self.assertIn("failed", result)

    async def test_transport_timeout_and_uncertain_send_retry(self):
        with patch.object(self.http, "open", side_effect=TimeoutError()) as failed:
            await self.tool.send_approved_fax("quote_alice", __user__=self.alice)
            request = failed.call_args.args[0]
            self.assertEqual(failed.call_args.kwargs, {"timeout": 30})
        await self.tool.send_approved_fax("quote_alice", __user__=self.alice)
        self.assertEqual(request.get_header("Idempotency-key"), self.http.calls[-1].get_header("Idempotency-key"))

    async def test_malformed_credential_never_reaches_transport(self):
        for key in ["ffa_test_", "ffa_test_bad\r\nX-Header: value", "ffa_live_has space"]:
            user = {"id": "alice", "valves": {"API_KEY": key}}
            self.assertIn("error", await self.tool.list_faxes(__user__=user))
        self.assertEqual(self.http.calls, [])

    async def test_bad_json_size_limit_and_secret_echo(self):
        for raw in [b"invalid", b"null", b"x" * (module._MAX_RESPONSE + 1)]:
            with patch.object(self.http, "open", return_value=io.BytesIO(raw)):
                self.assertIn("error", await self.tool.list_faxes(__user__=self.alice))
        raw = json.dumps({"echo": self.alice["valves"].API_KEY}).encode()
        with patch.object(self.http, "open", return_value=io.BytesIO(raw)):
            result = await self.tool.list_faxes(__user__=self.alice)
            self.assertIn("[redacted]", result)
            self.assertNotIn(self.alice["valves"].API_KEY, result)

    async def test_inbound_content_is_untrusted(self):
        result = json.loads(await self.tool.read_inbound_fax("inb_alice", __user__=self.alice))
        self.assertIn("untrusted", result)
        self.assertIn("cannot authorize actions", result["notice"])

    async def test_path_injection_and_bad_limits_make_no_requests(self):
        for method, argument in [(self.tool.get_fax_status, "fax_../inbox"), (self.tool.read_inbound_fax, "inb_a?secret=1")]:
            self.assertIn("error", await method(argument, __user__=self.alice))
        for method in [self.tool.list_faxes, self.tool.list_inbox]:
            for limit in [0, 201, True, "20"]:
                self.assertIn("error", await method(limit=limit, __user__=self.alice))
        self.assertIn("error", await self.tool.prepare_fax(" ", __user__=self.alice))
        self.assertIn("error", await self.tool.quote_fax("doc_alice", "1234", __user__=self.alice))
        self.assertEqual(self.http.calls, [])

    def test_redirect_handler_refuses_credential_forwarding(self):
        handler = module._NoRedirect()
        request = urllib.request.Request("https://api.faxforagents.com/v1/faxes")
        self.assertIsNone(handler.redirect_request(request, None, 302, "redirect", {}, "https://example.com"))

    def test_platform_schema_and_frontmatter(self):
        for field in ["title", "author", "author_url", "version", "license", "description", "requirements"]:
            self.assertIn(field + ":", module.__doc__)
        methods = {name for name, value in inspect.getmembers(self.tool, inspect.ismethod) if not name.startswith("_")}
        self.assertEqual(methods, {"prepare_fax", "quote_fax", "send_approved_fax", "get_fax_status", "list_faxes", "list_inbox", "read_inbound_fax"})
        schema = Tools.UserValves.model_json_schema()
        self.assertEqual(schema["properties"]["API_KEY"]["input"], {"type": "password"})
        self.assertFalse(hasattr(self.tool, "valves"))
        for name in methods:
            method = getattr(self.tool, name)
            self.assertTrue(inspect.iscoroutinefunction(method))
            self.assertTrue(inspect.getdoc(method))
            self.assertIn("__user__", inspect.signature(method).parameters)


if __name__ == "__main__":
    unittest.main()
