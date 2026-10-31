"""Evidence-state transitions and the separate authorization column."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from evidence_states import (
    EvidenceStateError,
    assert_authorization_status,
    assert_programme_credit,
    authorization_record_supports,
    tooling_set,
    transition,
)


def _decision(**overrides):
    record = {
        "decision_id": "DEC-001",
        "state": "reviewed",
        "authority": "reviewer",
        "decided_by": "Reviewer cited in the decision record",
        "citation": "decisions/DEC-001.json",
        "target_ids": ["RES-001"],
        "statement": "Review recorded for the fixture.",
        "release_classification": "PUBLICLY_CLEARED",
    }
    record.update(overrides)
    return record


class EvidenceStateTests(unittest.TestCase):
    def test_tooling_may_set_execution_states_only(self):
        for state in ("planned", "executed", "failed", "incomplete", "reproduced"):
            self.assertEqual(tooling_set(state), state)
        for state in ("reviewed", "accepted", "authorized"):
            with self.assertRaises(EvidenceStateError) as caught:
                tooling_set(state)
            self.assertIn("explicit owner or reviewer decision record", str(caught.exception))

    def test_illegal_transition_is_named(self):
        with self.assertRaises(EvidenceStateError) as caught:
            transition("planned", "accepted", target_id="RES-001")
        self.assertIn("illegal evidence-state transition: planned -> accepted", str(caught.exception))

    def test_review_requires_a_decision_record(self):
        with self.assertRaises(EvidenceStateError) as caught:
            transition("reproduced", "reviewed", target_id="RES-001")
        self.assertIn("without an explicit", str(caught.exception))
        self.assertEqual(
            transition("reproduced", "reviewed", decision_record=_decision(), target_id="RES-001"),
            "reviewed",
        )

    def test_executed_is_a_legal_tool_transition(self):
        self.assertEqual(transition("planned", "executed"), "executed")

    def test_programme_credit_is_not_self_awarded(self):
        self.assertEqual(assert_programme_credit("NONE"), "NONE")
        self.assertEqual(assert_programme_credit("CANDIDATE_PENDING_OWNER_REVIEW"), "CANDIDATE_PENDING_OWNER_REVIEW")
        with self.assertRaises(EvidenceStateError) as caught:
            assert_programme_credit("AWARDED", target_id="RES-001")
        self.assertIn("without an explicit owner or reviewer decision record", str(caught.exception))

    def test_authorization_is_not_inferred_from_evidence_status(self):
        evidence_only = _decision(
            state="authorized",
            evidence_status="authorized",
            statement="Evidence state only.",
        )
        self.assertFalse(authorization_record_supports(evidence_only, "RES-001"))
        with self.assertRaises(EvidenceStateError) as caught:
            assert_authorization_status("AUTHORIZED", [evidence_only], "RES-001")
        message = str(caught.exception)
        self.assertIn("NOT_AUTHORIZED", message)
        self.assertIn("no authorization record exists", message)
        self.assertEqual(assert_authorization_status("NOT_AUTHORIZED", [evidence_only], "RES-001"), "NOT_AUTHORIZED")

    def test_authorization_requires_its_own_column_on_the_decision(self):
        granted = _decision(
            authorization_status="AUTHORIZED",
            authority="owner",
            decided_by="Owner cited in the decision record",
            statement="Authorization recorded separately from evidence.",
        )
        self.assertTrue(authorization_record_supports(granted, "RES-001"))
        self.assertEqual(assert_authorization_status("AUTHORIZED", [granted], "RES-001"), "AUTHORIZED")
        with self.assertRaises(EvidenceStateError):
            assert_authorization_status("PENDING", [], "RES-001")


if __name__ == "__main__":
    unittest.main()
