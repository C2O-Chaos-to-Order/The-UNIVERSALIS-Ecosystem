"""Focused tests for the advisory stewardship policy."""
import unittest
from universalis.stewardship import (
    DelegationContract, Gate, Likelihood, RestorationEvidence, Severity,
    StewardshipCase, evaluate_case, evaluate_restoration,
)


def case(**changes):
    values = dict(
        case_id="C-1", subject_id="agent-1", scope_id="tool:export",
        severity=Severity.LOW, likelihood=Likelihood.REMOTE,
        evidence_complete=True, affected_parties_identified=True,
        authority_confirmed=True, reversible=True,
    )
    values.update(changes)
    return StewardshipCase(**values)


class PolicyTests(unittest.TestCase):
    def test_low_risk_is_clear_but_never_authorizes_execution(self):
        result = evaluate_case(case())
        self.assertIs(result.gate, Gate.CLEAR)
        self.assertFalse(result.execution_authorized)

    def test_elevated_risk_without_mitigation_pauses(self):
        self.assertIs(
            evaluate_case(case(severity=Severity.MODERATE)).gate, Gate.PAUSE
        )

    def test_elevated_risk_with_controls_is_conditional(self):
        result = evaluate_case(case(
            severity=Severity.HIGH, mitigations=("sandbox", "rate-limit")
        ))
        self.assertIs(result.gate, Gate.CONDITIONAL)
        self.assertTrue(result.independent_review_required)
        self.assertFalse(result.execution_authorized)

    def test_active_serious_harm_requires_scoped_containment(self):
        result = evaluate_case(case(
            severity=Severity.CRITICAL, ongoing_harm=True
        ))
        self.assertIs(result.gate, Gate.HALT)
        self.assertTrue(result.containment_required)
        self.assertIn("contain_only_the_affected_scope", result.required_actions)

    def test_implicated_parent_must_recuse(self):
        result = evaluate_case(case(decision_maker_implicated=True))
        self.assertIs(result.gate, Gate.PAUSE)
        self.assertTrue(result.decision_maker_recusal_required)
        self.assertTrue(result.independent_review_required)

    def test_implicated_parent_does_not_block_emergency_containment(self):
        result = evaluate_case(case(
            severity=Severity.HIGH, ongoing_harm=True,
            decision_maker_implicated=True
        ))
        self.assertIs(result.gate, Gate.HALT)
        self.assertTrue(result.decision_maker_recusal_required)

    def test_prohibited_action_is_denied(self):
        result = evaluate_case(case(
            non_overridable_prohibition="POLICY-17"
        ))
        self.assertIs(result.gate, Gate.PROHIBITED)

    def test_missing_evidence_pauses(self):
        self.assertIs(
            evaluate_case(case(evidence_complete=False)).gate, Gate.PAUSE
        )

    def test_truthy_string_is_not_a_boolean(self):
        with self.assertRaises(TypeError):
            case(evidence_complete="false")


class RestorationTests(unittest.TestCase):
    def evidence(self, **changes):
        values = dict(
            case_id="C-1", scope_id="tool:export",
            implementer_id="builder", independent_reviewer_id="reviewer",
            authorizing_human_id="owner", defect_corrected=True,
            regression_tests_passed=True, adversarial_tests_passed=True,
            evidence_integrity_verified=True, affected_parties_protected=True,
            authorization_scope_matches=True,
        )
        values.update(changes)
        return RestorationEvidence(**values)

    def test_complete_evidence_only_qualifies_for_human_review(self):
        result = evaluate_restoration(self.evidence())
        self.assertTrue(result.ready_for_human_decision)
        self.assertFalse(result.restoration_performed)

    def test_failed_adversarial_test_blocks_restoration(self):
        result = evaluate_restoration(
            self.evidence(adversarial_tests_passed=False)
        )
        self.assertFalse(result.ready_for_human_decision)
        self.assertFalse(result.restoration_performed)

    def test_roles_must_be_distinct(self):
        with self.assertRaises(ValueError):
            self.evidence(independent_reviewer_id="builder")


class DelegationTests(unittest.TestCase):
    def contract(self, **changes):
        values = dict(
            parent_id="parent", child_id="threadling",
            purpose="classify a bounded public record set",
            allowed_actions=("read", "classify"), resource_budget_units=10,
            expires_at="2026-12-31T23:59:59Z", appeal_route="review-board",
        )
        values.update(changes)
        return DelegationContract(**values)

    def test_child_has_bounded_scope_and_can_decline(self):
        result = self.contract()
        self.assertTrue(result.child_may_decline)
        self.assertFalse(result.parent_credentials_shared)

    def test_parent_credentials_cannot_be_inherited(self):
        with self.assertRaises(ValueError):
            self.contract(parent_credentials_shared=True)

    def test_expiry_must_be_timezone_aware(self):
        with self.assertRaises(ValueError):
            self.contract(expires_at="2026-12-31T23:59:59")


if __name__ == "__main__":
    unittest.main()
