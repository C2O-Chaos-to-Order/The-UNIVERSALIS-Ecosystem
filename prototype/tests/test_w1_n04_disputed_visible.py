"""N04 (Wave 1): a live DISPUTED account stays visible in coverage.

Owner policy (Kyle Steen, 2026-11-08): disputed live evidence stays VISIBLE in
coverage, flagged DISPUTED, and is never counted as resolved. A later,
separately ingested supported account for the same member does not hide it.
Only an explicit correction of the disputed lineage itself (which supersedes
that record while keeping its history) removes the flag.
"""

import unittest

import bootstrap  # noqa: F401
from support import CORPUS, T0, T1, ingest, memory_store, register_basics

from universalis.coverage import compute_coverage
from universalis.states import EvidenceState


class DisputedEvidenceStaysVisibleTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())
        self.store.declare_population_member(CORPUS, "m")

    def _disputed_then_supported(self):
        disputed = ingest(self.store, member_id="m", assertion_text="disputed original",
                          evidence_state=EvidenceState.DISPUTED, evidence_reason="witnesses disagree")
        ingest(self.store, member_id="m", assertion_text="later contrary assertion",
               evidence_state=EvidenceState.SUPPORTED, evidence_reason="reviewed")
        return disputed

    def test_audit_reproduction_disputed_live_lineage_is_not_resolved(self):
        self._disputed_then_supported()
        self.assertEqual(len(self.store.records_in_corpus(CORPUS)), 2)
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual(report.resolved, 0)
        self.assertEqual(report.unresolved, 1)

    def test_disputed_member_is_flagged_and_listed(self):
        self._disputed_then_supported()
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual(report.disputed, 1)
        self.assertEqual(report.disputed_members, ("m",))
        self.assertLessEqual(report.disputed, report.unresolved_other)

    def test_supported_then_disputed_order_also_flags(self):
        ingest(self.store, member_id="m", assertion_text="supported first",
               evidence_state=EvidenceState.SUPPORTED, evidence_reason="reviewed")
        ingest(self.store, member_id="m", assertion_text="disputed later",
               evidence_state=EvidenceState.DISPUTED, evidence_reason="new witness")
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual((report.resolved, report.disputed), (0, 1))

    def test_single_supported_record_still_resolves(self):
        ingest(self.store, member_id="m", assertion_text="only account",
               evidence_state=EvidenceState.SUPPORTED, evidence_reason="reviewed")
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual((report.resolved, report.disputed, report.disputed_members), (1, 0, ()))

    def test_explicit_correction_of_disputed_lineage_clears_flag_and_keeps_history(self):
        disputed = self._disputed_then_supported()
        self.store.correct_record(
            lineage_id=disputed.lineage_id, assertion_text="dispute adjudicated", version="2",
            evidence_state=EvidenceState.SUPPORTED, evidence_reason="owner adjudication recorded",
            evidence_provenance="witness:w1", correction_time=T1, ingestion_time=T1,
            witness_history=[{"witness_id": "w1", "note": "adjudicated"}],
            editor="editor-a", role_source="archive-a", role_recorder="recorder-a",
        )
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual((report.resolved, report.disputed), (1, 0))
        history = self.store.history(disputed.lineage_id)
        self.assertEqual([r.evidence_state for r in history][0], "disputed")
        self.assertEqual(len(history), 2)

    def test_two_members_only_disputed_one_is_flagged(self):
        self.store.declare_population_member(CORPUS, "n")
        self._disputed_then_supported()
        ingest(self.store, member_id="n", assertion_text="clean",
               evidence_state=EvidenceState.SUPPORTED, evidence_reason="reviewed")
        report = compute_coverage(self.store, CORPUS)
        self.assertEqual((report.resolved, report.unresolved, report.disputed), (1, 1, 1))
        self.assertEqual(report.disputed_members, ("m",))

    def test_mutation_latest_row_wins_is_detected(self):
        """In-process mutation: restore latest-row-wins classification."""
        from universalis import coverage
        original = coverage._live_records_for_member
        coverage._live_records_for_member = lambda store, corpus_id, member_id: [
            r for r in [store.current_record_for_member(corpus_id, member_id)] if r is not None]
        try:
            self._disputed_then_supported()
            report = compute_coverage(self.store, CORPUS)
            self.assertEqual(report.resolved, 1, "mutant should hide the dispute")
        finally:
            coverage._live_records_for_member = original


if __name__ == "__main__":
    unittest.main()
