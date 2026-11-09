"""K02 (owner-approved split, 2026-11-08): internal-candidate vs public-release.

Before this change every scaffold schema fixed ``release_classification`` to
``const PUBLICLY_CLEARED``. An uncleared candidate could not be represented
honestly, so packages self-labelled everything ``PUBLICLY_CLEARED`` even when
``metadata/programme_status.json`` said ``release_authorized: false``.

Contract pinned here:

- ``INTERNAL_CANDIDATE`` is a representable classification.
- ``--profile internal-candidate`` accepts ``INTERNAL_CANDIDATE`` (and
  ``PUBLICLY_CLEARED``) and always reports ``release_ready: false``.
- ``--profile public-release`` requires every label to be ``PUBLICLY_CLEARED``
  *and* an owner release authorization: ``release_authorized: true`` plus a
  decision record with ``authority: owner`` and ``authorization_status:
  AUTHORIZED`` citing the programme. Labels alone never make a package
  release-ready. The validator cannot authenticate the owner; it checks that
  the package cites an owner decision, nothing more.
- With no ``--profile`` the historical gate is unchanged (only
  ``PUBLICLY_CLEARED``), and the output says ``release_ready: false``.
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

INTERNAL = "INTERNAL_CANDIDATE"


def _run(package: Path, *profile: str):
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(package), *profile],
        capture_output=True, text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {}
    return proc.returncode, payload, proc.stderr


def _relabel(root: Path, value: str) -> None:
    """Set every file and record classification in the package to ``value``."""
    classes = json.loads((root / CLASSIFICATION_REL).read_text())
    write_json(root / CLASSIFICATION_REL, {name: value for name in classes})
    for path in root.rglob("*.json"):
        rel = path.relative_to(root).as_posix()
        if rel in (CLASSIFICATION_REL, "metadata/sha256_manifest.json"):
            continue
        data = json.loads(path.read_text())
        items = data if isinstance(data, list) else [data]
        changed = False
        for item in items:
            if isinstance(item, dict) and "release_classification" in item:
                item["release_classification"] = value
                changed = True
        if changed:
            write_json(path, data)
    import csv
    import hashlib

    # Cases carry a classification, so the case file's hash lock must follow.
    scenarios = root / "simulations" / "scenarios.json"
    digest = hashlib.sha256(scenarios.read_bytes()).hexdigest()
    for path in (root / "results").glob("*.json"):
        record = json.loads(path.read_text())
        if isinstance(record, dict) and "fixtures_sha256" in record:
            record["fixtures_sha256"] = digest
            write_json(path, record)
    for path in root.rglob("*.csv"):
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = list(reader)
        for row in rows:
            if "release_classification" in row:
                row["release_classification"] = value
            if row.get("fixtures_sha256"):
                row["fixtures_sha256"] = digest
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    write_manifest(root)


def _authorize_release(root: Path, *, authority: str = "owner") -> None:
    status_path = root / "metadata" / "programme_status.json"
    status = json.loads(status_path.read_text())
    status["release_authorized"] = True
    write_json(status_path, status)
    decisions = root / "decisions"
    decisions.mkdir(exist_ok=True)
    write_json(decisions / "DEC-REL-001.json", {
        "decision_id": "DEC-REL-001",
        "state": "authorized",
        "authority": authority,
        "authorization_status": "AUTHORIZED",
        "decided_by": "Owner cited in the decision record (synthetic test fixture)",
        "citation": "decisions/DEC-REL-001.json",
        "target_ids": [PROGRAMME_ID],
        "statement": "Synthetic fixture: owner authorizes public release of this package.",
        "release_classification": "PUBLICLY_CLEARED",
    })
    classes = json.loads((root / CLASSIFICATION_REL).read_text())
    classes["decisions/DEC-REL-001.json"] = "PUBLICLY_CLEARED"
    write_json(root / CLASSIFICATION_REL, classes)
    write_manifest(root)


def _check(payload: dict, name: str) -> dict:
    return next(item for item in payload.get("checks", []) if item["check"] == name)


class K02ReleaseProfilesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="k02-")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_internal_candidate_package_validates_under_internal_profile(self):
        root = build_executed(self.tmp / "pkg")
        _relabel(root, INTERNAL)
        code, payload, stderr = _run(root, "--profile", "internal-candidate")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["profile"], "internal-candidate")
        self.assertIs(payload["release_ready"], False)

    def test_internal_candidate_is_refused_by_default_and_public_release(self):
        root = build_executed(self.tmp / "pkg")
        _relabel(root, INTERNAL)
        for profile in ((), ("--profile", "public-release")):
            with self.subTest(profile=profile):
                code, payload, _ = _run(root, *profile)
                self.assertEqual(code, 1)
                reasons = " ".join(_check(payload, "classification_gate")["reasons"])
                self.assertIn("CLASSIFICATION_GATE", reasons)
                self.assertIs(payload["release_ready"], False)

    def test_unknown_label_is_refused_under_internal_profile(self):
        root = build_executed(self.tmp / "pkg")
        classes = json.loads((root / CLASSIFICATION_REL).read_text())
        classes[next(iter(classes))] = "PRIVATE"
        write_json(root / CLASSIFICATION_REL, classes)
        write_manifest(root)
        code, payload, _ = _run(root, "--profile", "internal-candidate")
        self.assertEqual(code, 1)
        self.assertIn("PRIVATE", " ".join(_check(payload, "classification_gate")["reasons"]))

    def test_public_labels_without_owner_authorization_are_not_release_ready(self):
        root = build_executed(self.tmp / "pkg")
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        reasons = " ".join(_check(payload, "release_authorization")["reasons"])
        self.assertIn("RELEASE_NOT_AUTHORIZED", reasons)
        self.assertIs(payload["release_ready"], False)

    def test_owner_authorized_public_package_is_release_ready(self):
        root = build_executed(self.tmp / "pkg")
        _authorize_release(root)
        code, payload, stderr = _run(root, "--profile", "public-release")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["release_ready"], True)

    def test_reviewer_authorization_is_not_owner_release_authorization(self):
        root = build_executed(self.tmp / "pkg")
        _authorize_release(root, authority="reviewer")
        code, payload, _ = _run(root, "--profile", "public-release")
        self.assertEqual(code, 1)
        self.assertIn("RELEASE_NOT_AUTHORIZED", " ".join(_check(payload, "release_authorization")["reasons"]))

    def test_default_profile_is_unchanged_but_never_release_ready(self):
        root = build_executed(self.tmp / "pkg")
        code, payload, stderr = _run(root)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(payload["profile"], "public-label-consistency")
        self.assertIs(payload["release_ready"], False)
        self.assertNotIn("release_authorization", [c["check"] for c in payload["checks"]])

    def test_schemas_accept_both_classifications_and_nothing_else(self):
        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            schema = json.loads(path.read_text())
            spec = schema["properties"]["release_classification"]
            with self.subTest(schema=path.name):
                self.assertEqual(sorted(spec.get("enum", [])), [INTERNAL, "PUBLICLY_CLEARED"])
                self.assertNotIn("const", spec)


class K02MutationTest(unittest.TestCase):
    def test_disabling_owner_authorization_check_is_detected(self):
        import validate_programme

        original = validate_programme.owner_release_authorized
        validate_programme.owner_release_authorized = lambda status, decisions, programme_id: True
        try:
            with tempfile.TemporaryDirectory(prefix="k02-mut-") as tmp:
                root = build_executed(Path(tmp) / "pkg")
                result = validate_programme.validate(root, profile="public-release")
        finally:
            validate_programme.owner_release_authorized = original
        # The mutant lets an unauthorized package through; the real check must not.
        self.assertTrue(result["release_ready"], "mutant should make the package look release-ready")
        with tempfile.TemporaryDirectory(prefix="k02-real-") as tmp:
            root = build_executed(Path(tmp) / "pkg")
            real = validate_programme.validate(root, profile="public-release")
        self.assertFalse(real["release_ready"])


if __name__ == "__main__":
    unittest.main()
