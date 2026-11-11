"""Public-release guard: git-pinned sources must belong to this package's repository.

Scoped to ``--profile public-release`` only. A git-pinned source (commit or
blob_sha present) is refused when its ``repository`` is not the package's
declared ``metadata/programme_status.json`` ``repository``, unless an owner
exception record in ``decisions/`` names that source.

The fixtures are synthetic. They do not cite a real corpus, private
repository, or real commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from package_files import CLASSIFICATION_REL, write_json, write_manifest  # noqa: E402
from support import PROGRAMME_ID, VALIDATOR, build_executed  # noqa: E402

from test_k02_release_profiles import _authorize_release, _check, _run  # noqa: E402

SYNTHETIC_COMMIT = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SYNTHETIC_BLOB = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
PACKAGE_REPO = "synthetic-public-package"
OTHER_REPO = "synthetic-other-repository"
CHECK = "public_source_repository"


def _pin(root: Path, repository: str | None, source_id: str = "SRC-001") -> None:
    path = root / "sources" / "source_register.json"
    sources = json.loads(path.read_text(encoding="utf-8"))
    target = next((source for source in sources if source.get("id") == source_id), None)
    if target is None:
        target = {
            "id": source_id,
            "kind": "fixture",
            "source_role": "other",
            "independence_from": [],
            "review_scope": "Synthetic fixture source. Nothing was reviewed.",
            "release_classification": "PUBLICLY_CLEARED",
        }
        sources.append(target)
    if repository is None:
        target.pop("repository", None)
    else:
        target["repository"] = repository
    target["path"] = "fixtures/synthetic-source.txt"
    target["commit"] = SYNTHETIC_COMMIT
    target["blob_sha"] = SYNTHETIC_BLOB
    write_json(path, sources)


def _declare_package_repo(root: Path, repository: str) -> None:
    path = root / "metadata" / "programme_status.json"
    status = json.loads(path.read_text(encoding="utf-8"))
    status["repository"] = repository
    write_json(path, status)


def _write_exception(
    root: Path,
    source_id: str,
    *,
    authority: str = "owner",
    authorization_status: str | None = "AUTHORIZED",
) -> None:
    decisions = root / "decisions"
    decisions.mkdir(exist_ok=True)
    record = {
        "decision_id": "DEC-SRC-REPO-EXC-001",
        "authority": authority,
        "decided_by": "Owner cited in the decision record (synthetic test fixture)",
        "citation": "decisions/DEC-SRC-REPO-EXC-001.json",
        "target_ids": [source_id],
        "statement": (
            "Synthetic fixture: owner excepts the named source from the "
            "public-release same-repository rule."
        ),
        "release_classification": "PUBLICLY_CLEARED",
    }
    if authorization_status is not None:
        record["authorization_status"] = authorization_status
    write_json(decisions / "DEC-SRC-REPO-EXC-001.json", record)
    classes = json.loads((root / CLASSIFICATION_REL).read_text(encoding="utf-8"))
    classes["decisions/DEC-SRC-REPO-EXC-001.json"] = "PUBLICLY_CLEARED"
    write_json(root / CLASSIFICATION_REL, classes)


def _reasons(payload: dict) -> str:
    return " ".join(_check(payload, CHECK)["reasons"])


class PublicSourceRepositoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="psr-")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _authorized_pinned(self, *, source_repo, package_repo, exception_for=None, authority="owner"):
        root = build_executed(self.tmp / "pkg")
        _pin(root, source_repo)
        if package_repo is not None:
            _declare_package_repo(root, package_repo)
        _authorize_release(root)
        if exception_for is not None:
            _write_exception(root, exception_for, authority=authority)
        write_manifest(root)
        return root

    def test_matching_repository_is_accepted_on_public_release(self):
        root = self._authorized_pinned(source_repo=PACKAGE_REPO, package_repo=PACKAGE_REPO)
        code, payload, stderr = _run(root, "--profile", "public-release")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["release_ready"], True)
        self.assertEqual(_check(payload, CHECK)["outcome"], "PASS")

    def test_other_repository_is_refused_without_exception(self):
        root = self._authorized_pinned(source_repo=OTHER_REPO, package_repo=PACKAGE_REPO)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIs(payload["release_ready"], False)
        self.assertEqual(_check(payload, CHECK)["outcome"], "FAIL")
        reasons = _reasons(payload)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", reasons)
        self.assertIn("SRC-001", reasons)
        self.assertIn(OTHER_REPO, reasons)
        self.assertIn(PACKAGE_REPO, reasons)

    def test_owner_exception_naming_the_source_allows_other_repository(self):
        root = self._authorized_pinned(
            source_repo=OTHER_REPO,
            package_repo=PACKAGE_REPO,
            exception_for="SRC-001",
        )
        code, payload, stderr = _run(root, "--profile", "public-release")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["release_ready"], True)
        self.assertEqual(_check(payload, CHECK)["outcome"], "PASS")

    def test_owner_exception_that_does_not_name_the_source_does_not_allow(self):
        root = self._authorized_pinned(
            source_repo=OTHER_REPO,
            package_repo=PACKAGE_REPO,
            exception_for=PROGRAMME_ID,
        )
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))
        self.assertIn("SRC-001", _reasons(payload))

    def test_owner_exception_marked_not_authorized_does_not_bypass(self):
        root = self._authorized_pinned(
            source_repo=OTHER_REPO,
            package_repo=PACKAGE_REPO,
            exception_for="SRC-001",
        )
        _write_exception(root, "SRC-001", authorization_status="NOT_AUTHORIZED")
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_owner_exception_without_authorization_status_does_not_bypass(self):
        root = self._authorized_pinned(
            source_repo=OTHER_REPO,
            package_repo=PACKAGE_REPO,
            exception_for="SRC-001",
        )
        _write_exception(root, "SRC-001", authorization_status=None)
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_repository_only_locator_is_refused(self):
        root = self._authorized_pinned(source_repo=OTHER_REPO, package_repo=PACKAGE_REPO)
        path = root / "sources" / "source_register.json"
        sources = json.loads(path.read_text())
        sources[0].pop("path", None)
        sources[0].pop("commit", None)
        sources[0].pop("blob_sha", None)
        write_json(path, sources)
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("D09 requires repository, path, commit, and blob_sha together", " ".join(_check(payload, "traceability")["reasons"]))
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_path_only_locator_is_refused(self):
        root = self._authorized_pinned(source_repo=None, package_repo=PACKAGE_REPO)
        path = root / "sources" / "source_register.json"
        sources = json.loads(path.read_text())
        sources[0].pop("repository", None)
        sources[0].pop("commit", None)
        sources[0].pop("blob_sha", None)
        write_json(path, sources)
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("D09 requires repository, path, commit, and blob_sha together", " ".join(_check(payload, "traceability")["reasons"]))
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_repository_and_path_without_git_shas_are_refused(self):
        root = self._authorized_pinned(source_repo=OTHER_REPO, package_repo=PACKAGE_REPO)
        path = root / "sources" / "source_register.json"
        sources = json.loads(path.read_text())
        sources[0].pop("commit", None)
        sources[0].pop("blob_sha", None)
        write_json(path, sources)
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("D09 requires repository, path, commit, and blob_sha together", " ".join(_check(payload, "traceability")["reasons"]))
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_reviewer_record_naming_the_source_is_not_an_owner_exception(self):
        root = self._authorized_pinned(
            source_repo=OTHER_REPO,
            package_repo=PACKAGE_REPO,
            exception_for="SRC-001",
            authority="reviewer",
        )
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", _reasons(payload))

    def test_internal_candidate_profile_does_not_apply_the_guard(self):
        root = build_executed(self.tmp / "internal")
        _pin(root, OTHER_REPO)
        _declare_package_repo(root, PACKAGE_REPO)
        write_manifest(root)
        code, payload, stderr = _run(root, "--profile", "internal-candidate")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["release_ready"], False)
        self.assertNotIn(CHECK, [item["check"] for item in payload["checks"]])

    def test_default_profile_does_not_apply_the_guard(self):
        root = build_executed(self.tmp / "default")
        _pin(root, OTHER_REPO)
        _declare_package_repo(root, PACKAGE_REPO)
        write_manifest(root)
        code, payload, stderr = _run(root)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["release_ready"], False)
        self.assertNotIn(CHECK, [item["check"] for item in payload["checks"]])

    def test_missing_package_repository_refuses_git_pinned_sources(self):
        root = self._authorized_pinned(source_repo=OTHER_REPO, package_repo=None)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        reasons = _reasons(payload)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", reasons)
        self.assertIn("must declare repository", reasons)
        self.assertIn("SRC-001", reasons)

    def test_git_pinned_source_missing_repository_is_refused(self):
        root = self._authorized_pinned(source_repo=None, package_repo=PACKAGE_REPO)
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        reasons = _reasons(payload)
        self.assertIn("PUBLIC_SOURCE_REPOSITORY", reasons)
        self.assertIn("SRC-001", reasons)
        self.assertIn("does not declare a repository", reasons)

    def test_unpinned_source_is_not_checked(self):
        root = build_executed(self.tmp / "unpinned")
        _declare_package_repo(root, PACKAGE_REPO)
        _authorize_release(root)
        write_manifest(root)
        code, payload, stderr = _run(root, "--profile", "public-release")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(_check(payload, CHECK)["outcome"], "PASS")


class PublicSourceRepositoryDocsTests(unittest.TestCase):
    def test_schema_describes_optional_package_repository(self):
        schema = json.loads((ROOT / "schemas" / "programme_status.schema.json").read_text())
        repo = schema["properties"]["repository"]
        self.assertEqual(repo["type"], "string")
        self.assertEqual(repo["minLength"], 1)
        self.assertIn("public-release", repo["description"])
        self.assertIs(schema.get("additionalProperties"), False)

    def test_specification_names_the_public_source_repository_check(self):
        spec = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")
        self.assertIn("`public_source_repository`", spec)
        self.assertIn("owner exception record", spec)

    def test_source_provenance_describes_the_guard(self):
        text = (ROOT / "SOURCE_PROVENANCE.md").read_text(encoding="utf-8")
        self.assertIn("## Public-release source repository", text)
        self.assertIn("corpus-agnostic", text)


class PublicSourceRepositoryMutationTest(unittest.TestCase):
    def test_disabling_the_guard_is_detected(self):
        import validate_programme

        original = validate_programme.check_public_source_repository
        validate_programme.check_public_source_repository = lambda data, reasons: None
        try:
            with tempfile.TemporaryDirectory(prefix="psr-mut-") as tmp:
                root = build_executed(Path(tmp) / "pkg")
                _pin(root, OTHER_REPO)
                _declare_package_repo(root, PACKAGE_REPO)
                _authorize_release(root)
                write_manifest(root)
                mutant = validate_programme.validate(root, profile="public-release")
        finally:
            validate_programme.check_public_source_repository = original
        self.assertTrue(mutant["release_ready"], "mutant should let another repository through")
        with tempfile.TemporaryDirectory(prefix="psr-real-") as tmp:
            root = build_executed(Path(tmp) / "pkg")
            _pin(root, OTHER_REPO)
            _declare_package_repo(root, PACKAGE_REPO)
            _authorize_release(root)
            write_manifest(root)
            real = validate_programme.validate(root, profile="public-release")
        self.assertFalse(real["release_ready"])


if __name__ == "__main__":
    unittest.main()
