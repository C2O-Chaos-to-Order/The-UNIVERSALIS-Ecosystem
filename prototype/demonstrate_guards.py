"""Run the guards that are easiest to fake and print the refusal.

This script is a demonstration, not a test suite and not evidence that any
requirement is accepted.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from universalis.authz import InMemoryAuthorizationStub
from universalis.coverage import compute_coverage
from universalis.errors import (
    ColourAloneRefused,
    DenominatorShrinkRefused,
    FailedRouteIsNotEmpty,
    InPlaceOverwriteRefused,
    VocabularyBoundaryError,
)
from universalis.failures import RouteRequest, present_as_empty, resolve
from universalis.invalidation import invalidate_evidence
from universalis.presentation import render_status, status_from_colour
from universalis.states import EvidenceState, require_evidence_state
from universalis.store import Store

T0 = "2026-01-01T00:00:00+00:00"
T1 = "2026-01-02T00:00:00+00:00"


def show(title, fn):
    print(f"--- {title}")
    try:
        value = fn()
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}")
        return
    if value is not None:
        print(value)


def main():
    store = Store(":memory:")
    store.register_corpus(
        corpus_id="corpus-1",
        version="v1",
        inclusion_rules=["keep"],
        scope_boundary="local",
        declared_scope="demo population",
        registered_at=T0,
    )
    record = store.ingest_record(
        corpus_id="corpus-1",
        assertion_text="first account",
        version="1",
        evidence_state=EvidenceState.DISPUTED,
        evidence_reason="two witnesses",
        evidence_provenance="w1",
        ingestion_time=T0,
        member_id="m1",
    )

    def in_place():
        store.correct_in_place(record.record_id, assertion_text="tampered")

    show("1. in-place correction", in_place)

    def bad_evidence():
        require_evidence_state("failed_request")

    show("2. failed_request stored as an evidence state", bad_evidence)

    store.declare_population_member("corpus-1", "m1")

    def shrink():
        compute_coverage(store, "corpus-1", denominator=0)

    show("3. shrink a coverage denominator", shrink)

    def failed_route():
        result = resolve(
            store,
            RouteRequest(corpus_id="corpus-1", route_failed=True, recorded_at=T0),
        )
        print(f"outcome={result.outcome} transport={result.transport}")
        present_as_empty(result)

    show("4. present a failed route as empty", failed_route)

    claim = store.register_claim(
        corpus_id="corpus-1",
        record_id=record.record_id,
        passage_locator="para:1",
        version_id="v1",
        member_id="m1",
    )
    store.append_claim_state(
        claim_id=claim.claim_id,
        review_state="decided",
        decision="accepted",
        reason="initial",
        recorded_at=T0,
    )
    store.declare_dependency(
        claim_id=claim.claim_id,
        depends_on_kind="record",
        depends_on_id=record.record_id,
    )

    def reopen():
        invalidate_evidence(store, record.record_id, reason="withdrawn", recorded_at=T1)
        current = store.current_claim_state(claim.claim_id)
        print(
            f"review_state={current.review_state} decision={current.decision} "
            f"prior_audit={store.audits_for(claim.claim_id)[0].prior_decision}"
        )
        if current.decision == "rejected":
            raise AssertionError("reopening wrote a rejection")

    show("5. invalidation reopens and does not reject", reopen)

    def colour():
        status_from_colour("red")

    show("6a. status from colour alone", colour)

    def render_colour():
        render_status(colour="red")

    show("6b. render colour alone", render_colour)

    def visible():
        stub = InMemoryAuthorizationStub()
        stub.show_path("/corpus/1")
        decision = stub.authorize(
            principal="ada",
            purpose="research",
            project="corpus-1",
            credential="stub-token",
            action="read",
            path="/corpus/1",
        )
        print(
            f"permitted={decision.permitted} visible={decision.path_visible} "
            f"notice={decision.notice}"
        )
        if decision.permitted:
            raise AssertionError("visibility was treated as permission")

    show("7. visible path is not permission", visible)
    print("--- types expected above")
    print(
        ", ".join(
            [
                InPlaceOverwriteRefused.__name__,
                VocabularyBoundaryError.__name__,
                DenominatorShrinkRefused.__name__,
                FailedRouteIsNotEmpty.__name__,
                ColourAloneRefused.__name__,
            ]
        )
    )


if __name__ == "__main__":
    main()
