"""Coverage against a declared population.

The denominator is the number of population members declared on the corpus.
Exclusions are reported beside that denominator. They are not a way to make
the denominator smaller. A report whose counts do not reconcile is refused:
no report object is returned, and the residual is an investigation item on
the exception rather than a rounded figure or a footnote.
"""

from __future__ import annotations

from dataclasses import dataclass

from universalis.errors import CoverageReconciliationRefused, DenominatorShrinkRefused
from universalis.store import Store


@dataclass(frozen=True)
class CoverageReport:
    declared_scope: str
    declared_population: int
    in_scope_total: int
    resolved: int
    unresolved: int
    excluded: int
    filtered: int
    missing: int
    unavailable: int
    unresolved_other: int
    shown: int

    def __post_init__(self) -> None:
        problems: list[str] = []
        if self.declared_population != self.in_scope_total + self.excluded:
            problems.append("declared_population != in_scope_total + excluded")
        if self.in_scope_total != self.resolved + self.unresolved:
            problems.append("in_scope_total != resolved + unresolved")
        if self.unresolved != self.missing + self.unavailable + self.unresolved_other:
            problems.append(
                "unresolved != missing + unavailable + unresolved_other"
            )
        if self.in_scope_total != self.shown + self.filtered:
            problems.append("in_scope_total != shown + filtered")
        if any(
            value < 0
            for value in (
                self.declared_population,
                self.in_scope_total,
                self.resolved,
                self.unresolved,
                self.excluded,
                self.filtered,
                self.missing,
                self.unavailable,
                self.unresolved_other,
                self.shown,
            )
        ):
            problems.append("a count is negative")
        residual = self.declared_population - (
            self.resolved + self.unresolved + self.excluded
        )
        if problems or residual != 0:
            raise CoverageReconciliationRefused(residual=residual, problems=problems)

    @property
    def denominator(self) -> int:
        return self.declared_population


def _classify(store: Store, corpus_id: str, member_id: str, excluded: dict) -> str:
    if member_id in excluded:
        return "excluded"
    record = store.current_record_for_member(corpus_id, member_id)
    claim = store.current_claim_for_member(corpus_id, member_id)
    reopened = False
    if claim is not None:
        state = store.current_claim_state(claim.claim_id)
        reopened = state is not None and state.review_state == "reopened"
    if record is None:
        route = store.latest_route(corpus_id, member_id)
        if route is not None and route.outcome == "unavailable":
            return "unavailable"
        return "missing"
    if record.evidence_state == "missing":
        return "missing"
    if record.evidence_state == "supported" and not reopened:
        return "resolved"
    return "unresolved_other"


def reconcile_boundary(
    *,
    sources: int,
    sinks: int,
    exclusions: int,
    observed: int,
    round_residual: bool = False,
) -> dict:
    """Reconcile the declared inbound, outbound, and rule-excluded populations.

    A non-zero residual is raised as an investigation item. Asking for the
    residual to be rounded is refused, and the unrounded residual is what the
    exception carries.
    """

    residual = sources - sinks - exclusions - observed
    if round_residual or residual != 0:
        raise CoverageReconciliationRefused(
            residual=residual,
            problems=[
                "unexplained residual between declared sources, sinks, "
                "boundary exclusions, and the observed total"
            ],
        )
    return {
        "sources": sources,
        "sinks": sinks,
        "exclusions": exclusions,
        "observed": observed,
        "residual": 0,
        "rounded": False,
    }


def compute_coverage(
    store: Store,
    corpus_id: str,
    *,
    denominator: int | None = None,
    filtered: int = 0,
) -> CoverageReport:
    corpus = store.corpus(corpus_id)
    members = store.population_ids(corpus_id)
    declared = len(members)
    if denominator is not None and denominator < declared:
        raise DenominatorShrinkRefused(
            "ULC-18-10: coverage is computed against the full declared population "
            f"({declared}); denominator {denominator} would shrink it"
        )
    if denominator is not None and denominator != declared:
        raise DenominatorShrinkRefused(
            "ULC-18-10: the coverage denominator is the full declared population "
            f"({declared}), not {denominator}"
        )
    excluded = store.exclusions(corpus_id)
    counts = {
        "resolved": 0,
        "missing": 0,
        "unavailable": 0,
        "unresolved_other": 0,
        "excluded": 0,
    }
    for member_id in members:
        kind = _classify(store, corpus_id, member_id, excluded)
        counts[kind] += 1
    unresolved = counts["missing"] + counts["unavailable"] + counts["unresolved_other"]
    in_scope = counts["resolved"] + unresolved
    if filtered < 0 or filtered > in_scope:
        raise CoverageReconciliationRefused(
            residual=0,
            problems=[f"filtered {filtered} is outside the in-scope total {in_scope}"],
        )
    return CoverageReport(
        declared_scope=corpus.declared_scope,
        declared_population=declared,
        in_scope_total=in_scope,
        resolved=counts["resolved"],
        unresolved=unresolved,
        excluded=counts["excluded"],
        filtered=filtered,
        missing=counts["missing"],
        unavailable=counts["unavailable"],
        unresolved_other=counts["unresolved_other"],
        shown=in_scope - filtered,
    )
