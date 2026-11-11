
import base64
import json
import unittest

from engineering_doctor.github_client import GitHubClient
from engineering_doctor.inventory import findings_from_inventory, inventory_repo


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _json(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


class InventoryTests(unittest.TestCase):
    def test_empty_repo_is_empty_not_unknown(self) -> None:
        def fetch(url: str, headers: dict[str, str]):
            if url.endswith("/example-empty"):
                return 200, {}, _json({
                    "name": "example-empty",
                    "default_branch": "main",
                    "private": False,
                    "html_url": "https://example.test/x",
                })
            if "git/ref/heads/main" in url:
                return 409, {}, b'{"message":"Git Repository is empty."}'
            if url.endswith("/pulls") or "pulls?" in url:
                return 200, {}, b"[]"
            return 404, {}, b"{}"

        client = GitHubClient(fetch=fetch)
        repo = inventory_repo(client, "example-empty", include_readme_tree=True, compare_behind=False)
        self.assertTrue(repo.empty)
        self.assertEqual(repo.open_pr_count, 0)
        self.assertEqual(repo.query_status, "ok")

    def test_api_failure_is_unknown_not_pass(self) -> None:
        def fetch(url: str, headers: dict[str, str]):
            return 502, {}, b'{"message":"unavailable"}'

        client = GitHubClient(fetch=fetch)
        repo = inventory_repo(client, "example-public", compare_behind=False)
        self.assertEqual(repo.query_status, "UNKNOWN")
        self.assertIsNone(repo.open_pr_count)
        findings = findings_from_inventory([repo])
        self.assertEqual(findings[0].severity, "High")
        self.assertIn("UNKNOWN", findings[0].title)

    def test_stacked_pr_without_checks_is_high(self) -> None:
        readme = "# Demo\n"
        tree = {"sha": "abc", "tree": [{"path": "README.md", "type": "blob"}], "truncated": False}

        def fetch(url: str, headers: dict[str, str]):
            if url.endswith("/example-public") and "/git/" not in url and "/pulls" not in url and "/readme" not in url:
                return 200, {}, _json({
                    "name": "example-public",
                    "default_branch": "main",
                    "private": False,
                    "html_url": "https://example.test/uni",
                })
            if "git/ref/heads/main" in url:
                return 200, {}, _json({"object": {"sha": "abc123def456"}})
            if "/pulls" in url:
                return 200, {}, _json([
                    {
                        "number": 6,
                        "title": "stacked",
                        "draft": True,
                        "state": "open",
                        "html_url": "https://example.test/pull/6",
                        "created_at": "2026-11-01T12:00:00Z",
                        "updated_at": "2026-11-02T12:00:00Z",
                        "head": {"ref": "feature", "sha": "fff111"},
                        "base": {"ref": "other-pr-branch"},
                    }
                ])
            if "compare/" in url:
                return 200, {}, _json({"behind_by": 4, "ahead_by": 2})
            if url.endswith("/check-runs") or "check-runs" in url:
                return 200, {}, _json({"check_runs": []})
            if url.endswith("/status") or url.rsplit("/", 1)[-1] == "status":
                return 200, {}, _json({"state": "pending"})
            if url.endswith("/readme"):
                return 200, {}, _json({"encoding": "base64", "content": _b64(readme)})
            if "/git/trees/" in url:
                return 200, {}, _json(tree)
            return 404, {}, b"{}"

        client = GitHubClient(fetch=fetch)
        repo = inventory_repo(client, "example-public")
        self.assertEqual(repo.open_pr_count, 1)
        self.assertEqual(repo.draft_pr_count, 1)
        self.assertTrue(repo.pull_requests[0].stacked)
        self.assertEqual(repo.pull_requests[0].behind_by, 4)
        findings = findings_from_inventory([repo])
        stacked = [item for item in findings if item.finding_id.startswith("STK")]
        self.assertEqual(len(stacked), 1)
        self.assertEqual(stacked[0].severity, "High")
