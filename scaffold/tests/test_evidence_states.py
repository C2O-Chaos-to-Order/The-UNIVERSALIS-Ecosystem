"""Evidence states, the separate execution-outcome axis, and authorization."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from evidence_states import (
    DECISION_REQUIRED,
    EXECUTION_OUTCOMES,
    STATES,
    TOOL_SETTABLE,
    EvidenceStateError,
    assert_authorization_status,
    assert_programme_credit,
    authorization_record_supports,
    cross_axis_problems,
    tooling_set,
    transition,
)

# The governing Plan's eight evidence states, in Plan order (Plan section 7).
PLAN_STATES = (
    "proposed",
    "documented",
    "implemented",
    "tested",
    "verified",
    "independently_reproduced",
    "validated",
    "authorized",
)


def _decision(**overrides):
    record = {
        "decision_id": "DEC-001",
        "state": "verified",
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
    def test_ladder_is_the_plan_vocabulary_in_plan_order(self):
        self.assertEqual(STATES, PLAN_STATES)
        # The retired scaffold ladder must not survive anywhere in the tuple.
        for retired in ("planned", "executed", "reproduced", "reviewed", "accepted"):
            self.assertNotIn(retired, STATES)

    def test_states_and_execution_outcomes_do_not_share_a_value(self):
        self.assertEqual(
            set(EXECUTION_OUTCOMES), {"not_executed", "executed", "failed", "incomplete"}
        )
        self.assertFalse(set(STATES) & set(EXECUTION_OUTCOMES))

    def test_tooling_may_set_only_the_four_pre_verification_states(self):
        self.assertEqual(
            TOOL_SETTABLE, frozenset({"proposed", "documented", "implemented", "tested"})
        )
        for state in ("proposed", "documented", "implemented", "tested"):
            self.assertEqual(tooling_set(state), state)
        for state in ("verified", "independently_reproduced", "validated", "authorized"):
            with self.assertRaises(EvidenceStateError) as caught:
                tooling_set(state)
            self.assertIn("explicit owner or reviewer decision record", str(caught.exception))

    def test_tooling_refuses_an_execution_outcome_as_an_evidence_state(self):
        for outcome in ("executed", "failed", "incomplete", "not_executed"):
            with self.assertRaises(EvidenceStateError) as caught:
                tooling_set(outcome)
            self.assertIn("execution outcome, not an evidence state", str(caught.exception))

    def test_illegal_transition_is_named(self):
        with self.assertRaises(EvidenceStateError) as caught:
            transition("proposed", "implemented", target_id="RES-001")
        self.assertIn(
            "illegal evidence-state transition: proposed -> implemented",
            str(caught.exception),
        )

    def test_no_demotion_edge_exists(self):
        with self.assertRaises(EvidenceStateError) as caught:
            transition("tested", "documented", target_id="RES-001")
        self.assertIn(
            "illegal evidence-state transition: tested -> documented", str(caught.exception)
        )

    def test_each_forward_step_is_the_only_edge(self):
        high = _decision(state="authorized")
        for index, state in enumerate(PLAN_STATES[:-1]):
            target = PLAN_STATES[index + 1]
            if target in DECISION_REQUIRED:
                self.assertEqual(
                    transition(state, target, decision_record=high, target_id="RES-001"),
                    target,
                )
            else:
                self.assertEqual(transition(state, target), target)
        # Every non-adjacent pair is illegal, in both directions.
        for current in PLAN_STATES:
            for target in PLAN_STATES:
                if target == current:
                    continue
                if PLAN_STATES.index(target) == PLAN_STATES.index(current) + 1:
                    continue
                with self.assertRaises(EvidenceStateError) as caught:
                    transition(
                        current, target, decision_record=high, target_id="RES-001"
                    )
                self.assertIn("illegal evidence-state transition", str(caught.exception))

    def test_verified_requires_a_decision_record(self):
        with self.assertRaises(EvidenceStateError) as caught:
            transition("tested", "verified", target_id="RES-001")
        self.assertIn("without an explicit", str(caught.exception))
        self.assertEqual(
            transition("tested", "verified", decision_record=_decision(), target_id="RES-001"),
            "verified",
        )

    def test_every_decision_gated_state_is_in_the_decision_set(self):
        self.assertEqual(
            DECISION_REQUIRED,
            frozenset({"verified", "independently_reproduced", "validated", "authorized"}),
        )

    def test_decision_state_covers_lower_decision_states(self):
        high = _decision(state="validated")
        # A validated decision cited for the target also covers the lower
        # decision-gated states on that same target.
        self.assertEqual(
            transition("tested", "verified", decision_record=high, target_id="RES-001"),
            "verified",
        )
        self.assertEqual(
            transition(
                "verified",
                "independently_reproduced",
                decision_record=high,
                target_id="RES-001",
            ),
            "independently_reproduced",
        )

    def test_programme_credit_is_not_self_awarded(self):
        self.assertEqual(assert_programme_credit("NONE"), "NONE")
        self.assertEqual(
            assert_programme_credit("CANDIDATE_PENDING_OWNER_REVIEW"),
            "CANDIDATE_PENDING_OWNER_REVIEW",
        )
        with self.assertRaises(EvidenceStateError) as caught:
            assert_programme_credit("AWARDED", target_id="RES-001")
        self.assertIn(
            "without an explicit owner or reviewer decision record", str(caught.exception)
        )

    def test_cross_axis_confusion_is_refused_both_ways(self):
        outcome_on_evidence_axis = cross_axis_problems(
            {"evidence_status": "failed", "execution_outcome": "failed"}, "RES-001"
        )
        self.assertTrue(outcome_on_evidence_axis)
        self.assertIn("EXECUTION_OUTCOME_CONFUSED", outcome_on_evidence_axis[0])
        self.assertIn("evidence_status 'failed'", outcome_on_evidence_axis[0])

        state_on_outcome_axis = cross_axis_problems(
            {"evidence_status": "documented", "execution_outcome": "documented"}, "RES-001"
        )
        self.assertTrue(state_on_outcome_axis)
        self.assertIn("execution_outcome 'documented'", state_on_outcome_axis[0])

        self.assertEqual(
            cross_axis_problems(
                {"evidence_status": "documented", "execution_outcome": "executed"}, "RES-001"
            ),
            [],
        )

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
        self.assertEqual(
            assert_authorization_status("NOT_AUTHORIZED", [evidence_only], "RES-001"),
            "NOT_AUTHORIZED",
        )

    def test_evidence_state_authorized_does_not_imply_authorization(self):
        """The Plan's top evidence state is not an authorization.

        An owner decision may legitimately set ``state: authorized`` on the
        evidence ladder. Unless that same record sets ``authorization_status``,
        the authorization column stays at its default.
        """
        owner_evidence_decision = _decision(
            state="authorized",
            authority="owner",
            decided_by="Owner cited in the decision record",
            statement="Evidence reached authorized. No release authorization granted.",
        )
        self.assertEqual(
            assert_authorization_status(
                "NOT_AUTHORIZED", [owner_evidence_decision], "RES-001"
            ),
            "NOT_AUTHORIZED",
        )
        self.assertFalse(
            authorization_record_supports(owner_evidence_decision, "RES-001")
        )

    def test_authorization_requires_its_own_column_on_the_decision(self):
        granted = _decision(
            authorization_status="AUTHORIZED",
            authority="owner",
            decided_by="Owner cited in the decision record",
            statement="Authorization recorded separately from evidence.",
        )
        self.assertTrue(authorization_record_supports(granted, "RES-001"))
        self.assertEqual(
            assert_authorization_status("AUTHORIZED", [granted], "RES-001"), "AUTHORIZED"
        )
        with self.assertRaises(EvidenceStateError):
            assert_authorization_status("PENDING", [], "RES-001")


if __name__ == "__main__":
    unittest.main()
