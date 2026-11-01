"""Stage P2. Requirement identifiers are ULC-<tablet>-<clause>."""

import sqlite3
import unittest

import bootstrap  # noqa: F401
from support import CORPUS, T0, T1, ingest, memory_store, register_basics

from universalis.coverage import CoverageReport, compute_coverage, reconcile_boundary
from universalis.errors import (
    CompleteLabelRefused,
    CoverageReconciliationRefused,
    DenominatorShrinkRefused,
    ViewScopeRequired,
)
from universalis.invalidation import invalidate_evidence
from universalis.states import EvidenceState, RouteOutcome
from universalis.views import ViewSpec, create_view, read_view


class StageP2CoverageTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())

    def _population(self):
        for member_id in ("a", "b", "c", "d", "e"):
            self.store.declare_population_member(CORPUS, member_id)
        self.store.exclude_member(CORPUS, "a", "outside the boundary")
        ingest(
            self.store,
            member_id="b",
            evidence_state=EvidenceState.SUPPORTED,
            evidence_reason="reviewed",
            assertion_text="supported account",
        )
        ingest(
            self.store,
            member_id="e",
            evidence_state=EvidenceState.DISPUTED,
            evidence_reason="witnesses disagree",
            assertion_text="disputed account",
        )
        self.store.record_route(
            corpus_id=CORPUS,
            member_id="d",
            outcome=RouteOutcome.UNAVAILABLE,
            detail="source unresolved",
            recorded_at=T0,
        )

    def test_ulc_18_10_coverage_denominator_cannot_shrink(self):
        self._population()
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual(report.denominator, 5)
        self.assertEqual(report.declared_population, 5)
        with self.assertRaises(DenominatorShrinkRefused):
            compute_coverage(self.store, CORPUS, denominator=4)
        with self.assertRaises(DenominatorShrinkRefused):
            self.store.shrink_population(CORPUS, "b")
        with self.assertRaises(sqlite3.IntegrityError) as caught:
            self.store.connection.execute(
                "DELETE FROM population_members WHERE member_id = ?",
                ("b",),
            )
        self.assertIn("shrinking the coverage denominator", str(caught.exception))
        self.store.connection.rollback()
        self.assertEqual(len(self.store.population_ids(CORPUS)), 5)
        self.assertEqual(compute_coverage(self.store, CORPUS).declared_population, 5)

    def test_ulc_21_10_coverage_report_states_reconciling_counts(self):
        self._population()
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual(report.declared_scope, "declared population of this corpus")
        self.assertEqual(report.declared_population, 5)
        self.assertEqual(report.excluded, 1)
        self.assertEqual(report.in_scope_total, 4)
        self.assertEqual(report.resolved, 1)
        self.assertEqual(report.missing, 1)
        self.assertEqual(report.unavailable, 1)
        self.assertEqual(report.unresolved_other, 1)
        self.assertEqual(report.unresolved, 3)
        self.assertEqual(report.filtered, 0)
        self.assertEqual(report.shown, 4)

    def test_ulc_21_10_unreconciled_counts_are_refused(self):
        with self.assertRaises(CoverageReconciliationRefused) as caught:
            CoverageReport(
                declared_scope="scope",
                declared_population=10,
                in_scope_total=10,
                resolved=7,
                unresolved=2,
                excluded=0,
                filtered=0,
                missing=2,
                unavailable=0,
                unresolved_other=0,
                shown=10,
            )
        self.assertIsInstance(caught.exception, CoverageReconciliationRefused)
        self.assertNotEqual(caught.exception.residual, 0)
        self.assertFalse(caught.exception.investigation_item["rounded"])
        self.assertNotIn("footnote", str(caught.exception))

    def test_ulc_16_02_residual_is_surfaced_and_not_rounded(self):
        balanced = reconcile_boundary(sources=10, sinks=4, exclusions=3, observed=3)
        self.assertEqual(balanced["residual"], 0)
        self.assertFalse(balanced["rounded"])
        with self.assertRaises(CoverageReconciliationRefused) as caught:
            reconcile_boundary(
                sources=10,
                sinks=4,
                exclusions=3,
                observed=2,
                round_residual=True,
            )
        self.assertEqual(caught.exception.residual, 1)
        self.assertFalse(caught.exception.investigation_item["rounded"])

    def test_ulc_21_02_view_declares_scope_before_any_total(self):
        with self.assertRaises(ViewScopeRequired):
            ViewSpec(
                corpus_id="",
                version="v1",
                inclusion_rules=("keep",),
                scope_boundary="local",
            )
        with self.assertRaises(ViewScopeRequired):
            create_view(
                self.store,
                corpus_id=CORPUS,
                version="v1",
                inclusion_rules=["keep"],
                scope_boundary="",
                created_at=T0,
            )
        self.assertEqual(self.store.view_rows(), [])
        self.store.declare_population_member(CORPUS, "b")
        ingest(self.store, member_id="b", evidence_state=EvidenceState.SUPPORTED, evidence_reason="reviewed")
        view = create_view(
            self.store,
            corpus_id=CORPUS,
            version="v1",
            inclusion_rules=["records pinned to this corpus"],
            scope_boundary="local single corpus",
            created_at=T0,
        )
        self.assertEqual(view.corpus_id, CORPUS)
        self.assertEqual(view.version, "v1")
        self.assertEqual(view.inclusion_rules, ("records pinned to this corpus",))
        self.assertEqual(view.scope_boundary, "local single corpus")
        self.assertTrue(view.complete)

    def test_ulc_21_05_filtered_view_discloses_omissions(self):
        self._population()
        view = create_view(
            self.store,
            corpus_id=CORPUS,
            version="v1",
            inclusion_rules=["records pinned to this corpus"],
            scope_boundary="local single corpus",
            filters=[{"field": "evidence_state", "equals": "supported"}],
            created_at=T0,
        )
        self.assertTrue(view.partial)
        self.assertFalse(view.complete)
        self.assertEqual(view.filters, ({"field": "evidence_state", "equals": "supported"},))
        self.assertEqual(view.shown_ids, ("b",))
        self.assertEqual(view.omitted_count, 3)
        self.assertEqual(set(view.omitted_ids), {"c", "d", "e"})

    def test_ulc_21_05_resolved_only_projection_cannot_be_labelled_complete(self):
        self._population()
        with self.assertRaises(CompleteLabelRefused):
            create_view(
                self.store,
                corpus_id=CORPUS,
                version="v1",
                inclusion_rules=["records pinned to this corpus"],
                scope_boundary="local single corpus",
                filters=[{"field": "evidence_state", "equals": "supported"}],
                label_complete=True,
                created_at=T0,
            )
        self.assertEqual(self.store.view_rows(), [])

    def test_ulc_21_11_view_records_generation_and_is_marked_stale(self):
        self.store.declare_population_member(CORPUS, "b")
        ingest(
            self.store,
            member_id="b",
            evidence_state=EvidenceState.SUPPORTED,
            evidence_reason="reviewed",
        )
        view = create_view(
            self.store,
            corpus_id=CORPUS,
            version="v1",
            inclusion_rules=["records pinned to this corpus"],
            scope_boundary="local single corpus",
            created_at=T0,
        )
        self.assertFalse(view.stale)
        self.assertEqual(view.staleness_value, "current")
        self.assertTrue(view.staleness_text)
        shown_before = view.shown_ids
        generation_before = view.evidence_generation
        ingest(self.store, assertion_text="later account", member_id="b")
        reread = read_view(self.store, view.view_id)
        self.assertTrue(reread.stale)
        self.assertEqual(reread.staleness_value, "stale")
        self.assertIn("snapshot is retained", reread.staleness_text)
        self.assertEqual(reread.shown_ids, shown_before)
        self.assertEqual(reread.evidence_generation, generation_before)
        recomputed = create_view(
            self.store,
            corpus_id=CORPUS,
            version="v1",
            inclusion_rules=["records pinned to this corpus"],
            scope_boundary="local single corpus",
            created_at=T1,
        )
        self.assertFalse(recomputed.stale)
        self.assertNotEqual(recomputed.view_id, view.view_id)
        self.assertTrue(read_view(self.store, view.view_id).stale)
        self.assertEqual(len(self.store.view_rows()), 2)

    def test_ulc_21_07_reopening_does_not_shrink_the_coverage_denominator(self):
        self.store.declare_population_member(CORPUS, "b")
        record = ingest(
            self.store,
            member_id="b",
            evidence_state=EvidenceState.SUPPORTED,
            evidence_reason="reviewed",
        )
        claim = self.store.register_claim(
            corpus_id=CORPUS,
            record_id=record.record_id,
            passage_locator="para:1",
            version_id="v1",
            member_id="b",
        )
        self.store.append_claim_state(
            claim_id=claim.claim_id,
            review_state="decided",
            decision="accepted",
            reason="initial decision",
            recorded_at=T0,
        )
        self.store.declare_dependency(
            claim_id=claim.claim_id,
            depends_on_kind="record",
            depends_on_id=record.record_id,
        )
        before = compute_coverage(self.store, CORPUS)
        self.assertEqual(before.declared_population, 1)
        self.assertEqual(before.resolved, 1)
        invalidate_evidence(self.store, record.record_id, reason="evidence withdrawn", recorded_at=T1)
        after = compute_coverage(self.store, CORPUS)
        self.assertEqual(after.declared_population, 1)
        self.assertEqual(after.resolved, 0)
        self.assertEqual(after.unresolved, 1)
        self.assertEqual(after.in_scope_total, before.in_scope_total)
        with self.assertRaises(DenominatorShrinkRefused):
            compute_coverage(self.store, CORPUS, denominator=0)


if __name__ == "__main__":
    unittest.main()
