"""SQLite store for corpora, sources, records, claims, and dependencies.

Corrections insert a new row. The only column on ``records`` that a later
write may change is ``superseded_by``, and a trigger refuses every other
update and every delete. That column is a link to the successor, not a change
to the prior account.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass

from universalis.errors import (
    AnalogyCannotPopulateSource,
    ClockCollapseRefused,
    ConstituentDiscarded,
    ContradictionDropRefused,
    ContradictionMergeRefused,
    DenominatorShrinkRefused,
    FieldDerivationRefused,
    HistoricalAuthorityNotInherited,
    InPlaceOverwriteRefused,
    InsufficientClaimPointer,
    LineageNotFound,
    PlausibleSubstituteRejected,
    PopulationMemberMissing,
    RecencyDoesNotResolve,
    ReopeningIsNotRejection,
    ResolutionRequiresGrounds,
    RetentionDoesNotPromote,
    RoleInferenceRefused,
    SourceNotScopedOrigin,
    StateCollapseRefused,
    TraceLinksRequired,
    UntypedReferenceRejected,
    VocabularyBoundaryError,
)
from universalis.states import (
    EXPLICIT_UNKNOWN,
    require_evidence_state,
    require_referent_type,
    require_route_outcome,
    require_timestamp_or_unknown,
    require_transport_outcome,
)

_ANALOGY_KINDS = frozenset(
    {"analogy", "metaphor", "figurative", "figure of speech"}
)

_SCHEMA = """
CREATE TABLE corpora (
    corpus_id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    inclusion_rules TEXT NOT NULL,
    scope_boundary TEXT NOT NULL,
    declared_scope TEXT NOT NULL,
    evidence_generation INTEGER NOT NULL,
    registered_at TEXT NOT NULL
);

CREATE TABLE population_members (
    corpus_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    PRIMARY KEY (corpus_id, member_id),
    FOREIGN KEY (corpus_id) REFERENCES corpora(corpus_id)
);

CREATE TABLE sources (
    source_id TEXT NOT NULL,
    version TEXT NOT NULL,
    identity TEXT NOT NULL,
    digest TEXT NOT NULL,
    retrieval_time TEXT NOT NULL,
    review_scope TEXT NOT NULL,
    provenance TEXT NOT NULL,
    resolve_limit INTEGER NOT NULL,
    kind TEXT NOT NULL,
    PRIMARY KEY (source_id, version)
);

CREATE TABLE records (
    record_id TEXT PRIMARY KEY,
    lineage_id TEXT NOT NULL,
    corpus_id TEXT NOT NULL,
    member_id TEXT,
    assertion_text TEXT NOT NULL,
    version TEXT NOT NULL,
    role_source TEXT NOT NULL,
    role_author TEXT NOT NULL,
    role_recorder TEXT NOT NULL,
    role_editor TEXT NOT NULL,
    role_reviewer TEXT NOT NULL,
    role_custodian TEXT NOT NULL,
    evidence_state TEXT NOT NULL,
    evidence_reason TEXT NOT NULL,
    evidence_provenance TEXT NOT NULL,
    custody_state TEXT NOT NULL,
    event_time TEXT NOT NULL,
    report_time TEXT NOT NULL,
    correction_time TEXT NOT NULL,
    ingestion_time TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    transformation_history TEXT NOT NULL,
    present_use_authorization TEXT NOT NULL,
    authority_claim TEXT NOT NULL,
    witness_history TEXT NOT NULL,
    editor TEXT NOT NULL,
    prior_belief TEXT NOT NULL,
    supersedes_record_id TEXT,
    superseded_by TEXT,
    CHECK (evidence_state IN (
        'supported', 'disputed', 'missing', 'stale', 'corrupted',
        'pending_review', 'unknown'
    ))
);

CREATE TABLE typed_references (
    reference_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    referent_type TEXT NOT NULL,
    referent_id TEXT NOT NULL,
    CHECK (referent_type IN (
        'artifact', 'model', 'observation', 'role', 'authority'
    ))
);

CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    member_id TEXT,
    record_id TEXT NOT NULL,
    passage_locator TEXT NOT NULL,
    version_id TEXT NOT NULL,
    title TEXT,
    document_ref TEXT
);

CREATE TABLE claim_states (
    state_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    review_state TEXT NOT NULL,
    decision TEXT NOT NULL,
    prior_decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    seq INTEGER NOT NULL
);

CREATE TABLE dependencies (
    dependency_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    depends_on_kind TEXT NOT NULL,
    depends_on_id TEXT NOT NULL,
    CHECK (depends_on_kind IN ('record', 'claim'))
);

CREATE TABLE contradictions (
    contradiction_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE contradiction_witnesses (
    witness_row_id TEXT PRIMARY KEY,
    contradiction_id TEXT NOT NULL,
    witness_id TEXT NOT NULL,
    account TEXT NOT NULL,
    witnessed_at TEXT NOT NULL,
    seq INTEGER NOT NULL
);

CREATE TABLE resolutions (
    resolution_id TEXT PRIMARY KEY,
    contradiction_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    grounds TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE aggregations (
    aggregation_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    constituent_ids TEXT NOT NULL,
    differences TEXT NOT NULL
);

CREATE TABLE exclusions (
    corpus_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (corpus_id, member_id)
);

CREATE TABLE route_log (
    route_id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    member_id TEXT,
    source_id TEXT,
    outcome TEXT NOT NULL,
    transport TEXT,
    detail TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    CHECK (outcome IN (
        'ok', 'empty', 'missing', 'failed_request', 'truncated',
        'denied', 'unavailable'
    ))
);

CREATE TABLE retention_notes (
    note_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    duration TEXT NOT NULL,
    evidence_state_at_note TEXT NOT NULL
);

CREATE TABLE views (
    view_id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL,
    version TEXT NOT NULL,
    inclusion_rules TEXT NOT NULL,
    scope_boundary TEXT NOT NULL,
    filters TEXT NOT NULL,
    partial INTEGER NOT NULL,
    complete INTEGER NOT NULL,
    omitted_count INTEGER NOT NULL,
    omitted_ids TEXT NOT NULL,
    shown_ids TEXT NOT NULL,
    evidence_generation INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE audit_events (
    audit_id TEXT PRIMARY KEY,
    subject_kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    prior_decision TEXT NOT NULL,
    new_review_state TEXT NOT NULL,
    reason TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER records_append_only
BEFORE UPDATE ON records
FOR EACH ROW
WHEN (
    NEW.record_id IS NOT OLD.record_id
    OR NEW.lineage_id IS NOT OLD.lineage_id
    OR NEW.corpus_id IS NOT OLD.corpus_id
    OR NEW.member_id IS NOT OLD.member_id
    OR NEW.assertion_text IS NOT OLD.assertion_text
    OR NEW.version IS NOT OLD.version
    OR NEW.role_source IS NOT OLD.role_source
    OR NEW.role_author IS NOT OLD.role_author
    OR NEW.role_recorder IS NOT OLD.role_recorder
    OR NEW.role_editor IS NOT OLD.role_editor
    OR NEW.role_reviewer IS NOT OLD.role_reviewer
    OR NEW.role_custodian IS NOT OLD.role_custodian
    OR NEW.evidence_state IS NOT OLD.evidence_state
    OR NEW.evidence_reason IS NOT OLD.evidence_reason
    OR NEW.evidence_provenance IS NOT OLD.evidence_provenance
    OR NEW.custody_state IS NOT OLD.custody_state
    OR NEW.event_time IS NOT OLD.event_time
    OR NEW.report_time IS NOT OLD.report_time
    OR NEW.correction_time IS NOT OLD.correction_time
    OR NEW.ingestion_time IS NOT OLD.ingestion_time
    OR NEW.source_ref IS NOT OLD.source_ref
    OR NEW.transformation_history IS NOT OLD.transformation_history
    OR NEW.present_use_authorization IS NOT OLD.present_use_authorization
    OR NEW.authority_claim IS NOT OLD.authority_claim
    OR NEW.witness_history IS NOT OLD.witness_history
    OR NEW.editor IS NOT OLD.editor
    OR NEW.prior_belief IS NOT OLD.prior_belief
    OR NEW.supersedes_record_id IS NOT OLD.supersedes_record_id
)
BEGIN
    SELECT RAISE(ABORT, 'in-place overwrite of a prior account is refused');
END;

CREATE TRIGGER records_no_delete
BEFORE DELETE ON records
BEGIN
    SELECT RAISE(ABORT, 'deleting a prior account is refused');
END;

CREATE TRIGGER population_no_delete
BEFORE DELETE ON population_members
BEGIN
    SELECT RAISE(ABORT, 'shrinking the coverage denominator is refused');
END;

CREATE TRIGGER population_no_shrink_update
BEFORE UPDATE ON population_members
BEGIN
    SELECT RAISE(ABORT, 'shrinking the coverage denominator is refused');
END;
"""


def _new_id() -> str:
    return uuid.uuid4().hex


def _json_list(value: object) -> str:
    if value is None:
        return "[]"
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list")
    return json.dumps(list(value))


def _as_unknown(value: object) -> str:
    if value is None or value == "":
        return EXPLICIT_UNKNOWN
    return str(value)


@dataclass(frozen=True)
class Corpus:
    corpus_id: str
    version: str
    inclusion_rules: tuple
    scope_boundary: str
    declared_scope: str
    evidence_generation: int
    registered_at: str


@dataclass(frozen=True)
class Source:
    source_id: str
    version: str
    identity: str
    digest: str
    retrieval_time: str
    review_scope: str
    provenance: str
    resolve_limit: int
    kind: str


@dataclass(frozen=True)
class Record:
    record_id: str
    lineage_id: str
    corpus_id: str
    member_id: str | None
    assertion_text: str
    version: str
    role_source: str
    role_author: str
    role_recorder: str
    role_editor: str
    role_reviewer: str
    role_custodian: str
    evidence_state: str
    evidence_reason: str
    evidence_provenance: str
    custody_state: str
    event_time: str
    report_time: str
    correction_time: str
    ingestion_time: str
    source_ref: str
    transformation_history: tuple
    present_use_authorization: str
    authority_claim: str
    witness_history: tuple
    editor: str
    prior_belief: str
    supersedes_record_id: str | None
    superseded_by: str | None


@dataclass(frozen=True)
class Reference:
    reference_id: str
    owner_id: str
    referent_type: str
    referent_id: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    corpus_id: str
    member_id: str | None
    record_id: str
    passage_locator: str
    version_id: str
    title: str | None
    document_ref: str | None


@dataclass(frozen=True)
class ClaimState:
    state_id: str
    claim_id: str
    review_state: str
    decision: str
    prior_decision: str
    reason: str
    recorded_at: str
    seq: int


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    claim_id: str
    depends_on_kind: str
    depends_on_id: str


@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    subject_id: str
    scope: str
    created_at: str
    witnesses: tuple
    resolution_decision: str | None
    resolution_grounds: str | None
    evidence_state: str
    winning_account: str | None


@dataclass(frozen=True)
class Aggregation:
    aggregation_id: str
    summary: str
    constituent_ids: tuple
    differences: tuple


@dataclass(frozen=True)
class RouteLog:
    route_id: str
    corpus_id: str
    member_id: str | None
    source_id: str | None
    outcome: str
    transport: str | None
    detail: str
    recorded_at: str


@dataclass(frozen=True)
class AuditEvent:
    audit_id: str
    subject_kind: str
    subject_id: str
    event_type: str
    prior_decision: str
    new_review_state: str
    reason: str
    recorded_at: str


def _record_from_row(row: sqlite3.Row) -> Record:
    return Record(
        record_id=row["record_id"],
        lineage_id=row["lineage_id"],
        corpus_id=row["corpus_id"],
        member_id=row["member_id"],
        assertion_text=row["assertion_text"],
        version=row["version"],
        role_source=row["role_source"],
        role_author=row["role_author"],
        role_recorder=row["role_recorder"],
        role_editor=row["role_editor"],
        role_reviewer=row["role_reviewer"],
        role_custodian=row["role_custodian"],
        evidence_state=row["evidence_state"],
        evidence_reason=row["evidence_reason"],
        evidence_provenance=row["evidence_provenance"],
        custody_state=row["custody_state"],
        event_time=row["event_time"],
        report_time=row["report_time"],
        correction_time=row["correction_time"],
        ingestion_time=row["ingestion_time"],
        source_ref=row["source_ref"],
        transformation_history=tuple(json.loads(row["transformation_history"])),
        present_use_authorization=row["present_use_authorization"],
        authority_claim=row["authority_claim"],
        witness_history=tuple(json.loads(row["witness_history"])),
        editor=row["editor"],
        prior_belief=row["prior_belief"],
        supersedes_record_id=row["supersedes_record_id"],
        superseded_by=row["superseded_by"],
    )


class Store:
    def __init__(self, path: str = ":memory:"):
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        self._conn.close()

    def _insert(self, table: str, row: dict) -> None:
        columns = list(row)
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(columns)
        self._conn.execute(
            f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
            [row[column] for column in columns],
        )

    def register_corpus(
        self,
        *,
        corpus_id: str,
        version: str,
        inclusion_rules: list,
        scope_boundary: str,
        declared_scope: str,
        registered_at: str,
    ) -> Corpus:
        if not corpus_id or not version or not scope_boundary or not declared_scope:
            raise ValueError("a corpus needs identity, version, scope, and a declared scope")
        if inclusion_rules is None:
            raise ValueError("inclusion rules must be declared")
        registered = str(require_timestamp_or_unknown(registered_at))
        if registered == EXPLICIT_UNKNOWN:
            raise ValueError("corpus registration time needs an offset")
        self._insert(
            "corpora",
            {
                "corpus_id": corpus_id,
                "version": version,
                "inclusion_rules": json.dumps(list(inclusion_rules)),
                "scope_boundary": scope_boundary,
                "declared_scope": declared_scope,
                "evidence_generation": 1,
                "registered_at": registered,
            },
        )
        self._conn.commit()
        return self.corpus(corpus_id)

    def corpus(self, corpus_id: str) -> Corpus:
        row = self._conn.execute(
            "SELECT * FROM corpora WHERE corpus_id = ?", (corpus_id,)
        ).fetchone()
        if row is None:
            raise KeyError(corpus_id)
        return Corpus(
            corpus_id=row["corpus_id"],
            version=row["version"],
            inclusion_rules=tuple(json.loads(row["inclusion_rules"])),
            scope_boundary=row["scope_boundary"],
            declared_scope=row["declared_scope"],
            evidence_generation=row["evidence_generation"],
            registered_at=row["registered_at"],
        )

    def generation(self, corpus_id: str) -> int:
        return self.corpus(corpus_id).evidence_generation

    def bump_generation(self, corpus_id: str) -> int:
        current = self.generation(corpus_id)
        self._conn.execute(
            "UPDATE corpora SET evidence_generation = ? WHERE corpus_id = ?",
            (current + 1, corpus_id),
        )
        self._conn.commit()
        return current + 1

    def register_source(
        self,
        *,
        source_id: str,
        version: str,
        identity: str,
        digest: str,
        retrieval_time: str,
        review_scope: str,
        provenance: str,
        resolve_limit: int = 1,
        kind: str = "origin",
        figurative: bool = False,
    ) -> Source:
        if figurative or str(kind).strip().lower() in _ANALOGY_KINDS:
            raise AnalogyCannotPopulateSource(
                "ULC-16-05: an analogy or metaphor cannot populate a source field"
            )
        missing = [
            name
            for name, value in (
                ("source_id", source_id),
                ("version", version),
                ("identity", identity),
                ("digest", digest),
                ("retrieval_time", retrieval_time),
                ("review_scope", review_scope),
                ("provenance", provenance),
            )
            if value is None or str(value).strip() == ""
        ]
        if missing:
            raise SourceNotScopedOrigin(
                "ULC-16-05: a source must resolve to a scoped origin with "
                f"declared provenance; missing {', '.join(missing)}"
            )
        retrieval = require_timestamp_or_unknown(retrieval_time)
        if retrieval == EXPLICIT_UNKNOWN:
            raise SourceNotScopedOrigin(
                "ULC-16-05: a source retrieval time must carry an offset"
            )
        self._insert(
            "sources",
            {
                "source_id": source_id,
                "version": version,
                "identity": identity,
                "digest": digest,
                "retrieval_time": retrieval,
                "review_scope": review_scope,
                "provenance": provenance,
                "resolve_limit": int(resolve_limit),
                "kind": kind,
            },
        )
        self._conn.commit()
        loaded = self.get_source(source_id, version)
        if loaded is None:
            raise SourceNotScopedOrigin("ULC-16-05: the source was not stored")
        return loaded

    def get_source(self, source_id: str, version: str | None = None) -> Source | None:
        if version is None:
            row = self._conn.execute(
                "SELECT * FROM sources WHERE source_id = ? ORDER BY version",
                (source_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT * FROM sources WHERE source_id = ? AND version = ?",
                (source_id, version),
            ).fetchone()
        if row is None:
            return None
        return Source(
            source_id=row["source_id"],
            version=row["version"],
            identity=row["identity"],
            digest=row["digest"],
            retrieval_time=row["retrieval_time"],
            review_scope=row["review_scope"],
            provenance=row["provenance"],
            resolve_limit=row["resolve_limit"],
            kind=row["kind"],
        )

    def declare_population_member(self, corpus_id: str, member_id: str) -> None:
        self.corpus(corpus_id)
        if not member_id:
            raise ValueError("a population member needs an id")
        self._insert(
            "population_members",
            {"corpus_id": corpus_id, "member_id": member_id},
        )
        self._conn.commit()

    def population_ids(self, corpus_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT member_id FROM population_members WHERE corpus_id = ? ORDER BY member_id",
            (corpus_id,),
        ).fetchall()
        return [row["member_id"] for row in rows]

    def shrink_population(self, corpus_id: str, member_id: str) -> None:
        raise DenominatorShrinkRefused(
            "ULC-18-10: removing a declared population member would shrink the "
            "coverage denominator and is refused"
        )

    def exclude_member(self, corpus_id: str, member_id: str, reason: str) -> None:
        if member_id not in self.population_ids(corpus_id):
            raise PopulationMemberMissing(member_id)
        if not reason:
            raise ValueError("an exclusion needs a reason")
        self._insert(
            "exclusions",
            {"corpus_id": corpus_id, "member_id": member_id, "reason": reason},
        )
        self._conn.commit()

    def exclusions(self, corpus_id: str) -> dict[str, str]:
        rows = self._conn.execute(
            "SELECT member_id, reason FROM exclusions WHERE corpus_id = ?",
            (corpus_id,),
        ).fetchall()
        return {row["member_id"]: row["reason"] for row in rows}

    def ingest_record(
        self,
        *,
        corpus_id: str,
        assertion_text: str,
        version: str,
        evidence_state: object,
        evidence_reason: str,
        evidence_provenance: str,
        ingestion_time: str,
        lineage_id: str | None = None,
        member_id: str | None = None,
        role_source: str | None = None,
        role_author: str | None = None,
        role_recorder: str | None = None,
        role_editor: str | None = None,
        role_reviewer: str | None = None,
        role_custodian: str | None = None,
        custody_state: str | None = None,
        event_time: str | None = None,
        report_time: str | None = None,
        correction_time: str | None = None,
        clocks_differ: bool = False,
        source_ref: str | None = None,
        transformation_history: list | None = None,
        present_use_authorization: str | None = None,
        authority_claim: str | None = None,
        witness_history: list | None = None,
        editor: str | None = None,
        record_id: str | None = None,
    ) -> Record:
        self.corpus(corpus_id)
        state = require_evidence_state(evidence_state)
        if not evidence_reason or not str(evidence_reason).strip():
            raise ValueError("an evidence state requires a reason")
        if not evidence_provenance or not str(evidence_provenance).strip():
            raise ValueError("an evidence state requires provenance")
        if not assertion_text or not version:
            raise ValueError("a record needs assertion text and a version")
        roles = {
            "role_source": _as_unknown(role_source),
            "role_author": _as_unknown(role_author),
            "role_recorder": _as_unknown(role_recorder),
            "role_editor": _as_unknown(role_editor),
            "role_reviewer": _as_unknown(role_reviewer),
            "role_custodian": _as_unknown(role_custodian),
        }
        clocks = {
            "event_time": require_timestamp_or_unknown(event_time),
            "report_time": require_timestamp_or_unknown(report_time),
            "correction_time": require_timestamp_or_unknown(correction_time),
            "ingestion_time": require_timestamp_or_unknown(ingestion_time),
        }
        if clocks["ingestion_time"] == EXPLICIT_UNKNOWN:
            raise ValueError("ingestion time needs an offset")
        if clocks_differ:
            concrete = [value for value in clocks.values() if value != EXPLICIT_UNKNOWN]
            if len(set(concrete)) < len(concrete):
                raise ClockCollapseRefused(
                    "ULC-18-04: clocks declared to differ were collapsed to one value"
                )
        custody = _as_unknown(custody_state)
        if custody_state is None:
            custody = EXPLICIT_UNKNOWN
        source_value = _as_unknown(source_ref)
        authorization = _as_unknown(present_use_authorization)
        authority = _as_unknown(authority_claim)
        history = list(witness_history or [])
        transforms = list(transformation_history or [])
        new_id = record_id or _new_id()
        self._insert(
            "records",
            {
                "record_id": new_id,
                "lineage_id": lineage_id or new_id,
                "corpus_id": corpus_id,
                "member_id": member_id,
                "assertion_text": assertion_text,
                "version": version,
                "evidence_state": state,
                "evidence_reason": evidence_reason,
                "evidence_provenance": evidence_provenance,
                "custody_state": custody,
                "source_ref": source_value,
                "transformation_history": _json_list(transforms),
                "present_use_authorization": authorization,
                "authority_claim": authority,
                "witness_history": _json_list(history),
                "editor": _as_unknown(editor),
                "prior_belief": "none",
                "supersedes_record_id": None,
                "superseded_by": None,
                **roles,
                **clocks,
            },
        )
        self._conn.execute(
            "UPDATE corpora SET evidence_generation = evidence_generation + 1 WHERE corpus_id = ?",
            (corpus_id,),
        )
        self._conn.commit()
        loaded = self.get_record(new_id)
        if loaded is None:
            raise RuntimeError("record insert was not readable")
        return loaded

    def correct_record(
        self,
        *,
        lineage_id: str,
        assertion_text: str,
        version: str,
        evidence_state: object,
        evidence_reason: str,
        evidence_provenance: str,
        correction_time: str,
        ingestion_time: str,
        witness_history: list | None = None,
        editor: str | None = None,
        role_source: str | None = None,
        role_author: str | None = None,
        role_recorder: str | None = None,
        role_editor: str | None = None,
        role_reviewer: str | None = None,
        role_custodian: str | None = None,
        custody_state: str | None = None,
        event_time: str | None = None,
        report_time: str | None = None,
        clocks_differ: bool = False,
        source_ref: str | None = None,
        transformation_history: list | None = None,
        present_use_authorization: str | None = None,
        authority_claim: str | None = None,
        inherit_authority: bool = False,
        member_id: str | None = None,
    ) -> Record:
        if inherit_authority:
            raise HistoricalAuthorityNotInherited(
                "ULC-00-10: present wording may not inherit historical authority"
            )
        prior = self.current_record(lineage_id)
        if prior is None:
            raise LineageNotFound(lineage_id)
        state = require_evidence_state(evidence_state)
        if not evidence_reason or not evidence_provenance:
            raise ValueError("a correction needs an evidence reason and provenance")
        roles = {
            "role_source": _as_unknown(role_source),
            "role_author": _as_unknown(role_author),
            "role_recorder": _as_unknown(role_recorder),
            "role_editor": _as_unknown(role_editor),
            "role_reviewer": _as_unknown(role_reviewer),
            "role_custodian": _as_unknown(role_custodian),
        }
        clocks = {
            "event_time": require_timestamp_or_unknown(event_time),
            "report_time": require_timestamp_or_unknown(report_time),
            "correction_time": require_timestamp_or_unknown(correction_time),
            "ingestion_time": require_timestamp_or_unknown(ingestion_time),
        }
        if clocks["correction_time"] == EXPLICIT_UNKNOWN or clocks["ingestion_time"] == EXPLICIT_UNKNOWN:
            raise ValueError("correction time and ingestion time need offsets")
        if clocks_differ:
            concrete = [value for value in clocks.values() if value != EXPLICIT_UNKNOWN]
            if len(set(concrete)) < len(concrete):
                raise ClockCollapseRefused(
                    "ULC-18-04: clocks declared to differ were collapsed to one value"
                )
        new_id = _new_id()
        linked_member = member_id if member_id is not None else prior.member_id
        self._insert(
            "records",
            {
                "record_id": new_id,
                "lineage_id": lineage_id,
                "corpus_id": prior.corpus_id,
                "member_id": linked_member,
                "assertion_text": assertion_text,
                "version": version,
                "evidence_state": state,
                "evidence_reason": evidence_reason,
                "evidence_provenance": evidence_provenance,
                "custody_state": _as_unknown(custody_state),
                "source_ref": _as_unknown(source_ref),
                "transformation_history": _json_list(list(transformation_history or [])),
                "present_use_authorization": _as_unknown(present_use_authorization),
                "authority_claim": _as_unknown(authority_claim),
                "witness_history": _json_list(list(witness_history or [])),
                "editor": _as_unknown(editor),
                "prior_belief": prior.evidence_state,
                "supersedes_record_id": prior.record_id,
                "superseded_by": None,
                **roles,
                **clocks,
            },
        )
        self._mark_superseded(prior.record_id, new_id)
        self._conn.execute(
            "UPDATE corpora SET evidence_generation = evidence_generation + 1 WHERE corpus_id = ?",
            (prior.corpus_id,),
        )
        self._conn.commit()
        loaded = self.get_record(new_id)
        if loaded is None:
            raise RuntimeError("correction insert was not readable")
        return loaded

    def _mark_superseded(self, prior_id: str, successor_id: str) -> None:
        self._conn.execute(
            "UPDATE records SET superseded_by = ? WHERE record_id = ?",
            (successor_id, prior_id),
        )

    def correct_in_place(self, record_id: str, **changes: object) -> None:
        raise InPlaceOverwriteRefused(
            "ULC-18-06: correction appends a new witnessed account; "
            "in-place overwrite of a prior account is refused"
        )

    def get_record(self, record_id: str) -> Record | None:
        row = self._conn.execute(
            "SELECT * FROM records WHERE record_id = ?", (record_id,)
        ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def current_record(self, lineage_id: str) -> Record | None:
        row = self._conn.execute(
            """
            SELECT * FROM records
            WHERE lineage_id = ? AND superseded_by IS NULL
            """,
            (lineage_id,),
        ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def history(self, lineage_id: str) -> list[Record]:
        rows = self._conn.execute(
            "SELECT * FROM records WHERE lineage_id = ? ORDER BY rowid",
            (lineage_id,),
        ).fetchall()
        return [_record_from_row(row) for row in rows]

    def records_in_corpus(self, corpus_id: str, *, current_only: bool = True) -> list[Record]:
        if current_only:
            rows = self._conn.execute(
                """
                SELECT * FROM records
                WHERE corpus_id = ? AND superseded_by IS NULL
                ORDER BY rowid
                """,
                (corpus_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM records WHERE corpus_id = ? ORDER BY rowid",
                (corpus_id,),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def current_record_for_member(self, corpus_id: str, member_id: str) -> Record | None:
        row = self._conn.execute(
            """
            SELECT * FROM records
            WHERE corpus_id = ? AND member_id = ? AND superseded_by IS NULL
            ORDER BY rowid DESC
            """,
            (corpus_id, member_id),
        ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def add_reference(self, *, owner_id: str, referent_type: object, referent_id: str) -> Reference:
        if not referent_id:
            raise UntypedReferenceRejected("ULC-00-02: a reference needs a referent id")
        parsed = require_referent_type(referent_type)
        reference_id = _new_id()
        self._insert(
            "typed_references",
            {
                "reference_id": reference_id,
                "owner_id": owner_id,
                "referent_type": parsed,
                "referent_id": referent_id,
            },
        )
        self._conn.commit()
        return Reference(reference_id, owner_id, parsed, referent_id)

    def references_for(self, owner_id: str) -> list[Reference]:
        rows = self._conn.execute(
            "SELECT * FROM typed_references WHERE owner_id = ? ORDER BY rowid",
            (owner_id,),
        ).fetchall()
        return [
            Reference(
                row["reference_id"],
                row["owner_id"],
                row["referent_type"],
                row["referent_id"],
            )
            for row in rows
        ]

    def register_claim(
        self,
        *,
        corpus_id: str,
        record_id: str,
        passage_locator: str | None,
        version_id: str | None,
        title: str | None = None,
        document_ref: str | None = None,
        member_id: str | None = None,
        claim_id: str | None = None,
    ) -> Claim:
        self.corpus(corpus_id)
        if self.get_record(record_id) is None:
            raise InsufficientClaimPointer(
                "ULC-18-03: a claim must resolve to a stored record"
            )
        if not passage_locator or not str(passage_locator).strip():
            raise InsufficientClaimPointer(
                "ULC-18-03: a title or document reference alone is insufficient; "
                "a precise passage is required"
            )
        if not version_id or not str(version_id).strip():
            raise InsufficientClaimPointer(
                "ULC-18-03: a title or document reference alone is insufficient; "
                "a version identifier is required"
            )
        new_id = claim_id or _new_id()
        self._insert(
            "claims",
            {
                "claim_id": new_id,
                "corpus_id": corpus_id,
                "member_id": member_id,
                "record_id": record_id,
                "passage_locator": passage_locator,
                "version_id": version_id,
                "title": title,
                "document_ref": document_ref,
            },
        )
        self._conn.commit()
        loaded = self.get_claim(new_id)
        if loaded is None:
            raise RuntimeError("claim insert was not readable")
        return loaded

    def get_claim(self, claim_id: str) -> Claim | None:
        row = self._conn.execute(
            "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
        ).fetchone()
        if row is None:
            return None
        return Claim(
            claim_id=row["claim_id"],
            corpus_id=row["corpus_id"],
            member_id=row["member_id"],
            record_id=row["record_id"],
            passage_locator=row["passage_locator"],
            version_id=row["version_id"],
            title=row["title"],
            document_ref=row["document_ref"],
        )

    def current_claim_for_member(self, corpus_id: str, member_id: str) -> Claim | None:
        row = self._conn.execute(
            """
            SELECT * FROM claims
            WHERE corpus_id = ? AND member_id = ?
            ORDER BY rowid DESC
            """,
            (corpus_id, member_id),
        ).fetchone()
        if row is None:
            return None
        return self.get_claim(row["claim_id"])

    def append_claim_state(
        self,
        *,
        claim_id: str,
        review_state: str,
        decision: str,
        reason: str,
        recorded_at: str,
    ) -> ClaimState:
        if self.get_claim(claim_id) is None:
            raise KeyError(claim_id)
        if review_state == "reopened" and decision == "rejected":
            raise ReopeningIsNotRejection(
                "ULC-21-07: a reopened claim has not been judged against"
            )
        recorded = require_timestamp_or_unknown(recorded_at)
        if recorded == EXPLICIT_UNKNOWN:
            raise ValueError("a claim state needs an offset timestamp")
        previous = self.claim_states(claim_id)
        prior_decision = previous[-1].decision if previous else "none"
        state = ClaimState(
            state_id=_new_id(),
            claim_id=claim_id,
            review_state=review_state,
            decision=decision,
            prior_decision=prior_decision,
            reason=reason,
            recorded_at=recorded,
            seq=len(previous) + 1,
        )
        self._insert(
            "claim_states",
            {
                "state_id": state.state_id,
                "claim_id": state.claim_id,
                "review_state": state.review_state,
                "decision": state.decision,
                "prior_decision": state.prior_decision,
                "reason": state.reason,
                "recorded_at": state.recorded_at,
                "seq": state.seq,
            },
        )
        self._conn.commit()
        return state

    def claim_states(self, claim_id: str) -> list[ClaimState]:
        rows = self._conn.execute(
            "SELECT * FROM claim_states WHERE claim_id = ? ORDER BY seq",
            (claim_id,),
        ).fetchall()
        return [
            ClaimState(
                state_id=row["state_id"],
                claim_id=row["claim_id"],
                review_state=row["review_state"],
                decision=row["decision"],
                prior_decision=row["prior_decision"],
                reason=row["reason"],
                recorded_at=row["recorded_at"],
                seq=row["seq"],
            )
            for row in rows
        ]

    def current_claim_state(self, claim_id: str) -> ClaimState | None:
        states = self.claim_states(claim_id)
        if not states:
            return None
        return states[-1]

    def declare_dependency(
        self, *, claim_id: str, depends_on_kind: str, depends_on_id: str
    ) -> Dependency:
        if self.get_claim(claim_id) is None:
            raise KeyError(claim_id)
        if depends_on_kind not in {"record", "claim"}:
            raise ValueError("a dependency kind is record or claim")
        if not depends_on_id:
            raise ValueError("a dependency needs an explicit target")
        if depends_on_kind == "record" and self.get_record(depends_on_id) is None:
            raise KeyError(depends_on_id)
        if depends_on_kind == "claim" and self.get_claim(depends_on_id) is None:
            raise KeyError(depends_on_id)
        dependency = Dependency(_new_id(), claim_id, depends_on_kind, depends_on_id)
        self._insert(
            "dependencies",
            {
                "dependency_id": dependency.dependency_id,
                "claim_id": dependency.claim_id,
                "depends_on_kind": dependency.depends_on_kind,
                "depends_on_id": dependency.depends_on_id,
            },
        )
        self._conn.commit()
        return dependency

    def dependencies(self) -> list[Dependency]:
        rows = self._conn.execute(
            "SELECT * FROM dependencies ORDER BY rowid"
        ).fetchall()
        return [
            Dependency(
                row["dependency_id"],
                row["claim_id"],
                row["depends_on_kind"],
                row["depends_on_id"],
            )
            for row in rows
        ]

    def derive_present_use_authorization(self, record_id: str) -> None:
        raise FieldDerivationRefused(
            "ULC-00-05: whether a record may be used now is not inferred from its origin "
            "or from transformation history"
        )

    def infer_role(self, record_id: str, role: str) -> None:
        raise RoleInferenceRefused(
            "ULC-18-02: provenance roles are distinct; "
            f"{role} is not inferred from another role"
        )

    def inherit_historical_authority(self, lineage_id: str) -> None:
        raise HistoricalAuthorityNotInherited(
            "ULC-00-10: present wording may not inherit historical authority it does not carry"
        )

    def create_summary(self, *, summary: str, constituent_ids: list[str]) -> Aggregation:
        if not constituent_ids:
            raise TraceLinksRequired(
                "ULC-00-06: a summary without resolvable trace links is rejected"
            )
        records = []
        for record_id in constituent_ids:
            record = self.get_record(record_id)
            if record is None:
                raise TraceLinksRequired(
                    "ULC-00-06: a trace link does not resolve to a stored record"
                )
            records.append(record)
        texts = {record.assertion_text for record in records}
        differences: list[dict] = []
        if len(texts) > 1:
            differences = [
                {"record_id": record.record_id, "assertion_text": record.assertion_text}
                for record in records
            ]
        aggregation = Aggregation(
            aggregation_id=_new_id(),
            summary=summary,
            constituent_ids=tuple(constituent_ids),
            differences=tuple(differences),
        )
        self._insert(
            "aggregations",
            {
                "aggregation_id": aggregation.aggregation_id,
                "summary": aggregation.summary,
                "constituent_ids": json.dumps(list(aggregation.constituent_ids)),
                "differences": json.dumps(list(aggregation.differences)),
            },
        )
        self._conn.commit()
        return aggregation

    def aggregate(
        self, record_ids: list[str], *, summary: str, discard_contradictory: bool = False
    ) -> Aggregation:
        if discard_contradictory:
            raise ConstituentDiscarded(
                "ULC-00-01: no aggregation output may be produced by discarding "
                "a contradictory constituent"
            )
        return self.create_summary(summary=summary, constituent_ids=list(record_ids))

    def resolve_summary(self, aggregation_id: str) -> list[Record]:
        row = self._conn.execute(
            "SELECT * FROM aggregations WHERE aggregation_id = ?",
            (aggregation_id,),
        ).fetchone()
        if row is None:
            raise KeyError(aggregation_id)
        ids = json.loads(row["constituent_ids"])
        return [self.get_record(record_id) for record_id in ids]  # type: ignore[misc]

    def get_aggregation(self, aggregation_id: str) -> Aggregation:
        row = self._conn.execute(
            "SELECT * FROM aggregations WHERE aggregation_id = ?",
            (aggregation_id,),
        ).fetchone()
        if row is None:
            raise KeyError(aggregation_id)
        return Aggregation(
            aggregation_id=row["aggregation_id"],
            summary=row["summary"],
            constituent_ids=tuple(json.loads(row["constituent_ids"])),
            differences=tuple(json.loads(row["differences"])),
        )

    def note_contradiction(
        self,
        *,
        subject_id: str,
        scope: str,
        witnesses: list[dict],
        created_at: str,
    ) -> Contradiction:
        if len(witnesses) < 2:
            raise ValueError("a contradiction needs two witnesses")
        accounts = {witness["account"] for witness in witnesses}
        if len(accounts) < 2:
            raise ValueError("witnesses that agree are not a contradiction")
        if not scope:
            raise ValueError("a contradiction needs a scope")
        contradiction_id = _new_id()
        created = require_timestamp_or_unknown(created_at)
        self._insert(
            "contradictions",
            {
                "contradiction_id": contradiction_id,
                "subject_id": subject_id,
                "scope": scope,
                "created_at": created,
            },
        )
        for index, witness in enumerate(witnesses, start=1):
            witnessed_at = require_timestamp_or_unknown(witness["witnessed_at"])
            self._insert(
                "contradiction_witnesses",
                {
                    "witness_row_id": _new_id(),
                    "contradiction_id": contradiction_id,
                    "witness_id": witness["witness_id"],
                    "account": witness["account"],
                    "witnessed_at": witnessed_at,
                    "seq": index,
                },
            )
        self._conn.commit()
        return self.get_contradiction(contradiction_id)

    def add_witness(
        self,
        contradiction_id: str,
        *,
        witness_id: str,
        account: str,
        witnessed_at: str,
        resolve_by_recency: bool = False,
    ) -> Contradiction:
        if resolve_by_recency:
            raise RecencyDoesNotResolve(
                "ULC-18-08: recency alone resolves nothing"
            )
        current = self.get_contradiction(contradiction_id)
        if current.resolution_decision is not None:
            raise ResolutionRequiresGrounds(
                "ULC-18-08: a recorded resolution already exists; recency is not a new one"
            )
        next_seq = len(current.witnesses) + 1
        self._insert(
            "contradiction_witnesses",
            {
                "witness_row_id": _new_id(),
                "contradiction_id": contradiction_id,
                "witness_id": witness_id,
                "account": account,
                "witnessed_at": require_timestamp_or_unknown(witnessed_at),
                "seq": next_seq,
            },
        )
        self._conn.commit()
        updated = self.get_contradiction(contradiction_id)
        if updated.evidence_state != "disputed" or updated.winning_account is not None:
            raise RecencyResolutionBroken()
        return updated

    def merge_contradiction(self, contradiction_id: str) -> None:
        raise ContradictionMergeRefused(
            "ULC-00-09: contradictions may not be silently merged"
        )

    def drop_contradiction(self, contradiction_id: str) -> None:
        raise ContradictionDropRefused(
            "ULC-00-09: contradictions may not be dropped"
        )

    def record_resolution(
        self,
        contradiction_id: str,
        *,
        decision: str,
        grounds: str,
        recorded_at: str,
    ) -> Contradiction:
        self.get_contradiction(contradiction_id)
        if not grounds or not str(grounds).strip():
            raise ResolutionRequiresGrounds(
                "ULC-18-08: a resolution decision requires recorded grounds"
            )
        if not decision:
            raise ResolutionRequiresGrounds(
                "ULC-18-08: a resolution decision requires recorded grounds"
            )
        self._insert(
            "resolutions",
            {
                "resolution_id": _new_id(),
                "contradiction_id": contradiction_id,
                "decision": decision,
                "grounds": grounds,
                "recorded_at": require_timestamp_or_unknown(recorded_at),
            },
        )
        self._conn.commit()
        return self.get_contradiction(contradiction_id)

    def get_contradiction(self, contradiction_id: str) -> Contradiction:
        row = self._conn.execute(
            "SELECT * FROM contradictions WHERE contradiction_id = ?",
            (contradiction_id,),
        ).fetchone()
        if row is None:
            raise KeyError(contradiction_id)
        witnesses = self._conn.execute(
            """
            SELECT * FROM contradiction_witnesses
            WHERE contradiction_id = ?
            ORDER BY seq
            """,
            (contradiction_id,),
        ).fetchall()
        resolution = self._conn.execute(
            """
            SELECT * FROM resolutions
            WHERE contradiction_id = ?
            ORDER BY rowid DESC
            """,
            (contradiction_id,),
        ).fetchone()
        witness_rows = tuple(
            {
                "witness_id": witness["witness_id"],
                "account": witness["account"],
                "witnessed_at": witness["witnessed_at"],
            }
            for witness in witnesses
        )
        if resolution is None:
            evidence_state = "disputed"
            decision = None
            grounds = None
        else:
            decision = resolution["decision"]
            grounds = resolution["grounds"]
            try:
                evidence_state = require_evidence_state(decision)
            except VocabularyBoundaryError:
                evidence_state = "disputed"
        return Contradiction(
            contradiction_id=row["contradiction_id"],
            subject_id=row["subject_id"],
            scope=row["scope"],
            created_at=row["created_at"],
            witnesses=witness_rows,
            resolution_decision=decision,
            resolution_grounds=grounds,
            evidence_state=evidence_state,
            winning_account=None,
        )

    def note_retention(self, record_id: str, duration: str) -> str:
        record = self.get_record(record_id)
        if record is None:
            raise KeyError(record_id)
        note_id = _new_id()
        self._insert(
            "retention_notes",
            {
                "note_id": note_id,
                "record_id": record_id,
                "duration": duration,
                "evidence_state_at_note": record.evidence_state,
            },
        )
        self._conn.commit()
        return note_id

    def promote_for_retention(self, record_id: str) -> None:
        raise RetentionDoesNotPromote(
            "ULC-18-01: retention duration must not promote an assertion to supported"
        )

    def fill_unknown(self, record_id: str, role: str, plausible_value: str) -> None:
        raise PlausibleSubstituteRejected(
            "ULC-18-07: where provenance is missing the field stays unknown; "
            f"no plausible value may be substituted for {role}"
        )

    def collapse_evidence_states(self, record_ids: list[str], into: str = "supported") -> None:
        raise StateCollapseRefused(
            "ULC-21-08: collapsing canonical evidence states into the record is refused"
        )

    def record_route(
        self,
        *,
        corpus_id: str,
        outcome: object,
        detail: str,
        recorded_at: str,
        member_id: str | None = None,
        source_id: str | None = None,
        transport: object | None = None,
    ) -> RouteLog:
        parsed_outcome = require_route_outcome(outcome)
        parsed_transport = None
        if transport is not None:
            parsed_transport = require_transport_outcome(transport)
        if parsed_outcome != "empty" and parsed_transport == "empty":
            from universalis.errors import FailedRouteIsNotEmpty

            raise FailedRouteIsNotEmpty(
                "ULC-21-06: a non-empty route outcome cannot be stored as transport empty"
            )
        route = RouteLog(
            route_id=_new_id(),
            corpus_id=corpus_id,
            member_id=member_id,
            source_id=source_id,
            outcome=parsed_outcome,
            transport=parsed_transport,
            detail=detail,
            recorded_at=require_timestamp_or_unknown(recorded_at),
        )
        self._insert(
            "route_log",
            {
                "route_id": route.route_id,
                "corpus_id": route.corpus_id,
                "member_id": route.member_id,
                "source_id": route.source_id,
                "outcome": route.outcome,
                "transport": route.transport,
                "detail": route.detail,
                "recorded_at": route.recorded_at,
            },
        )
        self._conn.commit()
        return route

    def latest_route(self, corpus_id: str, member_id: str) -> RouteLog | None:
        row = self._conn.execute(
            """
            SELECT * FROM route_log
            WHERE corpus_id = ? AND member_id = ?
            ORDER BY rowid DESC
            """,
            (corpus_id, member_id),
        ).fetchone()
        if row is None:
            return None
        return RouteLog(
            route_id=row["route_id"],
            corpus_id=row["corpus_id"],
            member_id=row["member_id"],
            source_id=row["source_id"],
            outcome=row["outcome"],
            transport=row["transport"],
            detail=row["detail"],
            recorded_at=row["recorded_at"],
        )

    def append_audit(
        self,
        *,
        subject_kind: str,
        subject_id: str,
        event_type: str,
        prior_decision: str,
        new_review_state: str,
        reason: str,
        recorded_at: str,
    ) -> AuditEvent:
        event = AuditEvent(
            audit_id=_new_id(),
            subject_kind=subject_kind,
            subject_id=subject_id,
            event_type=event_type,
            prior_decision=prior_decision,
            new_review_state=new_review_state,
            reason=reason,
            recorded_at=require_timestamp_or_unknown(recorded_at),
        )
        self._insert(
            "audit_events",
            {
                "audit_id": event.audit_id,
                "subject_kind": event.subject_kind,
                "subject_id": event.subject_id,
                "event_type": event.event_type,
                "prior_decision": event.prior_decision,
                "new_review_state": event.new_review_state,
                "reason": event.reason,
                "recorded_at": event.recorded_at,
            },
        )
        self._conn.commit()
        return event

    def audits_for(self, subject_id: str) -> list[AuditEvent]:
        rows = self._conn.execute(
            "SELECT * FROM audit_events WHERE subject_id = ? ORDER BY rowid",
            (subject_id,),
        ).fetchall()
        return [
            AuditEvent(
                audit_id=row["audit_id"],
                subject_kind=row["subject_kind"],
                subject_id=row["subject_id"],
                event_type=row["event_type"],
                prior_decision=row["prior_decision"],
                new_review_state=row["new_review_state"],
                reason=row["reason"],
                recorded_at=row["recorded_at"],
            )
            for row in rows
        ]

    def insert_view_row(self, row: dict) -> None:
        self._insert("views", row)
        self._conn.commit()

    def view_rows(self) -> list[sqlite3.Row]:
        return list(self._conn.execute("SELECT * FROM views ORDER BY rowid").fetchall())

    def view_row(self, view_id: str) -> sqlite3.Row | None:
        return self._conn.execute(
            "SELECT * FROM views WHERE view_id = ?", (view_id,)
        ).fetchone()


class RecencyResolutionBroken(RuntimeError):
    """A witness write left a contradiction looking resolved. That is a defect."""
