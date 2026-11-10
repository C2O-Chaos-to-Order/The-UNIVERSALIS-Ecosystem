"""Positive, negative, and boundary tests for the public tool/evidence registry."""

from __future__ import annotations

import copy
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from registry.validate import (
    DEFAULT_REPO_ROOT,
    EVIDENCE_SCHEMA_PATH,
    TOOL_SCHEMA_PATH,
    load_json,
    validate_instance,
    validate_registry,
)

REPO_ROOT = DEFAULT_REPO_ROOT
TOOL_001_PATH = REPO_ROOT / "registry" / "tools" / "tool-001.json"
EV_001_PATH = REPO_ROOT / "registry" / "evidence" / "ev-001.json"
EV_002_PATH = REPO_ROOT / "registry" / "evidence" / "ev-002.json"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class RealRegistryTests(unittest.TestCase):
    def test_shipped_registry_validates(self) -> None:
        self.assertEqual(validate_registry(REPO_ROOT), [])

    def test_tool_001_public_fields(self) -> None:
        record = load_json(TOOL_001_PATH)
        self.assertEqual(record["id"], "tool-001")
        self.assertEqual(record["name"], "Engineering Doctor")
        self.assertEqual(record["version"], "0.1.0")
        self.assertEqual(record["status"], "LIMITED")
        self.assertEqual(record["classification"], "PUBLIC_CANDIDATE")
        self.assertEqual(record["owner"], "owner")
        self.assertEqual(record["implementation"]["locator"], "engineering_doctor")
        self.assertEqual(record["evidence_ids"], ["ev-001", "ev-002"])
        self.assertIn("not authorization", record["does_not_authorize"])
        self.assertIn("private adapter", record["private_evidence_note"])
        self.assertNotIn("score", record)
        self.assertNotIn("confidence", record)

    def test_public_evidence_points_only_at_reproducible_sources(self) -> None:
        ev_001 = load_json(EV_001_PATH)
        ev_002 = load_json(EV_002_PATH)
        self.assertEqual(ev_001["kind"], "unittest_suite")
        self.assertEqual(ev_001["locator"]["path"], "engineering_doctor/tests")
        self.assertEqual(ev_001["classification"], "PUBLIC")
        self.assertTrue(ev_001["reproducible"])
        self.assertEqual(ev_002["kind"], "ci_run")
        self.assertEqual(ev_002["locator"]["run_id"], "42900738045")
        self.assertEqual(
            ev_002["locator"]["head_sha"],
            "6824f912af38be1dee963b59e1a2b0d630db0133",
        )
        self.assertTrue(
            ev_002["locator"]["url"].endswith("/actions/runs/42900738045")
        )
        for record in (ev_001, ev_002):
            blob = json.dumps(record)
            self.assertNotIn("score", record)
            self.assertNotIn("confidence", record)
            self.assertNotIn("20261110T210229Z", blob)

    def test_tool_001_locators_exist_and_run(self) -> None:
        record = load_json(TOOL_001_PATH)
        ran = 0
        for locator in record["test_locators"]:
            target = REPO_ROOT / locator["path"]
            self.assertTrue(target.exists(), locator["path"])
            if locator["kind"] == "workflow_file":
                self.assertTrue(target.is_file(), locator["path"])
                continue
            self.assertEqual(locator["kind"], "unittest_dir")
            loader = unittest.TestLoader()
            discovered = loader.discover(
                start_dir=str(target),
                pattern="test_*.py",
                top_level_dir=str(REPO_ROOT),
            )
            suite = _suite_excluding_registry(discovered)
            stream = io.StringIO()
            result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
            self.assertTrue(
                result.wasSuccessful(),
                msg=f"locator {locator['path']} failed:\n{stream.getvalue()}",
            )
            self.assertGreater(result.testsRun, 0)
            ran += result.testsRun
        self.assertGreater(ran, 0)


class SchemaNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool_schema = load_json(TOOL_SCHEMA_PATH)
        cls.evidence_schema = load_json(EVIDENCE_SCHEMA_PATH)
        cls.tool = load_json(TOOL_001_PATH)
        cls.evidence = load_json(EV_001_PATH)

    def test_unknown_field_is_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["unexpected"] = "nope"
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("unknown field" in error for error in errors), errors)

    def test_missing_required_field_is_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        del record["name"]
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("missing required field" in error for error in errors), errors)

    def test_bad_tool_id_is_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["id"] = "tool-01"
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("does not match pattern" in error for error in errors), errors)

    def test_bad_evidence_id_is_rejected(self) -> None:
        record = copy.deepcopy(self.evidence)
        record["id"] = "evidence-001"
        errors = validate_instance(record, self.evidence_schema)
        self.assertTrue(any("does not match pattern" in error for error in errors), errors)

    def test_score_field_is_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["score"] = 0
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(
            any("score" in error and ("not allowed" in error or "unknown field" in error) for error in errors),
            errors,
        )

    def test_confidence_field_is_rejected(self) -> None:
        record = copy.deepcopy(self.evidence)
        record["confidence"] = 0.9
        errors = validate_instance(record, self.evidence_schema)
        self.assertTrue(
            any("confidence" in error for error in errors),
            errors,
        )

    def test_empty_name_is_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["name"] = ""
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("minLength" in error for error in errors), errors)

    def test_empty_test_locators_are_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["test_locators"] = []
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("minItems" in error for error in errors), errors)

    def test_empty_evidence_ids_are_rejected(self) -> None:
        record = copy.deepcopy(self.tool)
        record["evidence_ids"] = []
        errors = validate_instance(record, self.tool_schema)
        self.assertTrue(any("minItems" in error for error in errors), errors)

    def test_non_public_classification_is_rejected(self) -> None:
        record = copy.deepcopy(self.evidence)
        record["classification"] = "UNLISTED"
        errors = validate_instance(record, self.evidence_schema)
        self.assertTrue(any("not in enum" in error for error in errors), errors)


class ReferentialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="registry-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        tests_dir = self.tmp / "engineering_doctor" / "tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_placeholder.py").write_text(
            "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        workflow = self.tmp / ".github" / "workflows"
        workflow.mkdir(parents=True)
        (workflow / "engineering-doctor.yml").write_text("name: dummy\n", encoding="utf-8")
        shutil.copytree(
            REPO_ROOT / "registry" / "schemas",
            self.tmp / "registry" / "schemas",
        )
        self.tool = load_json(TOOL_001_PATH)
        self.ev_001 = load_json(EV_001_PATH)
        self.ev_002 = load_json(EV_002_PATH)
        # The copied CI evidence record does not need a local path; keep it.
        self._write_tree(self.tool, self.ev_001, self.ev_002)

    def _write_tree(
        self,
        tool: dict[str, Any],
        ev_001: dict[str, Any],
        ev_002: dict[str, Any],
    ) -> None:
        _write_json(self.tmp / "registry" / "tools" / f"{tool['id']}.json", tool)
        _write_json(self.tmp / "registry" / "evidence" / f"{ev_001['id']}.json", ev_001)
        _write_json(self.tmp / "registry" / "evidence" / f"{ev_002['id']}.json", ev_002)

    def test_copy_of_records_validates_against_temp_tree(self) -> None:
        self.assertEqual(validate_registry(self.tmp), [])

    def test_missing_evidence_record_is_rejected(self) -> None:
        tool = copy.deepcopy(self.tool)
        tool["evidence_ids"] = ["ev-001", "ev-999"]
        self._write_tree(tool, self.ev_001, self.ev_002)
        errors = validate_registry(self.tmp)
        self.assertTrue(any("ev-999" in error and "missing" in error for error in errors), errors)

    def test_missing_test_locator_is_rejected(self) -> None:
        tool = copy.deepcopy(self.tool)
        tool["test_locators"] = [
            {
                "kind": "unittest_dir",
                "path": "engineering_doctor/tests/does-not-exist",
                "command": "true",
            }
        ]
        self._write_tree(tool, self.ev_001, self.ev_002)
        errors = validate_registry(self.tmp)
        self.assertTrue(
            any("does-not-exist" in error and "missing" in error for error in errors),
            errors,
        )

    def test_evidence_link_to_missing_test_is_rejected(self) -> None:
        ev_001 = copy.deepcopy(self.ev_001)
        ev_001["locator"]["path"] = "engineering_doctor/missing_tests"
        self._write_tree(self.tool, ev_001, self.ev_002)
        errors = validate_registry(self.tmp)
        self.assertTrue(
            any("missing" in error and "missing_tests" in error for error in errors),
            errors,
        )

    def test_filename_id_mismatch_is_rejected(self) -> None:
        path = self.tmp / "registry" / "tools" / "tool-001.json"
        record = copy.deepcopy(self.tool)
        record["id"] = "tool-002"
        _write_json(path, record)
        errors = validate_registry(self.tmp)
        self.assertTrue(any("does not match id" in error for error in errors), errors)


def _suite_excluding_registry(suite: unittest.TestSuite) -> unittest.TestSuite:
    kept = unittest.TestSuite()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            kept.addTests(_suite_excluding_registry(item))
        elif "test_registry" not in item.id():
            kept.addTest(item)
    return kept


if __name__ == "__main__":
    unittest.main()
