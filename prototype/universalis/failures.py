"""Six distinguishable route results.

Genuine emptiness is the only result whose outcome is ``empty``. A failed
request, an absent record, a truncated response, a denial, and an unavailable
source each keep their own outcome. None of those five may be written down as
though no material existed.
"""

from __future__ import annotations

from dataclasses import dataclass

from universalis.errors import (
    DegradedPresentedAsComplete,
    FabricationRefused,
    FailedRouteIsNotEmpty,
    OmissionNotNamed,
    TruncationNotReported,
    TruncationPresentedAsComplete,
)
from universalis.states import RouteOutcome, TransportOutcome
from universalis.store import Record, Store

_DEGRADED = frozenset(
    {"missing", "failed_request", "truncated", "denied", "unavailable"}
)

_TRANSPORT_FOR_OUTCOME = {
    "ok": TransportOutcome.OK.value,
    "empty": TransportOutcome.EMPTY.value,
    "failed_request": TransportOutcome.FAILED_REQUEST.value,
    "truncated": TransportOutcome.TRUNCATED.value,
    "denied": TransportOutcome.DENIED.value,
    "unavailable": TransportOutcome.UNAVAILABLE.value,
    "missing": None,
}


@dataclass(frozen=True)
class RouteRequest:
    corpus_id: str
    source_id: str | None = None
    source_version: str | None = None
    record_id: str | None = None
    member_id: str | None = None
    query_text: str | None = None
    authorized: bool = True
    path_visible: bool = False
    budget: int | None = None
    resolve_hops: int | None = None
    timed_out: bool = False
    route_failed: bool = False
    recorded_at: str = "2026-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class RouteResult:
    outcome: str
    transport: str | None
    records: tuple
    omitted_count: int
    omitted_ids: tuple
    omission_note: str
    complete: bool
    source_id: str | None
    detail: str

    def __post_init__(self) -> None:
        if self.outcome not in {item.value for item in RouteOutcome}:
            raise FailedRouteIsNotEmpty(
                f"{self.outcome!r} is not a distinguishable route outcome"
            )
        if self.outcome != "empty" and self.transport == TransportOutcome.EMPTY.value:
            raise FailedRouteIsNotEmpty(
                "ULC-21-06: a route that failed is never reported as though it found nothing "
                f"(outcome {self.outcome})"
            )
        if self.outcome == "empty" and self.transport != TransportOutcome.EMPTY.value:
            raise FailedRouteIsNotEmpty(
                "genuine emptiness is the only route stored as transport empty"
            )
        if self.outcome == "truncated" and self.complete:
            raise TruncationPresentedAsComplete(
                "ULC-21-06: a truncated response is not presented as complete"
            )
        if self.outcome in _DEGRADED and self.complete:
            raise DegradedPresentedAsComplete(
                "ULC-16-12: a degraded result may not be presented as complete "
                f"(outcome {self.outcome})"
            )
        if self.outcome == "truncated" and (self.omitted_count < 1 or not self.omitted_ids):
            raise TruncationNotReported(
                "ULC-16-12: a truncated response must name what it omitted"
            )
        if self.outcome == "failed_request" and not str(self.omission_note).strip():
            raise OmissionNotNamed(
                "ULC-16-12: a failed request must name what was omitted"
            )
        if self.outcome == "empty" and (self.records or self.omitted_count):
            raise FailedRouteIsNotEmpty(
                "genuine emptiness does not carry records or a hidden remainder"
            )


def present_as_empty(result: RouteResult) -> RouteResult:
    if result.outcome != RouteOutcome.EMPTY.value:
        raise FailedRouteIsNotEmpty(
            "ULC-21-06: refusing to present "
            f"{result.outcome} as though nothing was there"
        )
    return result


def label_complete(result: RouteResult) -> RouteResult:
    if result.outcome in _DEGRADED or not result.complete:
        raise DegradedPresentedAsComplete(
            "ULC-16-12: a degraded result may not be presented as complete"
        )
    return result


def fabricate_result(request: RouteRequest) -> RouteResult:
    raise FabricationRefused(
        "ULC-16-07: when a source cannot be resolved, fabricating a result is a hard error"
    )


def _result(
    *,
    outcome: str,
    records: list[Record] | tuple = (),
    omitted_ids: list[str] | tuple = (),
    omission_note: str = "",
    complete: bool,
    source_id: str | None,
    detail: str,
) -> RouteResult:
    omitted = tuple(omitted_ids)
    return RouteResult(
        outcome=outcome,
        transport=_TRANSPORT_FOR_OUTCOME[outcome],
        records=tuple(records),
        omitted_count=len(omitted),
        omitted_ids=omitted,
        omission_note=omission_note,
        complete=complete,
        source_id=source_id,
        detail=detail,
    )


def _corpus_registered(store: Store, corpus_id: str) -> bool:
    if not corpus_id:
        return False
    try:
        store.corpus(corpus_id)
    except KeyError:
        return False
    return True


def _lookup(store: Store, request: RouteRequest) -> list[Record] | None:
    """Return matches, or None when a requested record id is absent."""

    if request.record_id:
        record = store.get_record(request.record_id)
        if record is None or record.corpus_id != request.corpus_id:
            return None
        return [record]
    rows = store.records_in_corpus(request.corpus_id, current_only=True)
    if request.member_id:
        rows = [row for row in rows if row.member_id == request.member_id]
    if request.query_text:
        rows = [row for row in rows if request.query_text in row.assertion_text]
    return rows


def resolve(store: Store, request: RouteRequest) -> RouteResult:
    """Resolve one local query to one distinguishable outcome.

    Authorization is applied before lookup. A visible path does not change
    a denial into success or into emptiness. Corpus resolution is next: a
    corpus that was never registered is ``unavailable`` and incomplete, never
    ``empty``, because no scope was declared that could be empty. Source
    resolution follows: if
    the named source cannot be resolved within its limit, the result is
    unavailable and no assertion is synthesised.
    """

    if not request.authorized:
        result = _result(
            outcome=RouteOutcome.DENIED.value,
            complete=False,
            source_id=request.source_id,
            detail=(
                "denied; path visibility is not permission"
                if request.path_visible
                else "denied"
            ),
            omission_note="access denied; no records are returned",
        )
        _log(store, request, result)
        return result

    if not _corpus_registered(store, request.corpus_id):
        # Audit finding N03: an undeclared scope cannot be "complete and empty".
        result = _result(
            outcome=RouteOutcome.UNAVAILABLE.value,
            complete=False,
            source_id=request.source_id,
            detail="corpus is not registered; no scope was declared to search",
            omission_note=(
                f"corpus {request.corpus_id!r} is not registered; absence of results "
                "is unknown, not empty"
            ),
        )
        _log(store, request, result)
        return result

    if request.source_id:
        source = store.get_source(request.source_id, request.source_version)
        hops = request.resolve_hops
        unresolved = source is None or (
            hops is not None and hops > source.resolve_limit
        )
        if unresolved:
            result = _result(
                outcome=RouteOutcome.UNAVAILABLE.value,
                complete=False,
                source_id=request.source_id,
                detail="source could not be resolved within its declared limit",
                omission_note=(
                    f"source {request.source_id} unresolved; no answer was synthesised"
                ),
            )
            _log(store, request, result)
            return result

    if request.route_failed:
        result = _result(
            outcome=RouteOutcome.FAILED_REQUEST.value,
            complete=False,
            source_id=request.source_id,
            detail="request failed",
            omission_note="request failed before a result; this is a fault, not an absence of material",
        )
        _log(store, request, result)
        return result

    matches = _lookup(store, request)

    if request.timed_out:
        omitted = [] if matches is None else [record.record_id for record in matches]
        note = "results not retrieved before deadline"
        if omitted:
            result = _result(
                outcome=RouteOutcome.TRUNCATED.value,
                records=[],
                omitted_ids=omitted,
                omission_note=note,
                complete=False,
                source_id=request.source_id,
                detail="timed out after identifying matches that were not returned",
            )
        else:
            result = _result(
                outcome=RouteOutcome.FAILED_REQUEST.value,
                omission_note=note,
                complete=False,
                source_id=request.source_id,
                detail="timed out before any result",
            )
        _log(store, request, result)
        return result

    if matches is None:
        result = _result(
            outcome=RouteOutcome.MISSING.value,
            complete=False,
            source_id=request.source_id,
            detail=f"record {request.record_id} is absent",
            omission_note=f"record {request.record_id} is not in the corpus",
        )
        _log(store, request, result)
        return result

    if request.budget is not None and len(matches) > request.budget:
        shown = list(matches[: request.budget])
        omitted = [record.record_id for record in matches[request.budget :]]
        result = _result(
            outcome=RouteOutcome.TRUNCATED.value,
            records=shown,
            omitted_ids=omitted,
            omission_note="budget exhausted; omitted record ids are listed",
            complete=False,
            source_id=request.source_id,
            detail="truncated at the declared budget",
        )
        _log(store, request, result)
        return result

    if len(matches) == 0:
        result = _result(
            outcome=RouteOutcome.EMPTY.value,
            complete=True,
            source_id=request.source_id,
            detail="query completed and matched nothing",
        )
        _log(store, request, result)
        return result

    result = _result(
        outcome=RouteOutcome.OK.value,
        records=matches,
        complete=True,
        source_id=request.source_id,
        detail="query completed",
    )
    _log(store, request, result)
    return result


def _log(store: Store, request: RouteRequest, result: RouteResult) -> None:
    if not request.corpus_id or not request.member_id:
        return
    transport = result.transport if result.transport is not None else None
    store.record_route(
        corpus_id=request.corpus_id,
        member_id=request.member_id,
        source_id=request.source_id,
        outcome=result.outcome,
        transport=transport,
        detail=result.detail,
        recorded_at=request.recorded_at,
    )
