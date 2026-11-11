"""D09 source-locator format: repository, path, commit, and blob together.

These fixtures are synthetic. They do not cite a real work, manuscript, or
private corpus. Invalid fixtures are written so they fail on the D09 rule they
target, not on a stale locator shape.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from support import build_duplicate_id, build_empty, build_executed, run_validator
from package_files import rebuild_locks, write_json

SCHEMA = json.loads((ROOT / "schemas" / "source_register_entry.schema.json").read_text(encoding="utf-8"))
SPEC = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
PROVENANCE = (ROOT / "SOURCE_PROVENANCE.md").read_text(encoding="utf-8")

SYNTHETIC_COMMIT = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SYNTHETIC_BLOB = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _source(**overrides) -> dict:
    entry = {
        "id": "SRC-FIXTURE-001",
        "kind": "fixture",
        "source_role": "other",
        "independence_from": [],
        "review_scope": "Synthetic fixture. Nothing was reviewed.",
        "release_classification": "PUBLICLY_CLEARED",
    }
    entry.update(overrides)
    return entry


def _pinned(**overrides) -> dict:
    entry = _source(
        repository="example-public-repository",
        path="examples/synthetic_source.txt",
        commit=SYNTHETIC_COMMIT,
        blob_sha=SYNTHETIC_BLOB,
    )
    entry.update(overrides)
    return entry


def _git_pinned(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    return any(obj.get(field) not in (None, "") for field in ("repository", "path", "commit", "blob_sha"))


def _old_format(obj: dict) -> bool:
    return _git_pinned(obj) and not all(
        isinstance(obj.get(field), str) and obj.get(field).strip()
        for field in ("repository", "path", "commit", "blob_sha")
    )


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)


class D09SchemaAndDocsTests(unittest.TestCase):
    def test_schema_documents_repository(self):
        self.assertIn("repository", SCHEMA["properties"])
        spec = SCHEMA["properties"]["repository"]
        self.assertEqual(spec.get("type"), "string")
        self.assertGreaterEqual(spec.get("minLength", 0), 1)
        description = spec.get("description", "").lower()
        self.assertIn("repository that commit belongs to", description)
        self.assertIn("path is relative to that repository", description)

    def test_docs_state_the_four_field_locator(self):
        for document, label in (
            (SPEC, "SPECIFICATION.md"),
            (README, "README.md"),
            (PROVENANCE, "SOURCE_PROVENANCE.md"),
        ):
            with self.subTest(doc=label):
                self.assertIn("`repository`", document)
                self.assertIn("`commit`", document)
                self.assertIn("`blob_sha`", document)
                self.assertIn("repository-relative", document)


class D09ValidationTests(unittest.TestCase):
    def _run(self, sources: list[dict]) -> tuple[int, dict, str]:
        with tempfile.TemporaryDirectory() as tmp:
            package = build_empty(Path(tmp) / "programme")
            write_json(package / "sources" / "source_register.json", sources)
            rebuild_locks(package)
            return run_validator(package)

    def _traceability(self, payload: dict) -> str:
        return "\n".join(
            reason
            for check in payload["checks"]
            if check["check"] == "traceability"
            for reason in check["reasons"]
        )

    def test_a_synthetic_d09_locator_is_accepted(self):
        code, payload, stderr = self._run([_pinned()])
        self.assertEqual(code, 0, stderr + json.dumps(payload, indent=2))

    def test_an_unpinned_source_is_still_accepted(self):
        code, payload, stderr = self._run([_source()])
        self.assertEqual(code, 0, stderr + json.dumps(payload, indent=2))

    def test_a_git_pinned_source_without_repository_is_refused(self):
        entry = _pinned()
        del entry["repository"]
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare a repository", reasons)
        self.assertIn("D09 requires repository, path, commit, and blob_sha together", reasons)

    def test_a_git_pinned_source_without_a_path_is_refused(self):
        entry = _pinned()
        del entry["path"]
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare a path", reasons)
        self.assertIn("D09 requires repository, path, commit, and blob_sha together", reasons)
        self.assertNotIn("does not declare a repository", reasons)

    def test_a_git_pinned_source_without_blob_sha_is_refused(self):
        entry = _pinned()
        del entry["blob_sha"]
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare blob_sha", reasons)
        self.assertNotIn("does not declare a repository", reasons)

    def test_an_invalid_commit_sha_fails_on_the_sha_rule(self):
        # Full D09 shape so the fixture fails for the SHA reason, not a stale format.
        entry = _pinned(commit="not-a-valid-git-sha")
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        sha_reason = (
            "commit does not match the required pattern" in reasons
            or "commit must be a 40-character git SHA or omitted" in reasons
        )
        self.assertTrue(sha_reason, reasons)
        self.assertNotIn("does not declare a repository", reasons)
        self.assertNotIn("does not declare a path", reasons)
        self.assertNotIn("does not declare blob_sha", reasons)

    def test_a_git_pinned_source_without_commit_is_refused(self):
        entry = _pinned()
        del entry["commit"]
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare commit", reasons)
        self.assertNotIn("does not declare repository", reasons)

    def test_repository_without_a_complete_git_locator_is_refused(self):
        entry = _source(repository="example-public-repository")
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare a path", reasons)
        self.assertIn("does not declare commit", reasons)
        self.assertIn("does not declare blob_sha", reasons)

    def test_path_without_a_complete_git_locator_is_refused(self):
        entry = _source(path="examples/synthetic_source.txt")
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("does not declare a repository", reasons)
        self.assertIn("does not declare commit", reasons)
        self.assertIn("does not declare blob_sha", reasons)

    def test_a_non_relative_path_is_refused(self):
        entry = _pinned(path="../outside/synthetic_source.txt")
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("repository-relative path without '..' or a leading '/'", reasons)
        self.assertNotIn("does not declare a repository", reasons)

    def test_an_absolute_path_is_refused(self):
        entry = _pinned(path="/tmp/synthetic_source.txt")
        code, payload, stderr = self._run([entry])
        self.assertNotEqual(code, 0)
        reasons = self._traceability(payload)
        self.assertIn("repository-relative path without '..' or a leading '/'", reasons)


class D09OldFormatRegressionTests(unittest.TestCase):
    """Fails if an old-format locator reappears in a valid fixture."""

    def test_checked_in_json_has_no_old_format_locators(self):
        offenders = []
        for path in REPO.rglob("source_register.json"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            for obj in _walk_dicts(data):
                if _old_format(obj):
                    offenders.append(f"{path.relative_to(REPO)} id={obj.get('id')}")
        self.assertEqual(offenders, [], "old-format git locator (commit/blob without repository)")

    def test_valid_builders_do_not_emit_old_format_locators(self):
        with tempfile.TemporaryDirectory() as tmp:
            packages = [
                build_empty(Path(tmp) / "empty"),
                build_executed(Path(tmp) / "executed"),
                build_duplicate_id(Path(tmp) / "duplicate"),
            ]
            offenders = []
            for package in packages:
                register = json.loads((package / "sources" / "source_register.json").read_text())
                for obj in register:
                    if _old_format(obj):
                        offenders.append(f"{package.name}:{obj.get('id')}")
            self.assertEqual(offenders, [])

    def test_template_source_register_has_no_old_format_locators(self):
        register = json.loads(
            (ROOT / "templates" / "programme" / "sources" / "source_register.json").read_text()
        )
        offenders = [obj.get("id") for obj in register if _old_format(obj)]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
