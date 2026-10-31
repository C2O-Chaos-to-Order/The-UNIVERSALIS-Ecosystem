"""Validator checks, including negative fixtures that must fail for a stated reason."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from support import (
    build_accepted_without_decision,
    build_altered_expected,
    build_authorization_without_record,
    build_duplicate_id,
    build_executed,
    build_self_credit,
    build_unclassified,
    build_wrong_hash,
    run_validator,
)
from validate_programme import PLAN_EVIDENCE_FIELDS, SIMULATION_PASS_FIELDS


def _failing_check(payload: dict) -> str:
    failed = [item["check"] for item in payload["checks"] if item["outcome"] == "FAIL"]
    return failed[0] if len(failed) == 1 else str(failed)


def _reasons(payload: dict, check: str) -> str:
    for item in payload["checks"]:
        if item["check"] == check:
            return "\n".join(item["reasons"])
    return ""


class ValidatorTests(unittest.TestCase):
    def test_plan_fields_are_required_and_authorization_is_separate(self):
        research = json.loads((ROOT / "schemas" / "research_record.schema.json").read_text(encoding="utf-8"))
        result = json.loads((ROOT / "schemas" / "simulation_result.schema.json").read_text(encoding="utf-8"))
        for field in PLAN_EVIDENCE_FIELDS:
            self.assertIn(field, research["required"], field)
            self.assertIn(field, result["required"], field)
        for field in SIMULATION_PASS_FIELDS:
            self.assertIn(field, result["required"], field)
            self.assertNotIn(field, research["required"], field)
        self.assertIn("evidence_status", research["properties"])
        self.assertIn("authorization_status", research["properties"])
        self.assertNotEqual(
            research["properties"]["evidence_status"],
            research["properties"]["authorization_status"],
        )
        self.assertEqual(
            research["properties"]["authorization_status"]["enum"],
            ["NOT_AUTHORIZED", "AUTHORIZED"],
        )
        requirement = json.loads((ROOT / "schemas" / "requirement_record.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(requirement["properties"]["requirement_id"]["pattern"], r"^ULC-[0-9]{2}-[0-9]{2}$")

    def test_executed_package_passes_all_seven_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = build_executed(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertEqual(code, 0, stderr + "\n" + json.dumps(payload, indent=2))
            self.assertEqual(
                [item["check"] for item in payload["checks"]],
                [
                    "manifest_integrity",
                    "traceability",
                    "execution_evidence",
                    "expectation_discipline",
                    "count_arithmetic",
                    "honest_status",
                    "classification_gate",
                ],
            )
            result = json.loads((package / "results" / "SIM-001.json").read_text(encoding="utf-8"))
            self.assertEqual(result["evidence_status"], "executed")
            self.assertEqual(result["authorization_status"], "NOT_AUTHORIZED")
            self.assertNotEqual(result["authorization_status"], result["evidence_status"])
            self.assertEqual(result["programme_credit"], "CANDIDATE_PENDING_OWNER_REVIEW")

    def test_wrong_hash_fails_manifest_integrity(self):
        self._expect("wrong_hash", build_wrong_hash, "manifest_integrity", "MANIFEST_INTEGRITY: hash mismatch for README.md")

    def test_duplicate_identifier_fails_traceability(self):
        self._expect(
            "duplicate_id",
            build_duplicate_id,
            "traceability",
            "DUPLICATE_IDENTIFIER: SRC-001 appears more than once in sources/source_register.json",
        )

    def test_unclassified_artefact_fails_classification_gate(self):
        self._expect(
            "unclassified",
            build_unclassified,
            "classification_gate",
            "UNCLASSIFIED_ARTEFACT: unclassified artefact notes/stray.txt has no classification",
        )

    def test_altered_expected_outcome_fails_expectation_discipline(self):
        self._expect(
            "altered_expected",
            build_altered_expected,
            "expectation_discipline",
            "EXPECTATION_MISMATCH: result SIM-001 records an expected outcome that does not equal the expected outcome declared in simulations/scenarios.json",
        )

    def test_self_awarded_programme_credit_fails_honest_status(self):
        self._expect(
            "self_credit",
            build_self_credit,
            "honest_status",
            "PROGRAMME_CREDIT_SELF_AWARDED: RES-001 refusing to award programme credit without an explicit owner or reviewer decision record",
        )

    def test_accepted_without_decision_fails_honest_status(self):
        self._expect(
            "accepted_without_decision",
            build_accepted_without_decision,
            "honest_status",
            "EVIDENCE_STATE_WITHOUT_DECISION: RES-001 evidence state 'accepted' requires an explicit owner or reviewer decision record",
        )

    def test_authorization_without_record_fails_honest_status(self):
        self._expect(
            "authorization_without_record",
            build_authorization_without_record,
            "honest_status",
            "AUTHORIZATION_WITHOUT_RECORD: RES-001 authorization_status 'AUTHORIZED' is not the default NOT_AUTHORIZED and no authorization record exists",
        )

    def test_runner_does_not_assign_authorization_from_evidence(self):
        runner = (ROOT / "templates" / "programme" / "simulations" / "run_one.py").read_text(encoding="utf-8")
        self.assertIn('authorization_status = "NOT_AUTHORIZED"', runner)
        self.assertNotIn("authorization_status = evidence_status", runner)
        validator = (ROOT / "tools" / "validate_programme.py").read_text(encoding="utf-8")
        self.assertNotIn("authorization_status = evidence_status", validator)
        self.assertNotRegex(validator, r"authorization_status\"\]\s*=\s*.*evidence_status")

    def test_repository_has_no_four_digit_uni_requirement_ids(self):
        offenders = []
        for path in Path("/workspace").rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".md", ".json", ".csv"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"UNI-\d{4}", text):
                offenders.append(str(path))
        self.assertEqual(offenders, [])

    def _expect(self, _name: str, builder, check: str, reason: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = builder(Path(tmp) / "programme")
            code, payload, stderr = run_validator(package)
            self.assertNotEqual(code, 0)
            self.assertFalse(payload["ok"])
            self.assertEqual(_failing_check(payload), check, stderr + "\n" + json.dumps(payload, indent=2))
            self.assertIn(reason, _reasons(payload, check))


if __name__ == "__main__":
    unittest.main()
