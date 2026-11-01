"""Withdraw evidence and reopen dependent claims.

Reopening appends a new claim state and an audit row. The prior decision row
stays in the claim history. The new decision is not a rejection.
"""

from __future__ import annotations

from universalis.states import EXPLICIT_UNKNOWN, EvidenceState
from universalis.store import Store


def transitive_claim_dependents(store: Store, record_id: str) -> list[str]:
    """Claims that depend on this record, following explicit edges only.

    Sharing a corpus, a page, or a neighbour id does not create an edge.
    """

    dependencies = store.dependencies()
    dependents = {
        item.claim_id
        for item in dependencies
        if item.depends_on_kind == "record" and item.depends_on_id == record_id
    }
    changed = True
    while changed:
        changed = False
        for item in dependencies:
            if (
                item.depends_on_kind == "claim"
                and item.depends_on_id in dependents
                and item.claim_id not in dependents
            ):
                dependents.add(item.claim_id)
                changed = True
    return sorted(dependents)


def invalidate_evidence(
    store: Store,
    record_id: str,
    *,
    reason: str,
    recorded_at: str,
) -> list[str]:
    """Reopen every claim that transitively depends on this evidence.

    The evidence account is corrected by appending a pending-review account.
    The prior account remains. Dependents are reopened, not rejected.
    """

    if not reason or not str(reason).strip():
        raise ValueError("invalidation requires a reason for reopening")
    record = store.get_record(record_id)
    if record is None:
        raise KeyError(record_id)
    dependents = transitive_claim_dependents(store, record_id)
    store.correct_record(
        lineage_id=record.lineage_id,
        assertion_text=record.assertion_text,
        version=record.version,
        evidence_state=EvidenceState.PENDING_REVIEW,
        evidence_reason=reason,
        evidence_provenance=record.evidence_provenance,
        correction_time=recorded_at,
        ingestion_time=recorded_at,
        witness_history=[
            {"event": "invalidation", "prior_record_id": record.record_id}
        ],
        authority_claim=EXPLICIT_UNKNOWN,
        inherit_authority=False,
    )
    for claim_id in dependents:
        previous = store.current_claim_state(claim_id)
        prior_decision = previous.decision if previous is not None else "none"
        store.append_claim_state(
            claim_id=claim_id,
            review_state="reopened",
            decision="reopened",
            reason=reason,
            recorded_at=recorded_at,
        )
        store.append_audit(
            subject_kind="claim",
            subject_id=claim_id,
            event_type="reopened",
            prior_decision=prior_decision,
            new_review_state="reopened",
            reason=reason,
            recorded_at=recorded_at,
        )
    return dependents
