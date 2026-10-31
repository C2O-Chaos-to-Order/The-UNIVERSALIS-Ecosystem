"""Stage P0. Requirement identifiers are ULC-<tablet>-<clause>."""

import sqlite3
import unittest

import bootstrap  # noqa: F401
from support import CORPUS, SOURCE, T0, T1, T2, T3, T4, ingest, memory_store, register_basics

from universalis.errors import (
    ClockCollapseRefused,
    FieldDerivationRefused,
    HistoricalAuthorityNotInherited,
    InPlaceOverwriteRefused,
    InsufficientClaimPointer,
    RoleInferenceRefused,
    TimestampOffsetRequired,
    TraceLinksRequired,
    UntypedReferenceRejected,
)
from universalis.states import EvidenceState, ReferentType, order_timestamps
from universalis.store import Store


class StageP0RecordsTest(unittest.TestCase):
    def setUp(self):
        self.store = register_basics(memory_store())

    def test_record_types_round_trip(self):
        record = ingest(self.store, assertion_text="round trip", member_id="m1")
        claim = self.store.register_claim(
            corpus_id=CORPUS,
            record_id=record.record_id,
            passage_locator="para:2",
            version_id="v1",
            title="A title",
            member_id="m1",
        )
        dependency = self.store.declare_dependency(
            claim_id=claim.claim_id,
            depends_on_kind="record",
            depends_on_id=record.record_id,
        )
        reference = self.store.add_reference(
            owner_id=record.record_id,
            referent_type=ReferentType.ARTIFACT,
            referent_id="artifact-1",
        )
        corpus = self.store.corpus(CORPUS)
        source = self.store.get_source(SOURCE, "1")
        self.assertEqual(corpus.version, "v1")
        self.assertEqual(source.digest, "digest-1")
        self.assertEqual(self.store.get_record(record.record_id).assertion_text, "round trip")
        self.assertEqual(self.store.get_claim(claim.claim_id).passage_locator, "para:2")
        self.assertEqual(dependency.depends_on_id, record.record_id)
        self.assertEqual(reference.referent_type, "artifact")

    def test_ulc_00_02_typed_reference_round_trips(self):
        record = ingest(self.store)
        reference = self.store.add_reference(
            owner_id=record.record_id,
            referent_type="observation",
            referent_id="obs-9",
        )
        loaded = self.store.references_for(record.record_id)
        self.assertEqual(loaded, [reference])
        self.assertEqual(loaded[0].referent_type, "observation")

    def test_ulc_00_02_untyped_reference_is_rejected(self):
        record = ingest(self.store)
        for referent_type in (None, "", "document"):
            with self.assertRaises(UntypedReferenceRejected):
                self.store.add_reference(
                    owner_id=record.record_id,
                    referent_type=referent_type,
                    referent_id="x",
                )
        self.assertEqual(self.store.references_for(record.record_id), [])

    def test_ulc_00_05_source_transformation_and_authorization_are_separate(self):
        record = ingest(
            self.store,
            source_ref="source:pinned",
            transformation_history=["normalized whitespace"],
            present_use_authorization="not-authorized",
        )
        loaded = self.store.get_record(record.record_id)
        self.assertEqual(loaded.source_ref, "source:pinned")
        self.assertEqual(loaded.transformation_history, ("normalized whitespace",))
        self.assertEqual(loaded.present_use_authorization, "not-authorized")
        self.assertNotEqual(loaded.present_use_authorization, loaded.source_ref)
        omitted = ingest(self.store, source_ref="source:pinned", assertion_text="second")
        self.assertEqual(omitted.present_use_authorization, "unknown")
        self.assertNotEqual(omitted.present_use_authorization, omitted.source_ref)

    def test_ulc_00_05_present_use_authorization_is_not_derived(self):
        record = ingest(self.store, source_ref="source:pinned")
        with self.assertRaises(FieldDerivationRefused):
            self.store.derive_present_use_authorization(record.record_id)
        self.assertEqual(
            self.store.get_record(record.record_id).present_use_authorization,
            "unknown",
        )

    def test_ulc_00_06_summary_retains_resolvable_trace_links(self):
        first = ingest(self.store, assertion_text="alpha")
        second = ingest(self.store, assertion_text="beta")
        summary = self.store.create_summary(
            summary="two accounts",
            constituent_ids=[first.record_id, second.record_id],
        )
        resolved = self.store.resolve_summary(summary.aggregation_id)
        self.assertEqual([item.record_id for item in resolved], [first.record_id, second.record_id])
        self.assertEqual(summary.constituent_ids, (first.record_id, second.record_id))

    def test_ulc_00_06_summary_without_trace_links_is_rejected(self):
        with self.assertRaises(TraceLinksRequired):
            self.store.create_summary(summary="floating", constituent_ids=[])
        missing = ingest(self.store)
        with self.assertRaises(TraceLinksRequired):
            self.store.create_summary(
                summary="broken link",
                constituent_ids=[missing.record_id, "not-a-record"],
            )

    def test_ulc_00_10_received_text_retains_source_editor_version_and_witnesses(self):
        prior = ingest(
            self.store,
            version="v1",
            source_ref="source:pinned",
            editor="editor-a",
            witness_history=[{"witness_id": "w1", "note": "first"}],
            authority_claim="editor-verified",
        )
        corrected = self.store.correct_record(
            lineage_id=prior.lineage_id,
            assertion_text="revised wording",
            version="v2",
            evidence_state=EvidenceState.PENDING_REVIEW,
            evidence_reason="a later witness",
            evidence_provenance="witness:w2",
            correction_time=T2,
            ingestion_time=T2,
            editor="editor-b",
            witness_history=[{"witness_id": "w2", "note": "second"}],
            source_ref="source:pinned",
        )
        retained = self.store.get_record(prior.record_id)
        self.assertEqual(retained.version, "v1")
        self.assertEqual(retained.editor, "editor-a")
        self.assertEqual(retained.source_ref, "source:pinned")
        self.assertEqual(retained.witness_history, ({"witness_id": "w1", "note": "first"},))
        self.assertEqual(corrected.supersedes_record_id, prior.record_id)
        self.assertEqual(corrected.version, "v2")
        self.assertEqual(corrected.editor, "editor-b")

    def test_ulc_00_10_present_wording_does_not_inherit_historical_authority(self):
        prior = ingest(self.store, authority_claim="editor-verified")
        before = len(self.store.history(prior.lineage_id))
        with self.assertRaises(HistoricalAuthorityNotInherited):
            self.store.correct_record(
                lineage_id=prior.lineage_id,
                assertion_text="revised wording",
                version="v2",
                evidence_state=EvidenceState.PENDING_REVIEW,
                evidence_reason="correction",
                evidence_provenance="witness:w2",
                correction_time=T2,
                ingestion_time=T2,
                inherit_authority=True,
            )
        self.assertEqual(len(self.store.history(prior.lineage_id)), before)
        corrected = self.store.correct_record(
            lineage_id=prior.lineage_id,
            assertion_text="revised wording",
            version="v2",
            evidence_state=EvidenceState.PENDING_REVIEW,
            evidence_reason="correction",
            evidence_provenance="witness:w2",
            correction_time=T2,
            ingestion_time=T2,
        )
        self.assertEqual(corrected.authority_claim, "unknown")
        self.assertEqual(self.store.get_record(prior.record_id).authority_claim, "editor-verified")
        with self.assertRaises(HistoricalAuthorityNotInherited):
            self.store.inherit_historical_authority(prior.lineage_id)

    def test_ulc_18_02_provenance_roles_are_distinct_fields(self):
        record = ingest(
            self.store,
            role_source="source-role",
            role_author="author-role",
            role_recorder="recorder-role",
            role_editor="editor-role",
            role_reviewer="reviewer-role",
            role_custodian="custodian-role",
        )
        loaded = self.store.get_record(record.record_id)
        roles = [
            loaded.role_source,
            loaded.role_author,
            loaded.role_recorder,
            loaded.role_editor,
            loaded.role_reviewer,
            loaded.role_custodian,
        ]
        self.assertEqual(len(set(roles)), 6)

    def test_ulc_18_02_role_is_not_inferred_from_another(self):
        record = ingest(self.store, role_source="source-role", role_author=None)
        self.assertEqual(record.role_author, "unknown")
        self.assertNotEqual(record.role_author, record.role_source)
        with self.assertRaises(RoleInferenceRefused):
            self.store.infer_role(record.record_id, "role_author")
        self.assertEqual(self.store.get_record(record.record_id).role_author, "unknown")

    def test_ulc_18_03_claim_resolves_to_passage_and_version(self):
        record = ingest(self.store)
        claim = self.store.register_claim(
            corpus_id=CORPUS,
            record_id=record.record_id,
            passage_locator="section:4",
            version_id="v3",
            title="Optional title",
            document_ref="doc-1",
        )
        loaded = self.store.get_claim(claim.claim_id)
        self.assertEqual(loaded.passage_locator, "section:4")
        self.assertEqual(loaded.version_id, "v3")

    def test_ulc_18_03_title_alone_is_rejected(self):
        record = ingest(self.store)
        with self.assertRaises(InsufficientClaimPointer):
            self.store.register_claim(
                corpus_id=CORPUS,
                record_id=record.record_id,
                passage_locator=None,
                version_id=None,
                title="The Book",
                document_ref="doc-1",
            )
        with self.assertRaises(InsufficientClaimPointer):
            self.store.register_claim(
                corpus_id=CORPUS,
                record_id=record.record_id,
                passage_locator="para:1",
                version_id=None,
            )

    def test_ulc_18_04_four_clocks_are_stored_separately(self):
        record = ingest(
            self.store,
            event_time=T1,
            report_time=T2,
            correction_time=T3,
            ingestion_time=T4,
            clocks_differ=True,
        )
        loaded = self.store.get_record(record.record_id)
        clocks = [loaded.event_time, loaded.report_time, loaded.correction_time, loaded.ingestion_time]
        self.assertEqual(len(set(clocks)), 4)
        for value in clocks:
            self.assertTrue(value.endswith("+00:00") or "T" in value)

    def test_ulc_18_04_differing_clocks_are_not_collapsed(self):
        with self.assertRaises(ClockCollapseRefused):
            ingest(
                self.store,
                event_time=T1,
                report_time=T1,
                correction_time=T1,
                ingestion_time=T1,
                clocks_differ=True,
            )

    def test_ulc_18_05_offset_timestamp_round_trips_and_orders(self):
        record = ingest(self.store, event_time="2026-01-01T00:00:00Z", ingestion_time=T4)
        self.assertIn("+00:00", self.store.get_record(record.record_id).event_time)
        ordered = order_timestamps(
            ["2026-01-01T16:00:00+00:00", "2026-01-01T12:00:00-05:00"]
        )
        self.assertLess(ordered[0].instant, ordered[1].instant)
        self.assertEqual(ordered[0].text.startswith("2026-01-01T16:00:00"), True)

    def test_ulc_18_05_timestamp_without_offset_is_rejected(self):
        with self.assertRaises(TimestampOffsetRequired):
            order_timestamps(["2026-01-01T00:00:00", T1])
        with self.assertRaises(TimestampOffsetRequired):
            ingest(self.store, ingestion_time="2026-01-01T00:00:00")

    def test_ulc_18_06_correction_appends_and_retains_prior_belief(self):
        prior = ingest(self.store, assertion_text="first account", evidence_state=EvidenceState.DISPUTED)
        corrected = self.store.correct_record(
            lineage_id=prior.lineage_id,
            assertion_text="second account",
            version="2",
            evidence_state=EvidenceState.PENDING_REVIEW,
            evidence_reason="later witness",
            evidence_provenance="witness:w2",
            correction_time=T2,
            ingestion_time=T2,
        )
        retained = self.store.get_record(prior.record_id)
        self.assertEqual(retained.assertion_text, "first account")
        self.assertEqual(retained.evidence_state, "disputed")
        self.assertEqual(retained.superseded_by, corrected.record_id)
        self.assertEqual(corrected.prior_belief, "disputed")
        self.assertEqual(corrected.assertion_text, "second account")
        self.assertEqual(len(self.store.history(prior.lineage_id)), 2)
        self.assertIsNone(self.store.current_record(prior.lineage_id).superseded_by)
        self.assertEqual(self.store.current_record(prior.lineage_id).record_id, corrected.record_id)

    def test_ulc_18_06_in_place_overwrite_is_refused(self):
        prior = ingest(self.store, assertion_text="first account")
        with self.assertRaises(InPlaceOverwriteRefused):
            self.store.correct_in_place(prior.record_id, assertion_text="tampered")
        self.assertEqual(self.store.get_record(prior.record_id).assertion_text, "first account")
        with self.assertRaises(sqlite3.IntegrityError) as caught:
            self.store.connection.execute(
                "UPDATE records SET assertion_text = ? WHERE record_id = ?",
                ("tampered", prior.record_id),
            )
        self.assertIn("in-place overwrite", str(caught.exception))
        self.store.connection.rollback()
        self.assertEqual(self.store.get_record(prior.record_id).assertion_text, "first account")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.connection.execute(
                "DELETE FROM records WHERE record_id = ?",
                (prior.record_id,),
            )
        self.store.connection.rollback()
        self.assertEqual(self.store.get_record(prior.record_id).assertion_text, "first account")


if __name__ == "__main__":
    unittest.main()
