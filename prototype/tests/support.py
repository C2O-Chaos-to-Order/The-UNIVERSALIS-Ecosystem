"""Shared fixtures. Importing this module also puts the package on sys.path."""

import bootstrap  # noqa: F401

from universalis.states import EvidenceState
from universalis.store import Store

T0 = "2026-01-01T00:00:00+00:00"
T1 = "2026-01-02T00:00:00+00:00"
T2 = "2026-02-01T00:00:00+00:00"
T3 = "2026-03-01T08:00:00-05:00"
T4 = "2026-04-01T00:00:00+00:00"
CORPUS = "corpus-1"
SOURCE = "source-1"


def memory_store() -> Store:
    return Store(":memory:")


def register_basics(store: Store) -> Store:
    store.register_corpus(
        corpus_id=CORPUS,
        version="v1",
        inclusion_rules=["records pinned to this corpus"],
        scope_boundary="local single corpus",
        declared_scope="declared population of this corpus",
        registered_at=T0,
    )
    store.register_source(
        source_id=SOURCE,
        version="1",
        identity="pinned-origin",
        digest="digest-1",
        retrieval_time=T0,
        review_scope="full",
        provenance="retrieved and pinned",
        resolve_limit=1,
    )
    return store


def ingest(store: Store, **overrides):
    fields = {
        "corpus_id": CORPUS,
        "assertion_text": "an account",
        "version": "1",
        "evidence_state": EvidenceState.UNKNOWN,
        "evidence_reason": "not yet reviewed",
        "evidence_provenance": "witness:w1",
        "ingestion_time": T0,
        "role_source": "archive-a",
        "role_recorder": "recorder-a",
        "source_ref": SOURCE,
        "editor": "editor-a",
        "witness_history": [{"witness_id": "w1", "note": "first account"}],
    }
    fields.update(overrides)
    return store.ingest_record(**fields)
