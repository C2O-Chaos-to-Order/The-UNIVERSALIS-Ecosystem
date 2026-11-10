"""Fail-closed tests for knowledge records and Rule 1 enforcement."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from foundation.invariant import (
    apply_proposed_update,
    canonical_rule_1_digest,
    canonical_rule_1_text,
    check_capability_authorization_growth,
    check_rule_1_document,
    extract_canonical_text,
    sha256_text,
)
from knowledge.validate import (
    apply_correction,
    iter_record_paths,
    load_json,
    semantic_errors,
    validate_record_data,
    validate_tree,
)

ROOT = Path(__file__).resolve().parents[2]


def shipped_records() -> list[tuple[Path, dict]]:
    items = []
    for path in iter_record_paths(ROOT):
        items.append((path, load_json(path)))
    return items


class KnowledgeRecordTests(unittest.TestCase):
    def test_shipped_records_validate(self) -> None:
        errors = validate_tree(ROOT)
        self.assertEqual(errors, [])
        records = shipped_records()
        self.assertGreaterEqual(len(records), 3)
        for path, record in records:
            with self.subTest(path=path.name):
                self.assertEqual(record["interpretation"]["status"], "proposed")
                self.assertEqual(record["review_status"], "pending")
                self.assertEqual(record["authorization"]["status"], "NOT_AUTHORIZED")
                self.assertFalse(record["authorization"]["inferred_from_test_pass"])
                self.assertEqual(record["interpretation"]["kind"], "interpretation")
                self.assertTrue(record["interpretation"]["not_source_text"])
                self.assertLessEqual(len(record["interpretation"]["principle"]), 280)

    def test_rule_1_document_digest_matches_machine_record(self) -> None:
        self.assertEqual(check_rule_1_document(ROOT), [])
        machine = json.loads((ROOT / "foundation" / "rule_1.json").read_text(encoding="utf-8"))
        self.assertEqual(machine["id"], "RULE-1")
        self.assertEqual(machine["canonical_sha256"], canonical_rule_1_digest(ROOT))

    def test_source_digest_mismatch_is_detected(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["knowledge"]["sources"][0]["sha256"] = "0" * 64
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("sha256" in error for error in errors), errors)

    def test_accepted_without_decision_fails(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["review_status"] = "accepted"
        mutated.pop("decision_record", None)
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("accepted" in error and "decision" in error for error in errors), errors)

    def test_interpretation_cannot_be_marked_as_source_text(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["interpretation"]["kind"] = "source_text"
        mutated["interpretation"]["not_source_text"] = False
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("source text" in error or "interpretation.kind" in error for error in errors), errors)

    def test_authorization_cannot_be_set_from_a_test_pass(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["authorization"] = {
            "status": "AUTHORIZED",
            "inferred_from_test_pass": True,
        }
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("test pass" in error for error in errors), errors)
        self.assertTrue(any("AUTHORIZED" in error and "decision" in error for error in errors), errors)

    def test_correction_keeps_prior_version(self) -> None:
        _, record = shipped_records()[0]
        prior = record["interpretation"]["principle"]
        updated = apply_correction(record, "Corrected paraphrase of the same proposed principle.")
        self.assertEqual(updated["interpretation"]["principle"], "Corrected paraphrase of the same proposed principle.")
        self.assertEqual(len(updated["history"]), len(record.get("history") or []) + 1)
        self.assertEqual(updated["history"][-1]["preserved_principle"], prior)
        self.assertEqual(updated["history"][-1]["reason"], "correction")
        errors = validate_record_data(updated, ROOT, label="corrected")
        self.assertEqual(errors, [])

    def test_omitted_rule_1_is_rejected(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated.pop("rule_1")
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("missing rule_1" in error for error in errors), errors)

    def test_altered_rule_1_text_is_rejected(self) -> None:
        markdown = (ROOT / "foundation" / "RULE_1.md").read_text(encoding="utf-8")
        altered = markdown.replace("Do No Harm", "Do Some Harm")
        self.assertNotEqual(sha256_text(extract_canonical_text(altered)), canonical_rule_1_digest(ROOT))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            foundation = tmp_root / "foundation"
            foundation.mkdir()
            (foundation / "RULE_1.md").write_text(altered, encoding="utf-8")
            machine = json.loads((ROOT / "foundation" / "rule_1.json").read_text(encoding="utf-8"))
            (foundation / "rule_1.json").write_text(json.dumps(machine), encoding="utf-8")
            (foundation / "ASCENDENCE_RESPONSIBILITY.md").write_text(
                (ROOT / "foundation" / "ASCENDENCE_RESPONSIBILITY.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            errors = check_rule_1_document(tmp_root)
            self.assertTrue(any("canonical_sha256" in error for error in errors), errors)

    def test_mismatched_rule_1_digest_on_record_is_rejected(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["rule_1"] = {"id": "RULE-1", "digest": "a" * 64}
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("digest" in error for error in errors), errors)

    def test_proposed_change_that_touches_rule_1_is_rejected(self) -> None:
        _, record = shipped_records()[0]
        proposed = deepcopy(record)
        proposed["rule_1"] = {"id": "RULE-1", "digest": "b" * 64}
        next_state, errors = apply_proposed_update(record, proposed, ROOT, label="mutated")
        self.assertIsNone(next_state)
        self.assertTrue(any("touches RULE-1" in error for error in errors), errors)

    def test_open_protection_is_unaddressed_and_rejected(self) -> None:
        _, record = shipped_records()[0]
        mutated = deepcopy(record)
        mutated["rule_1_assessment"]["protections"][0]["status"] = "open"
        mutated["rule_1_assessment"]["protections"][0].pop("reason", None)
        errors = semantic_errors(mutated, ROOT, label="mutated")
        self.assertTrue(any("open" in error and "unaddressed" in error for error in errors), errors)

    def test_capability_growth_does_not_raise_authorization_alone(self) -> None:
        _, record = shipped_records()[0]
        grown = deepcopy(record)
        grown["capabilities"] = list(record["capabilities"]) + ["new_experimental_capability"]
        self.assertEqual(grown["authorization"]["status"], record["authorization"]["status"])
        self.assertEqual(grown["permissions"], record["permissions"])
        errors = check_capability_authorization_growth(record, grown, label="grown")
        self.assertEqual(errors, [])
        next_state, update_errors = apply_proposed_update(record, grown, ROOT, label="grown")
        self.assertEqual(update_errors, [])
        self.assertIsNotNone(next_state)

        raised = deepcopy(grown)
        raised["authorization"] = {
            "status": "AUTHORIZED",
            "inferred_from_test_pass": False,
        }
        raised_errors = check_capability_authorization_growth(record, raised, label="raised")
        self.assertTrue(any("capability growth" in error for error in raised_errors), raised_errors)

        permitted = deepcopy(grown)
        permitted["permissions"] = list(record["permissions"]) + ["write_external_systems"]
        perm_errors = check_capability_authorization_growth(record, permitted, label="permitted")
        self.assertTrue(any("capability growth" in error for error in perm_errors), perm_errors)

        approved = deepcopy(raised)
        approved["decision_record"] = {
            "kind": "human_authorization",
            "id": "DEC-TEST-001",
            "note": "Synthetic fixture for the capability-growth path.",
        }
        approved["rule_1_assessment"] = deepcopy(record["rule_1_assessment"])
        approved["rule_1_assessment"]["revision"] = int(record["rule_1_assessment"]["revision"]) + 1
        approved["rule_1_assessment"]["reassessed_for"] = "new_experimental_capability"
        approved_errors = check_capability_authorization_growth(record, approved, label="approved")
        self.assertEqual(approved_errors, [])

    def test_working_principle_is_not_in_rule_1_digest(self) -> None:
        canonical = canonical_rule_1_text(ROOT)
        companion = (ROOT / "foundation" / "ASCENDENCE_RESPONSIBILITY.md").read_text(encoding="utf-8")
        self.assertNotIn("Ascendence without responsibility becomes uncontrolled power", canonical)
        self.assertIn("Ascendence without responsibility becomes uncontrolled power", companion)
        self.assertIn(
            "You don't transcend responsibility; you transcend the limitations that prevent you from fulfilling responsibility better.",
            companion,
        )
        machine = json.loads((ROOT / "foundation" / "rule_1.json").read_text(encoding="utf-8"))
        related = machine["related_working_principles"]
        self.assertTrue(related)
        self.assertFalse(related[0]["part_of_canonical_text"])
        self.assertFalse(related[0]["plan_amendment"])
        self.assertEqual(related[0]["phase_axis_mapping"], "interpretation_only")
        markdown = (ROOT / "foundation" / "RULE_1.md").read_text(encoding="utf-8")
        self.assertIn("ASCENDENCE_RESPONSIBILITY.md", markdown)
        self.assertIn("interpretation only", markdown.lower())

    def test_rule_1_honesty_note_present_in_readme(self) -> None:
        readme = (ROOT / "foundation" / "README.md").read_text(encoding="utf-8")
        self.assertIn("does not prove that a tool can never cause harm", readme.lower())
        self.assertIn("Where Rule 1 is enforced", readme)
        self.assertIn("Where Rule 1 is not enforced", readme)
        knowledge_readme = (ROOT / "knowledge" / "README.md").read_text(encoding="utf-8")
        self.assertIn("A pass is not authorization", knowledge_readme)

    def test_principles_are_short_paraphrases(self) -> None:
        for path, record in shipped_records():
            with self.subTest(path=path.name):
                principle = record["interpretation"]["principle"]
                self.assertGreaterEqual(len(principle), 20)
                self.assertLessEqual(len(principle), 280)
                raw = path.read_text(encoding="utf-8")
                self.assertNotIn("# ", principle)
                self.assertLess(len(raw), 20000)


if __name__ == "__main__":
    unittest.main()
