"""Exceptions raised when a prototype guard refuses a write or a report.

These are local checks. They are not a certification, and a raised exception
is not itself a reviewed requirement.
"""


class UniversalisError(Exception):
    """Base type for refusals this prototype raises."""


class InPlaceOverwriteRefused(UniversalisError):
    """ULC-18-06: a prior account's content is not updated in place."""


class TimestampOffsetRequired(UniversalisError):
    """ULC-18-05: a timestamp without an offset cannot be ordered."""


class UntypedReferenceRejected(UniversalisError):
    """ULC-00-02: a reference must carry a referent type from the closed set."""


class FieldDerivationRefused(UniversalisError):
    """ULC-00-05: no permission to use a record now may be inferred from where it came from or what has changed it."""


class TraceLinksRequired(UniversalisError):
    """ULC-00-06: a summary without resolvable trace links is rejected."""


class HistoricalAuthorityNotInherited(UniversalisError):
    """ULC-00-10: present wording does not inherit historical authority."""


class RoleInferenceRefused(UniversalisError):
    """ULC-18-02: a provenance role is not inferred from another role."""


class InsufficientClaimPointer(UniversalisError):
    """ULC-18-03: a title or document reference alone cannot locate a claim."""


class ClockCollapseRefused(UniversalisError):
    """ULC-18-04: clocks that differ are not stored as one collapsed value."""


class VocabularyBoundaryError(UniversalisError):
    """A value from one vocabulary was offered to the other vocabulary's field."""


class StateCollapseRefused(UniversalisError):
    """ULC-21-08: canonical evidence states are not collapsed into the record."""


class RetentionDoesNotPromote(UniversalisError):
    """ULC-18-01: retention duration does not promote an evidence state."""


class PlausibleSubstituteRejected(UniversalisError):
    """ULC-18-07: a missing author, source, or time is not filled with a guess."""


class RecencyDoesNotResolve(UniversalisError):
    """ULC-18-08: a newer witness does not resolve a conflict."""


class ContradictionMergeRefused(UniversalisError):
    """ULC-00-09: contradictions are not silently merged."""


class ContradictionDropRefused(UniversalisError):
    """ULC-00-09: contradictions are not dropped."""


class ResolutionRequiresGrounds(UniversalisError):
    """ULC-18-08: a conflict changes only when a resolution records grounds."""


class ConstituentDiscarded(UniversalisError):
    """ULC-00-01: an aggregation may not discard a contradictory constituent."""


class ReadinessRefused(UniversalisError):
    """ULC-00-12: readiness is refused without evaluated, passing evidence."""


class ToolingStatusForbidden(UniversalisError):
    """Tooling must not set reviewed, accepted, or authorized."""


class DenominatorShrinkRefused(UniversalisError):
    """ULC-18-10: the coverage denominator stays the full declared population."""


class CoverageReconciliationRefused(UniversalisError):
    """ULC-21-10 and ULC-16-02: counts that do not reconcile are not reported.

    The residual is carried on the exception as an investigation item. It is
    not rounded away and it is not attached as a footnote on a report.
    """

    def __init__(self, residual, problems):
        self.residual = residual
        self.problems = tuple(problems)
        self.investigation_item = {
            "residual": residual,
            "problems": list(self.problems),
            "rounded": False,
        }
        detail = "; ".join(self.problems) if self.problems else "residual is non-zero"
        super().__init__(
            "coverage reconciliation refused; residual "
            f"{residual} is an investigation item and was not rounded ({detail})"
        )


class ViewScopeRequired(UniversalisError):
    """ULC-21-02: a view declares corpus, version, rules, and scope before a total."""


class CompleteLabelRefused(UniversalisError):
    """ULC-21-05: a filtered or resolved-only view is not labelled complete."""


class FailedRouteIsNotEmpty(UniversalisError):
    """ULC-21-06: a failed, missing, truncated, denied, or unavailable route is not empty."""


class TruncationPresentedAsComplete(UniversalisError):
    """ULC-21-06 and ULC-16-12: a truncated result is not presented as complete."""


class TruncationNotReported(UniversalisError):
    """ULC-16-12: a truncated result names what it omitted."""


class OmissionNotNamed(UniversalisError):
    """ULC-16-12: a degraded result names what was omitted."""


class DegradedPresentedAsComplete(UniversalisError):
    """ULC-16-12: a degraded result is not presented as complete."""


class FabricationRefused(UniversalisError):
    """ULC-16-07: a fabricated result is a hard error."""


class ReopeningIsNotRejection(UniversalisError):
    """ULC-21-07: reopening a claim does not write a rejection."""


class StatusIncomplete(UniversalisError):
    """ULC-21-03: a status needs both a text label and a machine value."""


class ColourAloneRefused(UniversalisError):
    """ULC-21-03 and ULC-21-09: colour cannot carry status by itself."""


class StatusAnnouncementRequired(UniversalisError):
    """ULC-21-09: a status change is announced in text."""


class IncompleteClaimRendering(UniversalisError):
    """ULC-21-01: a claim rendering needs state, reason, and source."""


class AuthorizationNotImplied(UniversalisError):
    """ULC-00-11: a test, mapping, or equation does not supply authorization."""


class AnalogyCannotPopulateSource(UniversalisError):
    """ULC-16-05: an analogy or metaphor cannot populate a source field."""


class SourceNotScopedOrigin(UniversalisError):
    """ULC-16-05: a source must resolve to a scoped origin with provenance."""


class AuthorizationDimensionMissing(UniversalisError):
    """ULC-16-11: an authorization check is missing a required dimension."""


class LineageNotFound(UniversalisError):
    """The lineage named for a correction does not exist in the store."""


class PopulationMemberMissing(UniversalisError):
    """The population member is not in the declared population."""


class DomainNotForwardInvariant(UniversalisError):
    """ULC-01-05: a trajectory bound is not a guarantee on a domain that
    iteration escapes.

    A bound derived under a premise is only a guarantee where the premise
    actually holds along the trajectory. If the state leaves the declared
    domain, or the per-step premise has already failed, the bound may still
    appear numerically satisfied while the guarantee it seemed to give is
    gone. This refusal is recorded rather than repaired by widening the
    domain after the fact.
    """

    def __init__(self, step, reason, bound_holder=None):
        self.step = step
        self.reason = reason
        self.bound_holder = bound_holder
        super().__init__(
            f"trajectory guarantee refused at step {step}: {reason}"
        )
