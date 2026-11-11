
import json
import unittest

from engineering_doctor.github_client import GitHubClient, GitHubError, redact
from engineering_doctor.tests.support import FakeFetch


class GitHubClientTests(unittest.TestCase):
    def test_redact_removes_common_token_shapes(self) -> None:
        token = "ghp_" + ("a" * 36)
        text = f"Authorization: Bearer {token} and leftover"
        self.assertNotIn(token, redact(text, token))
        self.assertIn("<redacted>", redact(text, token))

    def test_get_only_invokes_injected_fetch(self) -> None:
        fake = FakeFetch()
        fake.register("/repos/example/demo", {"name": "demo"})
        client = GitHubClient(token="ghp_" + ("b" * 36), fetch=fake)
        payload, _ = client.get("/repos/example/demo")
        self.assertEqual(payload["name"], "demo")
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("/repos/example/demo", fake.calls[0])

    def test_http_error_is_not_an_empty_list(self) -> None:
        fake = FakeFetch()
        fake.register("/repos/example/demo", {"message": "boom"}, status=500)
        client = GitHubClient(fetch=fake)
        with self.assertRaises(GitHubError) as ctx:
            client.get("/repos/example/demo")
        self.assertEqual(ctx.exception.status, 500)

    def test_pagination_follows_next_link(self) -> None:
        fake = FakeFetch()
        fake.register(
            "/repos/example/demo/pulls",
            [{"number": 1}],
            headers={"Link": '<https://api.github.com/repos/example/demo/pulls?page=2>; rel="next"'},
        )
        fake.register(
            "/repos/example/demo/pulls",
            [{"number": 2}],
        )
        # Second registration overwrites the first if keys collide; use query keys.
        fake.routes.clear()
        fake.register(
            "/repos/example/demo/pulls",
            [{"number": 1}],
            headers={"link": '<https://api.github.com/repos/example/demo/pulls?page=2>; rel="next"'},
        )
        # urlsplit path is the same; FakeFetch uses path only, so this cannot
        # distinguish pages. Use a fetch that keys on the full URL instead.

        seen: list[str] = []

        def fetch(url: str, headers: dict[str, str]):
            seen.append(url)
            if "page=2" in url:
                return 200, {}, json.dumps([{"number": 2}]).encode()
            headers_out = {
                "link": '<https://api.github.com/repos/example/demo/pulls?page=2>; rel="next"'
            }
            return 200, headers_out, json.dumps([{"number": 1}]).encode()

        client = GitHubClient(fetch=fetch)
        items = client.get_paginated("/repos/example/demo/pulls", {"state": "open"})
        self.assertEqual([item["number"] for item in items], [1, 2])
        self.assertEqual(len(seen), 2)

    def test_error_text_does_not_include_token(self) -> None:
        token = "ghp_" + ("c" * 36)

        def fetch(url: str, headers: dict[str, str]):
            return 401, {}, f"bad token {token}".encode()

        client = GitHubClient(token=token, fetch=fetch)
        with self.assertRaises(GitHubError) as ctx:
            client.get("/user")
        self.assertNotIn(token, str(ctx.exception))
