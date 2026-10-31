"""Two vocabularies, referent types, and readiness.

Evidence states and transport outcomes are different types. A value that
belongs to one is rejected by the parser for the other. Route outcomes are a
third type: they are how a query is reported, and they are not evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from universalis.errors import (
    ReadinessRefused,
    TimestampOffsetRequired,
    ToolingStatusForbidden,
    VocabularyBoundaryError,
)

EXPLICIT_UNKNOWN = "unknown"

_TOOLING_FORBIDDEN = frozenset({"reviewed", "accepted", "authorized"})
_TOOLING_ALLOWED = frozenset(
    {"planned", "executed", "failed", "incomplete", "reproduced"}
)


class EvidenceState(Enum):
    SUPPORTED = "supported"
    DISPUTED = "disputed"
    MISSING = "missing"
    STALE = "stale"
    CORRUPTED = "corrupted"
    PENDING_REVIEW = "pending_review"
    UNKNOWN = "unknown"


class TransportOutcome(Enum):
    OK = "ok"
    EMPTY = "empty"
    FAILED_REQUEST = "failed_request"
    TRUNCATED = "truncated"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"


class RouteOutcome(Enum):
    """Data-layer outcomes for a route.

    ``missing`` here is an absent record. It is not ``EvidenceState.MISSING``
    and it is not ``TransportOutcome.EMPTY``. The string overlaps the evidence
    vocabulary on purpose so the type check, not the spelling, is what keeps
    them apart. ``ok`` is a successful retrieval with records; the other six
    are the distinguishable results required for a route.
    """

    OK = "ok"
    EMPTY = "empty"
    MISSING = "missing"
    FAILED_REQUEST = "failed_request"
    TRUNCATED = "truncated"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"


class ReferentType(Enum):
    ARTIFACT = "artifact"
    MODEL = "model"
    OBSERVATION = "observation"
    ROLE = "role"
    AUTHORITY = "authority"


class Readiness(Enum):
    EVALUATED_PASSING = "evaluated_passing"
    ABSENT = "absent"
    FAILED = "failed"
    UNEXECUTED = "unexecuted"


class OffsetTimestamp:
    """An instant that carries an explicit UTC offset."""

    def __init__(self, text: str):
        if not isinstance(text, str):
            raise TimestampOffsetRequired(
                "ULC-18-05: a timestamp must be text that includes an offset"
            )
        raw = text.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise TimestampOffsetRequired(
                "ULC-18-05: a timestamp without an offset is rejected for ordering"
            ) from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise TimestampOffsetRequired(
                "ULC-18-05: a wall-clock label without an offset is rejected for ordering"
            )
        self.instant = parsed.astimezone(timezone.utc)
        self.text = parsed.isoformat()

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"OffsetTimestamp({self.text!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OffsetTimestamp):
            return self.instant == other.instant and self.text == other.text
        return NotImplemented


def parse_offset_timestamp(value: str) -> OffsetTimestamp:
    return OffsetTimestamp(value)


def order_timestamps(values: list[str]) -> list[OffsetTimestamp]:
    """Order timestamps. A single missing offset refuses the whole ordering."""

    parsed = [parse_offset_timestamp(value) for value in values]
    return sorted(parsed, key=lambda item: item.instant)


def require_timestamp_or_unknown(value: str | None) -> str:
    """Store an offset timestamp, or the explicit unknown sentinel. Never a guess."""

    if value is None or value == EXPLICIT_UNKNOWN:
        return EXPLICIT_UNKNOWN
    return str(parse_offset_timestamp(value))


def require_evidence_state(value: object) -> str:
    if isinstance(value, (TransportOutcome, RouteOutcome)):
        raise VocabularyBoundaryError(
            f"{value!r} is not an evidence state and cannot be stored in an evidence-state field"
        )
    if isinstance(value, EvidenceState):
        return value.value
    if isinstance(value, str):
        transport_values = {item.value for item in TransportOutcome}
        if value in transport_values:
            raise VocabularyBoundaryError(
                f"{value} is a transport outcome and cannot be written as an evidence state"
            )
        try:
            return EvidenceState(value).value
        except ValueError as exc:
            raise VocabularyBoundaryError(
                f"{value!r} is not a canonical evidence state"
            ) from exc
    raise VocabularyBoundaryError(
        f"{type(value).__name__} cannot be stored as an evidence state"
    )


def require_transport_outcome(value: object) -> str:
    if isinstance(value, (EvidenceState, RouteOutcome)):
        raise VocabularyBoundaryError(
            f"{value!r} cannot be stored in a transport-outcome field"
        )
    if isinstance(value, TransportOutcome):
        return value.value
    if isinstance(value, str):
        evidence_values = {item.value for item in EvidenceState}
        if value in evidence_values:
            raise VocabularyBoundaryError(
                f"{value} is an evidence state and cannot be stored as a transport outcome"
            )
        try:
            return TransportOutcome(value).value
        except ValueError as exc:
            raise VocabularyBoundaryError(
                f"{value!r} is not a transport outcome"
            ) from exc
    raise VocabularyBoundaryError(
        f"{type(value).__name__} cannot be stored as a transport outcome"
    )


def require_route_outcome(value: object) -> str:
    if isinstance(value, (EvidenceState, TransportOutcome)):
        raise VocabularyBoundaryError(
            f"{value!r} cannot be stored as a route outcome"
        )
    if isinstance(value, RouteOutcome):
        return value.value
    if isinstance(value, str):
        try:
            return RouteOutcome(value).value
        except ValueError as exc:
            raise VocabularyBoundaryError(
                f"{value!r} is not a route outcome"
            ) from exc
    raise VocabularyBoundaryError(
        f"{type(value).__name__} cannot be stored as a route outcome"
    )


def require_referent_type(value: object) -> str:
    from universalis.errors import UntypedReferenceRejected

    if value is None or value == "":
        raise UntypedReferenceRejected(
            "ULC-00-02: an untyped reference is rejected"
        )
    if isinstance(value, ReferentType):
        return value.value
    if isinstance(value, str):
        try:
            return ReferentType(value).value
        except ValueError as exc:
            raise UntypedReferenceRejected(
                "ULC-00-02: referent type must be one of artifact, model, "
                "observation, role, authority"
            ) from exc
    raise UntypedReferenceRejected(
        "ULC-00-02: an untyped reference is rejected"
    )


def assert_readiness(state: Readiness, *, evaluated: bool, passing: bool) -> None:
    """Readiness is a specific state. The other three states stay distinct."""

    if not isinstance(state, Readiness):
        raise ReadinessRefused(
            "ULC-00-12: readiness must be one of the four distinct states"
        )
    if state is not Readiness.EVALUATED_PASSING:
        raise ReadinessRefused(
            "ULC-00-12: "
            f"{state.value} is not readiness; absent, failed, and unexecuted stay distinct"
        )
    if not evaluated or not passing:
        raise ReadinessRefused(
            "ULC-00-12: readiness may be asserted only for evaluated, passing evidence"
        )


def tooling_set_evidence_status(status: str) -> str:
    """Record a tooling status. Reviewer statuses are refused."""

    if status in _TOOLING_FORBIDDEN or status not in _TOOLING_ALLOWED:
        raise ToolingStatusForbidden(
            "tooling may record planned, executed, failed, incomplete, or "
            f"reproduced; it may not set {status!r}"
        )
    return status
