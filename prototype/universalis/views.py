"""Filtered views that declare their scope and keep their snapshot.

A view records the evidence generation it was computed from. When the corpus
generation later changes, the stored snapshot is left as it was and a read
marks it stale, with both a machine value and a text label.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from universalis.errors import CompleteLabelRefused, ViewScopeRequired
from universalis.states import require_timestamp_or_unknown
from universalis.store import Store


@dataclass(frozen=True)
class ViewSpec:
    corpus_id: str
    version: str
    inclusion_rules: tuple
    scope_boundary: str

    def __post_init__(self) -> None:
        if not self.corpus_id or not str(self.corpus_id).strip():
            raise ViewScopeRequired(
                "ULC-21-02: a view declares its corpus identifier before reporting a total"
            )
        if not self.version or not str(self.version).strip():
            raise ViewScopeRequired(
                "ULC-21-02: a view declares its corpus version before reporting a total"
            )
        if self.inclusion_rules is None:
            raise ViewScopeRequired(
                "ULC-21-02: a view declares its inclusion rules before reporting a total"
            )
        if not self.scope_boundary or not str(self.scope_boundary).strip():
            raise ViewScopeRequired(
                "ULC-21-02: a view declares its scope boundary before reporting a total"
            )


@dataclass(frozen=True)
class View:
    view_id: str
    corpus_id: str
    version: str
    inclusion_rules: tuple
    scope_boundary: str
    filters: tuple
    partial: bool
    complete: bool
    omitted_count: int
    omitted_ids: tuple
    shown_ids: tuple
    evidence_generation: int
    stale: bool
    staleness_value: str
    staleness_text: str


def _is_resolved_only(filters: list[dict]) -> bool:
    for item in filters:
        field = item.get("field")
        equals = item.get("equals")
        if field in {"evidence_state", "disposition"} and equals in {
            "supported",
            "resolved",
        }:
            return True
    return False


def _member_state(store: Store, corpus_id: str, member_id: str) -> str:
    record = store.current_record_for_member(corpus_id, member_id)
    if record is None:
        return "missing"
    return record.evidence_state


def _apply_filters(evidence_state: str, filters: list[dict]) -> bool:
    for item in filters:
        field = item.get("field")
        if field != "evidence_state":
            raise ViewScopeRequired(
                "a view filter must name the evidence_state field it narrows"
            )
        if "equals" not in item:
            raise ViewScopeRequired("a view filter must declare what it keeps")
        if evidence_state != item["equals"]:
            return False
    return True


def create_view(
    store: Store,
    *,
    corpus_id: str,
    version: str,
    inclusion_rules: list | None,
    scope_boundary: str,
    filters: list | None = None,
    label_complete: bool = False,
    created_at: str,
) -> View:
    rules = None if inclusion_rules is None else tuple(inclusion_rules)
    spec = ViewSpec(
        corpus_id=corpus_id,
        version=version,
        inclusion_rules=rules if rules is not None else None,  # type: ignore[arg-type]
        scope_boundary=scope_boundary,
    )
    corpus = store.corpus(spec.corpus_id)
    if spec.version != corpus.version:
        raise ViewScopeRequired(
            "ULC-21-02: the view version must be the declared corpus version"
        )
    active_filters = list(filters or [])
    partial = bool(active_filters)
    resolved_only = _is_resolved_only(active_filters)
    if label_complete and (partial or resolved_only):
        raise CompleteLabelRefused(
            "ULC-21-05: a filtered or resolved-only projection cannot be labelled complete"
        )
    excluded = set(store.exclusions(spec.corpus_id))
    in_scope = [
        member_id
        for member_id in store.population_ids(spec.corpus_id)
        if member_id not in excluded
    ]
    shown: list[str] = []
    omitted: list[str] = []
    for member_id in in_scope:
        state = _member_state(store, spec.corpus_id, member_id)
        if _apply_filters(state, active_filters):
            shown.append(member_id)
        else:
            omitted.append(member_id)
    complete = not partial
    view_id = uuid.uuid4().hex
    store.insert_view_row(
        {
            "view_id": view_id,
            "corpus_id": spec.corpus_id,
            "version": spec.version,
            "inclusion_rules": json.dumps(list(spec.inclusion_rules)),
            "scope_boundary": spec.scope_boundary,
            "filters": json.dumps(active_filters),
            "partial": 1 if partial else 0,
            "complete": 1 if complete else 0,
            "omitted_count": len(omitted),
            "omitted_ids": json.dumps(omitted),
            "shown_ids": json.dumps(shown),
            "evidence_generation": corpus.evidence_generation,
            "created_at": require_timestamp_or_unknown(created_at),
        }
    )
    return read_view(store, view_id)


def read_view(store: Store, view_id: str) -> View:
    row = store.view_row(view_id)
    if row is None:
        raise KeyError(view_id)
    corpus = store.corpus(row["corpus_id"])
    stale = corpus.evidence_generation != row["evidence_generation"]
    if stale:
        staleness_value = "stale"
        staleness_text = (
            "Stale: the evidence generation changed after this snapshot; "
            "the snapshot is retained until recomputed"
        )
    else:
        staleness_value = "current"
        staleness_text = "Current for the evidence generation recorded on this snapshot"
    return View(
        view_id=row["view_id"],
        corpus_id=row["corpus_id"],
        version=row["version"],
        inclusion_rules=tuple(json.loads(row["inclusion_rules"])),
        scope_boundary=row["scope_boundary"],
        filters=tuple(json.loads(row["filters"])),
        partial=bool(row["partial"]),
        complete=bool(row["complete"]),
        omitted_count=row["omitted_count"],
        omitted_ids=tuple(json.loads(row["omitted_ids"])),
        shown_ids=tuple(json.loads(row["shown_ids"])),
        evidence_generation=row["evidence_generation"],
        stale=stale,
        staleness_value=staleness_value,
        staleness_text=staleness_text,
    )
