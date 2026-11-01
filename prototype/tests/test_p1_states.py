"""Stage P1. Requirement identifiers are ULC-<tablet>-<clause>."""

import unittest

import bootstrap  # noqa: F401
from support import T0, T1, T2, T3, ingest, memory_store, register_basics

from universalis.errors import (
    ConstituentDiscarded,
    ContradictionDropRefused,
    ContradictionMergeRefused,
    PlausibleSubstituteRejected,
    ReadinessRefused,
    RecencyDoesNotResolve,
    RetentionDoesNotPromote,
    StateCollapseRefused,
    VocabularyBoundaryError,
)
from universalis.presentation import project_for_display, save_projection_as_record
from universalis.states import (
    EvidenceState,
    Readiness,
    TransportOutcome,
    assert_readiness,
    require_evidence_state,
    require_transport_outcome,
)


class StageP1StatesTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())

    def test_ulc_21_08_every_evidence_state_round_trips(self):
        seen = []
        for state in EvidenceState:
            record = ingest(
                self.store,
                assertion_text=state.value,
                evidence_state=state,
                evidence_reason=f"reason for {state.value}",
                evidence_provenance=f"provenance for {state.value}",
            )
            loaded = self.store.get_record(record.record_id)
            self.assertEqual(loaded.evidence_state, state.value)
            self.assertEqual(loaded.evidence_reason, f"reason for {state.value}")
            self.assertEqual(loaded.evidence_provenance, f"provenance for {state.value}")
            self.assertEqual(loaded.custody_state, "unknown")
            seen.append(loaded.evidence_state)
        self.assertEqual(seen, [state.value for state in EvidenceState])

    def test_ulc_21_08_failed_request_cannot_be_stored_as_evidence_state(self):
        before = len(self.store.records_in_corpus("corpus-1", current_only=False))
        with self.assertRaises(VocabularyBoundaryError):
            require_evidence_state("failed_request")
        with self.assertRaises(VocabularyBoundaryError):
            require_evidence_state(TransportOutcome.FAILED_REQUEST)
        with self.assertRaises(VocabularyBoundaryError):
            ingest(self.store, evidence_state="failed_request")
        after = len(self.store.records_in_corpus("corpus-1", current_only=False))
        self.assertEqual(before, after)
        self.assertEqual(require_evidence_state("missing"), "missing")
        self.assertNotEqual(require_evidence_state("missing"), "failed_request")

    def test_ulc_21_08_evidence_state_cannot_be_stored_as_transport(self):
        with self.assertRaises(VocabularyBoundaryError):
            require_transport_outcome(EvidenceState.SUPPORTED)
        with self.assertRaises(VocabularyBoundaryError):
            require_transport_outcome("supported")
        for outcome in TransportOutcome:
            self.assertEqual(require_transport_outcome(outcome), outcome.value)
            self.store.record_route(
                corpus_id="corpus-1",
                outcome=outcome.value,
                transport=outcome,
                detail=outcome.value,
                recorded_at=T0,
            )

    def test_ulc_21_08_canonical_states_are_not_collapsed_into_the_record(self):
        records = [
            ingest(self.store, assertion_text=state.value, evidence_state=state)
            for state in EvidenceState
        ]
        with self.assertRaises(StateCollapseRefused):
            self.store.collapse_evidence_states([item.record_id for item in records])
        projection = project_for_display([item.evidence_state for item in records])
        self.assertEqual(projection.kind, "presentation_projection")
        self.assertFalse(projection.writable)
        with self.assertRaises(StateCollapseRefused):
            save_projection_as_record(projection)
        for record, state in zip(records, EvidenceState):
            self.assertEqual(self.store.get_record(record.record_id).evidence_state, state.value)

    def test_ulc_18_01_retention_duration_does_not_promote_evidence(self):
        record = ingest(
            self.store,
            evidence_state=EvidenceState.DISPUTED,
            evidence_reason="witnesses disagree",
        )
        self.store.note_retention(record.record_id, "P100Y")
        self.assertEqual(self.store.get_record(record.record_id).evidence_state, "disputed")
        with self.assertRaises(RetentionDoesNotPromote):
            self.store.promote_for_retention(record.record_id)
        self.assertEqual(self.store.get_record(record.record_id).evidence_state, "disputed")

    def test_ulc_18_07_missing_author_source_and_time_stay_unknown(self):
        record = ingest(
            self.store,
            role_author=None,
            role_recorder="recorder-a",
            source_ref=None,
            event_time=None,
            ingestion_time=T1,
        )
        loaded = self.store.get_record(record.record_id)
        self.assertEqual(loaded.role_author, "unknown")
        self.assertNotEqual(loaded.role_author, loaded.role_recorder)
        self.assertEqual(loaded.source_ref, "unknown")
        self.assertEqual(loaded.event_time, "unknown")
        self.assertNotEqual(loaded.event_time, loaded.ingestion_time)

    def test_ulc_18_07_plausible_substitute_is_rejected(self):
        record = ingest(self.store, role_author=None, event_time=None)
        with self.assertRaises(PlausibleSubstituteRejected):
            self.store.fill_unknown(record.record_id, "role_author", "probably Ada")
        loaded = self.store.get_record(record.record_id)
        self.assertEqual(loaded.role_author, "unknown")
        self.assertEqual(loaded.event_time, "unknown")

    def test_ulc_18_08_newer_witness_does_not_resolve_conflict(self):
        contradiction = self.store.note_contradiction(
            subject_id="subject-1",
            scope="wording of the account",
            created_at=T0,
            witnesses=[
                {"witness_id": "w1", "account": "alpha", "witnessed_at": T0},
                {"witness_id": "w2", "account": "beta", "witnessed_at": T1},
            ],
        )
        self.assertEqual(contradiction.evidence_state, "disputed")
        self.assertIsNone(contradiction.winning_account)
        with self.assertRaises(RecencyDoesNotResolve):
            self.store.add_witness(
                contradiction.contradiction_id,
                witness_id="w3",
                account="gamma",
                witnessed_at=T3,
                resolve_by_recency=True,
            )
        updated = self.store.add_witness(
            contradiction.contradiction_id,
            witness_id="w3",
            account="gamma",
            witnessed_at=T3,
        )
        self.assertEqual(updated.evidence_state, "disputed")
        self.assertIsNone(updated.resolution_decision)
        self.assertIsNone(updated.winning_account)
        self.assertEqual(updated.witnesses[-1]["account"], "gamma")
        resolved = self.store.record_resolution(
            contradiction.contradiction_id,
            decision="keep both accounts on the record",
            grounds="a reviewer recorded grounds",
            recorded_at=T2,
        )
        self.assertEqual(resolved.resolution_grounds, "a reviewer recorded grounds")
        self.assertIsNone(resolved.winning_account)
        self.assertEqual(len(resolved.witnesses), 3)

    def test_ulc_00_09_contradiction_is_an_explicit_record(self):
        contradiction = self.store.note_contradiction(
            subject_id="subject-1",
            scope="scoped to this wording",
            created_at=T0,
            witnesses=[
                {"witness_id": "w1", "account": "alpha", "witnessed_at": T0},
                {"witness_id": "w2", "account": "beta", "witnessed_at": T1},
            ],
        )
        loaded = self.store.get_contradiction(contradiction.contradiction_id)
        self.assertEqual(loaded.scope, "scoped to this wording")
        self.assertEqual(loaded.evidence_state, "disputed")
        self.assertEqual(len(loaded.witnesses), 2)

    def test_ulc_00_09_contradiction_cannot_be_merged_or_dropped(self):
        contradiction = self.store.note_contradiction(
            subject_id="subject-1",
            scope="scoped",
            created_at=T0,
            witnesses=[
                {"witness_id": "w1", "account": "alpha", "witnessed_at": T0},
                {"witness_id": "w2", "account": "beta", "witnessed_at": T1},
            ],
        )
        with self.assertRaises(ContradictionMergeRefused):
            self.store.merge_contradiction(contradiction.contradiction_id)
        with self.assertRaises(ContradictionDropRefused):
            self.store.drop_contradiction(contradiction.contradiction_id)
        loaded = self.store.get_contradiction(contradiction.contradiction_id)
        self.assertEqual(len(loaded.witnesses), 2)

    def test_ulc_00_01_aggregation_keeps_contradictory_constituents(self):
        first = ingest(self.store, assertion_text="alpha")
        second = ingest(self.store, assertion_text="beta")
        aggregation = self.store.aggregate(
            [first.record_id, second.record_id],
            summary="both accounts",
        )
        self.assertEqual(aggregation.constituent_ids, (first.record_id, second.record_id))
        difference_ids = {item["record_id"] for item in aggregation.differences}
        self.assertEqual(difference_ids, {first.record_id, second.record_id})

    def test_ulc_00_01_discarding_a_contradictory_constituent_is_refused(self):
        first = ingest(self.store, assertion_text="alpha")
        second = ingest(self.store, assertion_text="beta")
        with self.assertRaises(ConstituentDiscarded):
            self.store.aggregate(
                [first.record_id, second.record_id],
                summary="dropped",
                discard_contradictory=True,
            )
        count = self.store.connection.execute("SELECT COUNT(*) AS n FROM aggregations").fetchone()["n"]
        self.assertEqual(count, 0)

    def test_ulc_00_12_readiness_states_stay_distinct(self):
        states = list(Readiness)
        self.assertEqual(len(states), 4)
        self.assertEqual(len(set(states)), 4)
        for state in (
            Readiness.ABSENT,
            Readiness.FAILED,
            Readiness.UNEXECUTED,
        ):
            with self.assertRaises(ReadinessRefused):
                assert_readiness(state, evaluated=True, passing=True)

    def test_ulc_00_12_readiness_requires_evaluated_passing_evidence(self):
        assert_readiness(Readiness.EVALUATED_PASSING, evaluated=True, passing=True)
        with self.assertRaises(ReadinessRefused):
            assert_readiness(Readiness.EVALUATED_PASSING, evaluated=False, passing=True)
        with self.assertRaises(ReadinessRefused):
            assert_readiness(Readiness.EVALUATED_PASSING, evaluated=True, passing=False)


if __name__ == "__main__":
    unittest.main()
