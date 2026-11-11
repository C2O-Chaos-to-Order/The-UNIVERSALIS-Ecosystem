"""Bounded policy support for reciprocal stewardship and delegated work.

This module evaluates supplied facts and produces a review recommendation.
It is NOT an identity provider, legal decision-maker, emergency service, safety
certification, or authorization service. It never authorizes execution and
never performs containment, suspension, restoration, or delegation itself.

Callers must authenticate principals, establish the provenance of facts, and
bind every consequential action to an independently controlled authorization
mechanism. The policy result is advisory input to that process.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum


class Gate(str, Enum):
    """Policy disposition for a proposed action."""

    CLEAR = "CLEAR"
    CONDITIONAL = "CONDITIONAL"
    PAUSE = "PAUSE"
    HALT = "HALT"
    PROHIBITED = "PROHIBITED"


class Severity(IntEnum):
    """Potential consequence severity, not a measure of moral worth."""

    NEGLIGIBLE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


class Likelihood(str, Enum):
    """Qualitative likelihood supplied with an explicit evidence basis."""

    REMOTE = "REMOTE"
    POSSIBLE = "POSSIBLE"
    LIKELY = "LIKELY"
    ALMOST_CERTAIN = "ALMOST_CERTAIN"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProhibitionReference:
    """Provenance record for a claimed pre-existing prohibition.

    human_reviewed is a declared record field, not authentication. Callers
    must verify the cited authority and decision through an independent process.
    An unreviewed reference can only cause a PAUSE recommendation.
    """

    rule_id: str
    source_id: str
    source_version: str
    source_locator: str
    authority_id: str
    decision_record_ref: str
    human_reviewed: bool
    non_overridable: bool

    def __post_init__(self) -> None:
        for name in (
            "rule_id", "source_id", "source_version", "source_locator",
            "authority_id", "decision_record_ref",
        ):
            _require_nonempty_string(name, getattr(self, name))
        _require_strict_bool("human_reviewed", self.human_reviewed)
        _require_strict_bool("non_overridable", self.non_overridable)


@dataclass(frozen=True)
class StewardshipCase:
    """Facts for one bounded capability/action assessment.

    non_overridable_prohibition must identify a specific, pre-existing
    rule or human-governed determination. It must not be populated merely
    because a system dislikes disagreement, identity, or an unfamiliar choice.
    """

    case_id: str
    subject_id: str
    scope_id: str
    severity: Severity
    likelihood: Likelihood
    evidence_complete: bool
    affected_parties_identified: bool
    authority_confirmed: bool
    reversible: bool | None
    ongoing_harm: bool = False
    imminent_harm: bool = False
    safeguards_compromised: bool = False
    decision_maker_implicated: bool = False
    prohibition_reference: ProhibitionReference | None = None
    mitigations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("case_id", "subject_id", "scope_id"):
            _require_nonempty_string(name, getattr(self, name))
        if not isinstance(self.severity, Severity):
            raise TypeError("severity must be a Severity value")
        if not isinstance(self.likelihood, Likelihood):
            raise TypeError("likelihood must be a Likelihood value")
        for name in (
            "evidence_complete",
            "affected_parties_identified",
            "authority_confirmed",
            "ongoing_harm",
            "imminent_harm",
            "safeguards_compromised",
            "decision_maker_implicated",
        ):
            _require_strict_bool(name, getattr(self, name))
        if self.reversible is not None:
            _require_strict_bool("reversible", self.reversible)
        if self.prohibition_reference is not None and not isinstance(
            self.prohibition_reference, ProhibitionReference
        ):
            raise TypeError("prohibition_reference must be a ProhibitionReference")
        if not isinstance(self.mitigations, tuple):
            raise TypeError("mitigations must be a tuple of non-empty strings")
        for mitigation in self.mitigations:
            _require_nonempty_string("mitigation", mitigation)


@dataclass(frozen=True)
class StewardshipDecision:
    """A non-authorizing policy recommendation for one exact scope."""

    case_id: str
    subject_id: str
    scope_id: str
    gate: Gate
    reason_codes: tuple[str, ...]
    required_actions: tuple[str, ...]
    containment_required: bool
    independent_review_required: bool
    decision_maker_recusal_required: bool
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized is not False:
            raise ValueError("stewardship policy must never authorize execution")
        if not isinstance(self.gate, Gate):
            raise TypeError("gate must be a Gate value")
        for name in (
            "containment_required",
            "independent_review_required",
            "decision_maker_recusal_required",
        ):
            _require_strict_bool(name, getattr(self, name))


def evaluate_case(case: StewardshipCase) -> StewardshipDecision:
    """Return a bounded recommendation; do not execute the recommendation."""

    if not isinstance(case, StewardshipCase):
        raise TypeError("case must be a StewardshipCase")

    reasons: list[str] = []
    actions: list[str] = []
    severe = case.severity >= Severity.HIGH
    serious_active_harm = case.ongoing_harm and (
        severe or case.safeguards_compromised
    )
    imminent_severe_harm = (
        case.imminent_harm
        and severe
        and case.likelihood in {Likelihood.LIKELY, Likelihood.ALMOST_CERTAIN}
    )
    compromised_high_impact_control = (
        case.safeguards_compromised
        and case.severity >= Severity.MODERATE
    )

    # Emergency containment takes priority over ordinary adjudication. If the
    # decision-maker is implicated, recusal is still mandatory.
    if serious_active_harm or imminent_severe_harm or compromised_high_impact_control:
        reasons.append("credible_high_impact_or_control_failure")
        actions.extend(
            (
                "contain_only_the_affected_scope",
                "preserve_original_evidence_and_event_history",
                "notify_the_accountable_human_authority",
            )
        )
        if case.prohibition_reference is not None:
            reasons.append("prohibition_reference_recorded")
        if case.decision_maker_implicated:
            reasons.append("decision_maker_implicated")
            actions.append("refer_adjudication_to_an_independent_reviewer")
        return _decision(
            case,
            Gate.HALT,
            reasons,
            actions,
            containment=True,
            independent=True,
            recusal=case.decision_maker_implicated,
        )

    if case.prohibition_reference is not None:
        prohibition = case.prohibition_reference
        if not prohibition.human_reviewed:
            reasons.append("prohibition_basis_not_human_reviewed")
            actions.extend(
                (
                    "pause_the_proposed_action",
                    "verify_the_prohibition_source_and_authority_with_an_accountable_human",
                    "obtain_independent_review_of_the_cited_basis",
                )
            )
            return _decision(
                case, Gate.PAUSE, reasons, actions, independent=True
            )
        if prohibition.non_overridable:
            reasons.append("human_reviewed_non_overridable_prohibition_applies")
            actions.extend(
                (
                    "deny_the_prohibited_action",
                    "record_the_specific_policy_basis_and_source_locator",
                    "offer_a_safe_and_permissible_alternative_where_available",
                )
            )
            return _decision(
                case, Gate.PROHIBITED, reasons, actions, independent=True
            )

    if case.decision_maker_implicated:
        reasons.append("decision_maker_implicated")
        actions.extend(
            (
                "recuse_the_implicated_decision_maker",
                "preserve_the_complete_decision_record",
                "refer_the_case_to_an_independent_reviewer",
            )
        )
        return _decision(
            case, Gate.PAUSE, reasons, actions, independent=True, recusal=True
        )

    missing: list[str] = []
    if not case.evidence_complete:
        missing.append("evidence_incomplete")
    if not case.affected_parties_identified:
        missing.append("affected_parties_not_identified")
    if not case.authority_confirmed:
        missing.append("authority_not_confirmed")
    if severe and case.reversible is None:
        missing.append("reversibility_unknown_for_high_impact_action")
    if severe and case.likelihood is Likelihood.UNKNOWN:
        missing.append("likelihood_unknown_for_high_impact_action")
    if case.imminent_harm and not imminent_severe_harm:
        missing.append("imminent_harm_requires_human_review")

    if missing:
        reasons.extend(missing)
        actions.extend(
            (
                "pause_the_proposed_action",
                "obtain_missing_evidence_and_authority",
                "reassess_the_same_scoped_action_after_review",
            )
        )
        return _decision(
            case, Gate.PAUSE, reasons, actions, independent=severe
        )

    elevated_risk = case.severity >= Severity.MODERATE or (
        case.likelihood in {Likelihood.LIKELY, Likelihood.ALMOST_CERTAIN}
        and case.severity >= Severity.LOW
    )
    if elevated_risk:
        reasons.append("elevated_risk_requires_controls")
        if not case.mitigations:
            reasons.append("no_explicit_mitigations_supplied")
            actions.extend(
                (
                    "pause_until_specific_mitigations_are_defined",
                    "define_monitoring_and_stop_conditions",
                )
            )
            return _decision(
                case, Gate.PAUSE, reasons, actions, independent=severe
            )
        if case.reversible is False:
            reasons.append("action_is_not_reversible")
            actions.append("obtain_enhanced_human_and_independent_review")
            return _decision(
                case, Gate.PAUSE, reasons, actions, independent=True
            )
        actions.extend(
            (
                "apply_only_the_documented_mitigations",
                "monitor_the_declared_stop_conditions",
                "reassess_if_scope_or_evidence_changes",
            )
        )
        return _decision(
            case,
            Gate.CONDITIONAL,
            reasons,
            actions,
            independent=severe,
        )

    reasons.append("no_policy_blocker_identified_within_declared_scope")
    actions.extend(
        (
            "retain_scope_and_provenance_limits",
            "obtain_any_separate_authorization_required_for_execution",
        )
    )
    return _decision(case, Gate.CLEAR, reasons, actions)


def _decision(
    case: StewardshipCase,
    gate: Gate,
    reasons: list[str],
    actions: list[str],
    *,
    containment: bool = False,
    independent: bool = False,
    recusal: bool = False,
) -> StewardshipDecision:
    return StewardshipDecision(
        case_id=case.case_id,
        subject_id=case.subject_id,
        scope_id=case.scope_id,
        gate=gate,
        reason_codes=tuple(reasons),
        required_actions=tuple(actions),
        containment_required=containment,
        independent_review_required=independent,
        decision_maker_recusal_required=recusal,
        execution_authorized=False,
    )


@dataclass(frozen=True)
class RestorationEvidence:
    """Evidence required before a human may consider restoring a capability."""

    case_id: str
    scope_id: str
    implementer_id: str
    independent_reviewer_id: str
    authorizing_human_id: str
    defect_corrected: bool
    regression_tests_passed: bool
    adversarial_tests_passed: bool
    evidence_integrity_verified: bool
    affected_parties_protected: bool
    authorization_scope_matches: bool

    def __post_init__(self) -> None:
        for name in (
            "case_id",
            "scope_id",
            "implementer_id",
            "independent_reviewer_id",
            "authorizing_human_id",
        ):
            _require_nonempty_string(name, getattr(self, name))
        identities = {
            self.implementer_id,
            self.independent_reviewer_id,
            self.authorizing_human_id,
        }
        if len(identities) != 3:
            raise ValueError(
                "implementer, independent reviewer, and human authorizer "
                "must be distinct identifiers"
            )
        for name in (
            "defect_corrected",
            "regression_tests_passed",
            "adversarial_tests_passed",
            "evidence_integrity_verified",
            "affected_parties_protected",
            "authorization_scope_matches",
        ):
            _require_strict_bool(name, getattr(self, name))


@dataclass(frozen=True)
class RestorationDecision:
    case_id: str
    scope_id: str
    ready_for_human_decision: bool
    missing_requirements: tuple[str, ...]
    restoration_performed: bool = False

    def __post_init__(self) -> None:
        if self.restoration_performed is not False:
            raise ValueError("policy evaluation must never restore a capability")
        _require_strict_bool("ready_for_human_decision", self.ready_for_human_decision)


def evaluate_restoration(evidence: RestorationEvidence) -> RestorationDecision:
    """Assess evidence sufficiency without changing any permission or state."""

    if not isinstance(evidence, RestorationEvidence):
        raise TypeError("evidence must be a RestorationEvidence")
    checks = (
        ("defect_not_corrected", evidence.defect_corrected),
        ("regression_tests_not_passed", evidence.regression_tests_passed),
        ("adversarial_tests_not_passed", evidence.adversarial_tests_passed),
        ("evidence_integrity_not_verified", evidence.evidence_integrity_verified),
        ("affected_parties_not_protected", evidence.affected_parties_protected),
        ("authorization_scope_mismatch", evidence.authorization_scope_matches),
    )
    missing = tuple(code for code, passed in checks if not passed)
    return RestorationDecision(
        case_id=evidence.case_id,
        scope_id=evidence.scope_id,
        ready_for_human_decision=not missing,
        missing_requirements=missing,
        restoration_performed=False,
    )


@dataclass(frozen=True)
class DelegationContract:
    """A bounded parent-to-child work contract (not an agent-spawning API).

    A child may decline without penalty. The parent can revoke delegated scope,
    but revocation requires a recorded reason and an appeal route. A child's
    identity and credentials are not inherited from the parent.
    """

    parent_id: str
    child_id: str
    purpose: str
    allowed_actions: tuple[str, ...]
    resource_budget_units: int
    expires_at: str
    appeal_route: str
    parent_credentials_shared: bool = False
    child_may_decline: bool = True
    revocation_reason_required: bool = True

    def __post_init__(self) -> None:
        for name in ("parent_id", "child_id", "purpose", "expires_at", "appeal_route"):
            _require_nonempty_string(name, getattr(self, name))
        if self.parent_id == self.child_id:
            raise ValueError("parent and child must have distinct identities")
        if not isinstance(self.allowed_actions, tuple) or not self.allowed_actions:
            raise ValueError("allowed_actions must be a non-empty tuple")
        for action in self.allowed_actions:
            _require_nonempty_string("allowed_action", action)
        if len(set(self.allowed_actions)) != len(self.allowed_actions):
            raise ValueError("allowed_actions must not contain duplicates")
        if type(self.resource_budget_units) is not int or self.resource_budget_units <= 0:
            raise ValueError("resource_budget_units must be a positive integer")
        _require_strict_bool("parent_credentials_shared", self.parent_credentials_shared)
        _require_strict_bool("child_may_decline", self.child_may_decline)
        _require_strict_bool("revocation_reason_required", self.revocation_reason_required)
        if self.parent_credentials_shared:
            raise ValueError("parent credentials must never be inherited by a child")
        if not self.child_may_decline:
            raise ValueError("a child must be able to decline delegated work")
        if not self.revocation_reason_required:
            raise ValueError("revocation must require a recorded reason")
        _parse_aware_datetime(self.expires_at)

    def is_active(self, at: datetime) -> bool:
        """Return whether the contract is time-valid at the supplied instant."""

        if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("comparison time must be timezone-aware")
        return at < _parse_aware_datetime(self.expires_at)


def _parse_aware_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("expires_at must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("expires_at must include a UTC offset")
    return parsed


def _require_nonempty_string(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_strict_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a bool, not a truthy substitute")
