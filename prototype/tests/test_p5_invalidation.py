"""Stage P5. The corrected plan assigns ULC-21-07 here, with P1 and P2.

ULC-00-09 remains assigned to P1. The extra test below only shows that
invalidation does not drop a contradiction; it does not add ULC-00-09 to P5.
"""

import unittest

import bootstrap  # noqa: F401
from support import CORPUS, T0, T1, ingest, memory_store, register_basics

from universalis.errors import ContradictionDropRefused, ReopeningIsNotRejection
from universalis.invalidation import invalidate_evidence
from universalis.states import EvidenceState


class StageP5InvalidationTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())

    def _claim(self, record_id, member_id):
        claim = self.store.register_claim(
            corpus_id=CORPUS,
            record_id=record_id,
            passage_locator=f"para:{member_id}",
            version_id="v1",
            member_id=member_id,
        )
        self.store.append_claim_state(
            claim_id=claim.claim_id,
            review_state="decided",
            decision="accepted",
            reason="initial decision",
            recorded_at=T0,
        )
        return claim

    def test_ulc_21_07_invalidation_reopens_transitive_dependents(self):
        evidence = ingest(self.store, member_id="e", assertion_text="evidence")
        other = ingest(self.store, member_id="o", assertion_text="other")
        first = self._claim(evidence.record_id, "e")
        second = self._claim(evidence.record_id, "e2")
        third = self._claim(other.record_id, "o")
        self.store.declare_dependency(
            claim_id=first.claim_id,
            depends_on_kind="record",
            depends_on_id=evidence.record_id,
        )
        self.store.declare_dependency(
            claim_id=second.claim_id,
            depends_on_kind="claim",
            depends_on_id=first.claim_id,
        )
        reopened = invalidate_evidence(
            self.store,
            evidence.record_id,
            reason="witness withdrew the exhibit",
            recorded_at=T1,
        )
        self.assertEqual(reopened, sorted([first.claim_id, second.claim_id]))
        for claim_id in (first.claim_id, second.claim_id):
            self.assertEqual(self.store.current_claim_state(claim_id).review_state, "reopened")
        self.assertEqual(self.store.current_claim_state(third.claim_id).review_state, "decided")
        self.assertEqual(self.store.current_claim_state(third.claim_id).decision, "accepted")

    def test_ulc_21_07_reopened_claim_is_not_automatically_rejected(self):
        evidence = ingest(self.store, member_id="e")
        claim = self._claim(evidence.record_id, "e")
        self.store.declare_dependency(
            claim_id=claim.claim_id,
            depends_on_kind="record",
            depends_on_id=evidence.record_id,
        )
        with self.assertRaises(ReopeningIsNotRejection):
            self.store.append_claim_state(
                claim_id=claim.claim_id,
                review_state="reopened",
                decision="rejected",
                reason="would be an automatic rejection",
                recorded_at=T1,
            )
        invalidate_evidence(
            self.store,
            evidence.record_id,
            reason="withdrawn",
            recorded_at=T1,
        )
        current = self.store.current_claim_state(claim.claim_id)
        self.assertEqual(current.review_state, "reopened")
        self.assertNotEqual(current.decision, "rejected")
        self.assertEqual(current.decision, "reopened")

    def test_ulc_21_07_audit_history_retains_the_prior_verdict(self):
        evidence = ingest(
            self.store,
            member_id="e",
            assertion_text="original account",
            evidence_state=EvidenceState.SUPPORTED,
            evidence_reason="reviewed",
        )
        claim = self._claim(evidence.record_id, "e")
        self.store.declare_dependency(
            claim_id=claim.claim_id,
            depends_on_kind="record",
            depends_on_id=evidence.record_id,
        )
        invalidate_evidence(
            self.store,
            evidence.record_id,
            reason="withdrawn for review",
            recorded_at=T1,
        )
        history = self.store.claim_states(claim.claim_id)
        self.assertEqual(history[0].decision, "accepted")
        self.assertEqual(history[0].review_state, "decided")
        self.assertEqual(history[-1].review_state, "reopened")
        audits = self.store.audits_for(claim.claim_id)
        self.assertEqual(audits[0].prior_decision, "accepted")
        self.assertEqual(audits[0].new_review_state, "reopened")
        self.assertEqual(audits[0].reason, "withdrawn for review")
        retained = self.store.get_record(evidence.record_id)
        self.assertEqual(retained.assertion_text, "original account")
        self.assertEqual(retained.evidence_state, "supported")
        current = self.store.current_record(evidence.lineage_id)
        self.assertEqual(current.evidence_state, "pending_review")
        self.assertEqual(current.prior_belief, "supported")

    def test_ulc_00_09_invalidation_does_not_drop_the_contradiction(self):
        evidence = ingest(self.store, member_id="e")
        contradiction = self.store.note_contradiction(
            subject_id=evidence.record_id,
            scope="the account",
            created_at=T0,
            witnesses=[
                {"witness_id": "w1", "account": "alpha", "witnessed_at": T0},
                {"witness_id": "w2", "account": "beta", "witnessed_at": T1},
            ],
        )
        claim = self._claim(evidence.record_id, "e")
        self.store.declare_dependency(
            claim_id=claim.claim_id,
            depends_on_kind="record",
            depends_on_id=evidence.record_id,
        )
        invalidate_evidence(self.store, evidence.record_id, reason="withdrawn", recorded_at=T1)
        loaded = self.store.get_contradiction(contradiction.contradiction_id)
        self.assertEqual(len(loaded.witnesses), 2)
        self.assertEqual(loaded.evidence_state, "disputed")
        with self.assertRaises(ContradictionDropRefused):
            self.store.drop_contradiction(contradiction.contradiction_id)


if __name__ == "__main__":
    unittest.main()
